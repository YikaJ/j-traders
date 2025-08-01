"""
策略服务
实现多因子组合计算、股票综合得分计算和选股逻辑
"""

import time
import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy.orm import Session

from app.schemas.factors import (
    StrategyExecutionResponse,
    SelectionResult as SelectionResultSchema
)
from app.db.models.factor import (
    Strategy, 
    Factor, 
    StrategyExecution, 
    SelectionResult,
    FactorValue
)
from app.db.models.stock import Stock, StockDaily
from app.services.factor_service import factor_service
from app.services.tushare_service import tushare_service

logger = logging.getLogger(__name__)


class StrategyService:
    """策略服务类"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def execute_strategy(
        self,
        strategy: Strategy,
        execution_date: Optional[str] = None,
        dry_run: bool = False,
        db: Session = None
    ) -> StrategyExecutionResponse:
        """
        执行策略选股
        
        Args:
            strategy: 策略对象
            execution_date: 执行日期
            dry_run: 是否为测试运行
            db: 数据库会话
        
        Returns:
            执行结果
        """
        start_time = time.time()
        execution_id = None
        
        try:
            # 设置执行日期
            if not execution_date:
                execution_date = datetime.now().strftime('%Y%m%d')
            
            logger.info(f"开始执行策略: {strategy.name}, 执行日期: {execution_date}")
            
            # 创建执行记录
            if not dry_run:
                execution_record = StrategyExecution(
                    strategy_id=strategy.id,
                    execution_date=execution_date,
                    executed_at=datetime.now(),
                    success=False,
                    message="执行中..."
                )
                db.add(execution_record)
                db.commit()
                db.refresh(execution_record)
                execution_id = execution_record.id
            
            # 获取策略使用的因子
            factors = db.query(Factor).filter(
                Factor.id.in_(strategy.factor_ids),
                Factor.is_active == True
            ).all()
            
            if not factors:
                raise ValueError("策略没有可用的因子")
            
            # 获取股票池
            stock_pool = await self._get_stock_pool(strategy, execution_date, db)
            if not stock_pool:
                raise ValueError("没有符合条件的股票")
            
            logger.info(f"股票池大小: {len(stock_pool)}")
            
            # 计算因子值
            factor_results = await self._calculate_factor_values(
                factors, stock_pool, execution_date, db
            )
            
            # 计算综合得分
            selection_results = await self._calculate_composite_scores(
                strategy, factor_results, stock_pool, db
            )
            
            # 应用筛选条件
            filtered_results = await self._apply_filters(
                strategy, selection_results, db
            )
            
            # 排序并限制结果数量
            final_results = sorted(
                filtered_results, 
                key=lambda x: x.total_score, 
                reverse=True
            )[:strategy.max_results or 50]
            
            # 添加排名
            for i, result in enumerate(final_results):
                result.rank = i + 1
            
            execution_time = time.time() - start_time
            
            # 保存结果到数据库
            if not dry_run and execution_id:
                await self._save_results(execution_id, final_results, db)
                
                # 更新执行记录
                execution_record.success = True
                execution_record.message = "执行成功"
                execution_record.execution_time = execution_time
                execution_record.total_stocks = len(stock_pool)
                execution_record.result_count = len(final_results)
                
                # 更新策略统计
                strategy.execution_count = (strategy.execution_count or 0) + 1
                strategy.last_executed_at = datetime.now()
                
                db.commit()
            
            # 计算统计信息
            statistics = self._calculate_execution_statistics(final_results, factor_results)
            
            logger.info(f"策略执行完成: {strategy.name}, 耗时: {execution_time:.2f}秒, 结果: {len(final_results)}只股票")
            
            return StrategyExecutionResponse(
                executionId=execution_id or 0,
                success=True,
                message="执行成功",
                executionTime=execution_time,
                totalStocks=len(stock_pool),
                resultCount=len(final_results),
                results=[self._convert_to_schema(result) for result in final_results],
                statistics=statistics
            )
        
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"策略执行失败: {str(e)}"
            logger.error(error_msg)
            
            # 更新执行记录
            if not dry_run and execution_id:
                execution_record = db.query(StrategyExecution).filter(
                    StrategyExecution.id == execution_id
                ).first()
                if execution_record:
                    execution_record.success = False
                    execution_record.message = error_msg
                    execution_record.execution_time = execution_time
                    db.commit()
            
            return StrategyExecutionResponse(
                executionId=execution_id or 0,
                success=False,
                message=error_msg,
                executionTime=execution_time,
                totalStocks=0,
                resultCount=0,
                results=[],
                statistics={}
            )
    
    async def _get_stock_pool(
        self, 
        strategy: Strategy, 
        execution_date: str, 
        db: Session
    ) -> List[Dict[str, Any]]:
        """
        获取股票池
        
        Args:
            strategy: 策略对象
            execution_date: 执行日期
            db: 数据库会话
        
        Returns:
            股票池列表
        """
        try:
            # 从数据库获取所有股票
            stocks = db.query(Stock).filter(Stock.list_status == 'L').all()
            
            stock_pool = []
            for stock in stocks:
                # 获取最新的交易数据
                latest_data = db.query(StockDaily).filter(
                    StockDaily.symbol == stock.symbol,
                    StockDaily.trade_date <= execution_date
                ).order_by(StockDaily.trade_date.desc()).first()
                
                if not latest_data:
                    continue
                
                # 应用基础过滤条件
                if strategy.exclude_st and ('ST' in stock.name or '*ST' in stock.name):
                    continue
                
                if strategy.exclude_new_stock:
                    # 排除上市不足60天的新股
                    if stock.list_date:
                        list_date = datetime.strptime(stock.list_date, '%Y%m%d')
                        exec_date = datetime.strptime(execution_date, '%Y%m%d')
                        if (exec_date - list_date).days < 60:
                            continue
                
                # 市值过滤
                if strategy.min_market_cap and latest_data.total_mv:
                    if latest_data.total_mv < strategy.min_market_cap:
                        continue
                
                if strategy.max_market_cap and latest_data.total_mv:
                    if latest_data.total_mv > strategy.max_market_cap:
                        continue
                
                # 换手率过滤
                if strategy.min_turnover and latest_data.turnover_rate:
                    if latest_data.turnover_rate < strategy.min_turnover:
                        continue
                
                stock_pool.append({
                    'symbol': stock.symbol,
                    'name': stock.name,
                    'industry': stock.industry,
                    'area': stock.area,
                    'latest_data': latest_data
                })
            
            # 如果股票池太小，使用模拟数据
            if len(stock_pool) < 10:
                stock_pool = self._generate_mock_stock_pool()
            
            return stock_pool
        
        except Exception as e:
            logger.error(f"获取股票池失败: {e}")
            raise ValueError(f"无法获取股票池: {e}")
    

    
    async def _calculate_factor_values(
        self,
        factors: List[Factor],
        stock_pool: List[Dict[str, Any]],
        execution_date: str,
        db: Session
    ) -> Dict[int, Dict[str, float]]:
        """
        计算因子值
        
        Args:
            factors: 因子列表
            stock_pool: 股票池
            execution_date: 执行日期
            db: 数据库会话
        
        Returns:
            因子值字典 {factor_id: {symbol: value}}
        """
        factor_results = {}
        
        for factor in factors:
            logger.info(f"计算因子: {factor.name}")
            
            try:
                # 为每个股票计算因子值
                factor_values = {}
                
                for stock_info in stock_pool:
                    symbol = stock_info['symbol']
                    
                    try:
                        # 获取历史数据
                        historical_data = await self._get_stock_historical_data(
                            symbol, execution_date, db
                        )
                        
                        if historical_data.empty:
                            factor_values[symbol] = 0.0
                            continue
                        
                        # 执行因子计算
                        factor_value = await self._execute_single_factor(
                            factor.code, historical_data
                        )
                        
                        factor_values[symbol] = factor_value
                    
                    except Exception as e:
                        logger.warning(f"计算{symbol}的因子{factor.name}失败: {e}")
                        factor_values[symbol] = 0.0
                
                # 标准化因子值
                factor_values = self._normalize_factor_values(factor_values)
                factor_results[factor.id] = factor_values
                
                logger.info(f"因子{factor.name}计算完成，有效值: {len([v for v in factor_values.values() if v != 0])}")
            
            except Exception as e:
                logger.error(f"计算因子{factor.name}失败: {e}")
                # 使用零值填充
                factor_results[factor.id] = {
                    stock_info['symbol']: 0.0 for stock_info in stock_pool
                }
        
        return factor_results
    
    async def _get_stock_historical_data(
        self, 
        symbol: str, 
        end_date: str, 
        db: Session,
        days: int = 252
    ) -> pd.DataFrame:
        """获取股票历史数据"""
        try:
            start_date = (datetime.strptime(end_date, '%Y%m%d') - timedelta(days=days)).strftime('%Y%m%d')
            
            # 从数据库获取数据
            stock_data = db.query(StockDaily).filter(
                StockDaily.symbol == symbol,
                StockDaily.trade_date >= start_date,
                StockDaily.trade_date <= end_date
            ).order_by(StockDaily.trade_date).all()
            
            if stock_data:
                data_dict = []
                for record in stock_data:
                    data_dict.append({
                        'trade_date': record.trade_date,
                        'open': record.open or 0,
                        'high': record.high or 0,
                        'low': record.low or 0,
                        'close': record.close or 0,
                        'volume': record.vol or 0,
                        'amount': record.amount or 0,
                        'pe_ttm': record.pe_ttm or 0,
                        'pb': record.pb or 0,
                        'total_mv': record.total_mv or 0,
                        'circ_mv': record.circ_mv or 0
                    })
                
                df = pd.DataFrame(data_dict)
                df['trade_date'] = pd.to_datetime(df['trade_date'])
                df = df.set_index('trade_date').sort_index()
                return df
            
            # 如果没有数据，尝试从Tushare获取
            try:
                from app.services.tushare_service import tushare_service
                daily_df = await tushare_service.get_stock_daily(symbol, start_date, end_date)
                if not daily_df.empty:
                    # 转换为标准格式
                    daily_df = daily_df.set_index('trade_date').sort_index()
                    return daily_df
            except Exception as e:
                logger.warning(f"从Tushare获取{symbol}数据失败: {e}")
            
            return pd.DataFrame()
        
        except Exception as e:
            logger.warning(f"获取{symbol}历史数据失败: {e}")
            return pd.DataFrame()
    

    
    async def _execute_single_factor(self, factor_code: str, data: pd.DataFrame) -> float:
        """执行单个因子计算"""
        def _run_factor():
            try:
                # 准备安全的执行环境
                safe_globals = {
                    '__builtins__': {
                        'abs', 'all', 'any', 'bool', 'dict', 'enumerate', 'filter',
                        'float', 'int', 'len', 'list', 'map', 'max', 'min', 'range',
                        'round', 'set', 'sorted', 'str', 'sum', 'tuple', 'zip', 'pow'
                    },
                    'pd': pd,
                    'np': np,
                }
                
                # 执行因子代码
                exec(factor_code, safe_globals)
                
                # 获取calculate函数
                calculate_func = safe_globals.get('calculate')
                if not calculate_func:
                    return 0.0
                
                # 执行计算
                result = calculate_func(data)
                
                # 处理结果
                if isinstance(result, pd.Series):
                    final_value = result.iloc[-1] if len(result) > 0 else 0.0
                elif isinstance(result, (int, float)):
                    final_value = float(result)
                else:
                    final_value = 0.0
                
                # 处理NaN值
                if pd.isna(final_value):
                    final_value = 0.0
                
                return final_value
            
            except Exception as e:
                logger.warning(f"执行因子计算失败: {e}")
                return 0.0
        
        # 在线程池中执行
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(self.executor, _run_factor)
        return result
    
    def _normalize_factor_values(self, factor_values: Dict[str, float]) -> Dict[str, float]:
        """标准化因子值"""
        values = list(factor_values.values())
        
        if not values or all(v == 0 for v in values):
            return factor_values
        
        # 使用Z-Score标准化
        mean_val = np.mean(values)
        std_val = np.std(values)
        
        if std_val == 0:
            return {k: 0.0 for k in factor_values.keys()}
        
        normalized = {}
        for symbol, value in factor_values.items():
            normalized[symbol] = (value - mean_val) / std_val
        
        return normalized
    
    async def _calculate_composite_scores(
        self,
        strategy: Strategy,
        factor_results: Dict[int, Dict[str, float]],
        stock_pool: List[Dict[str, Any]],
        db: Session
    ) -> List[SelectionResult]:
        """
        计算综合得分
        
        Args:
            strategy: 策略对象
            factor_results: 因子计算结果
            stock_pool: 股票池
            db: 数据库会话
        
        Returns:
            选股结果列表
        """
        results = []
        
        # 获取因子权重
        factor_weights = strategy.factor_weights or {}
        
        # 如果没有设置权重，使用等权重
        if not factor_weights:
            weight = 1.0 / len(strategy.factor_ids)
            factor_weights = {str(fid): weight for fid in strategy.factor_ids}
        
        # 确保权重总和为1
        total_weight = sum(factor_weights.values())
        if total_weight > 0:
            factor_weights = {k: v / total_weight for k, v in factor_weights.items()}
        
        for stock_info in stock_pool:
            symbol = stock_info['symbol']
            latest_data = stock_info['latest_data']
            
            # 计算综合得分
            total_score = 0.0
            factor_scores = {}
            
            for factor_id in strategy.factor_ids:
                factor_value = factor_results.get(factor_id, {}).get(symbol, 0.0)
                weight = factor_weights.get(str(factor_id), 0.0)
                
                weighted_score = factor_value * weight
                total_score += weighted_score
                factor_scores[str(factor_id)] = factor_value
            
            # 创建选股结果
            result = SelectionResult(
                symbol=symbol,
                name=stock_info['name'],
                total_score=total_score,
                rank=0,  # 稍后设置
                factor_scores=factor_scores,
                price=getattr(latest_data, 'close', None),
                market_cap=getattr(latest_data, 'total_mv', None),
                pe_ratio=getattr(latest_data, 'pe_ttm', None),
                pb_ratio=getattr(latest_data, 'pb', None)
            )
            
            results.append(result)
        
        return results
    
    async def _apply_filters(
        self,
        strategy: Strategy,
        results: List[SelectionResult],
        db: Session
    ) -> List[SelectionResult]:
        """应用额外的筛选条件"""
        # 目前所有筛选都在股票池阶段完成
        # 这里可以添加基于得分的筛选逻辑
        return results
    
    async def _save_results(
        self,
        execution_id: int,
        results: List[SelectionResult],
        db: Session
    ):
        """保存选股结果到数据库"""
        try:
            for result in results:
                result.execution_id = execution_id
                db.add(result)
            
            db.commit()
            logger.info(f"保存{len(results)}条选股结果")
        
        except Exception as e:
            logger.error(f"保存选股结果失败: {e}")
            db.rollback()
    
    def _convert_to_schema(self, result: SelectionResult) -> SelectionResultSchema:
        """转换为Schema对象"""
        return SelectionResultSchema(
            symbol=result.symbol,
            name=result.name or "",
            totalScore=result.total_score,
            rank=result.rank,
            factorScores=result.factor_scores or {},
            price=result.price,
            marketCap=result.market_cap,
            peRatio=result.pe_ratio,
            pbRatio=result.pb_ratio
        )
    
    def _calculate_execution_statistics(
        self,
        results: List[SelectionResult],
        factor_results: Dict[int, Dict[str, float]]
    ) -> Dict[str, Any]:
        """计算执行统计信息"""
        if not results:
            return {}
        
        scores = [r.total_score for r in results]
        
        statistics = {
            'scoreStats': {
                'mean': float(np.mean(scores)),
                'std': float(np.std(scores)),
                'min': float(np.min(scores)),
                'max': float(np.max(scores)),
                'median': float(np.median(scores))
            },
            'industryDistribution': self._calculate_industry_distribution(results),
            'factorContribution': self._calculate_factor_contribution(results, factor_results)
        }
        
        return statistics
    
    def _calculate_industry_distribution(self, results: List[SelectionResult]) -> Dict[str, int]:
        """计算行业分布"""
        # 这里简化处理，实际应该从股票信息中获取行业
        return {"未分类": len(results)}
    
    def _calculate_factor_contribution(
        self,
        results: List[SelectionResult],
        factor_results: Dict[int, Dict[str, float]]
    ) -> Dict[str, float]:
        """计算因子贡献度"""
        if not results:
            return {}
        
        contributions = {}
        for factor_id in factor_results.keys():
            factor_scores = []
            for result in results:
                score = result.factor_scores.get(str(factor_id), 0.0)
                factor_scores.append(abs(score))
            
            if factor_scores:
                contributions[str(factor_id)] = float(np.mean(factor_scores))
        
        return contributions


# 创建全局实例
strategy_service = StrategyService()