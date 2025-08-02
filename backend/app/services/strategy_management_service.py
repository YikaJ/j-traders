"""
策略管理服务
处理策略的创建、更新、执行等核心功能
"""

from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.db.models.strategy import Strategy, StrategyExecution, StrategyTemplate
from app.db.models.factor import Factor
from app.schemas.strategy import (
    StrategyCreate, StrategyUpdate, StrategyResponse,
    StrategyListRequest, StrategyListResponse,
    StrategyExecutionRequest, StrategyExecutionResult,
    SelectedStock, StrategyExecutionDetail
)
from app.services.factor_service import factor_service
from app.services.tushare_service import tushare_service

logger = logging.getLogger(__name__)


class StrategyManagementService:
    """策略管理服务"""
    
    def __init__(self):
        self.factor_service = factor_service
        self.tushare_service = tushare_service
    
    async def create_strategy(self, db: Session, strategy_data: StrategyCreate, created_by: str = None) -> StrategyResponse:
        """创建新策略"""
        try:
            # 验证因子存在性
            await self._validate_factors(db, strategy_data.factors)
            
            # 创建策略记录
            db_strategy = Strategy(
                name=strategy_data.name,
                description=strategy_data.description,
                factors=[factor.dict() for factor in strategy_data.factors],
                filters=strategy_data.filters.dict() if strategy_data.filters else None,
                config=strategy_data.config.dict() if strategy_data.config else None,
                created_by=created_by
            )
            
            db.add(db_strategy)
            db.commit()
            db.refresh(db_strategy)
            
            logger.info(f"策略创建成功: {db_strategy.strategy_id}")
            return self._strategy_to_response(db_strategy)
            
        except Exception as e:
            logger.error(f"创建策略失败: {e}")
            db.rollback()
            raise
    
    async def get_strategies(self, db: Session, request: StrategyListRequest) -> StrategyListResponse:
        """获取策略列表"""
        try:
            query = db.query(Strategy)
            
            # 应用筛选条件
            if request.is_active is not None:
                query = query.filter(Strategy.is_active == request.is_active)
            
            if request.created_by:
                query = query.filter(Strategy.created_by == request.created_by)
            
            if request.keyword:
                keyword_filter = or_(
                    Strategy.name.contains(request.keyword),
                    Strategy.description.contains(request.keyword)
                )
                query = query.filter(keyword_filter)
            
            # 获取总数
            total = query.count()
            
            # 应用分页和排序
            strategies = query.order_by(desc(Strategy.created_at))\
                            .offset(request.skip)\
                            .limit(request.limit)\
                            .all()
            
            strategy_responses = [self._strategy_to_response(strategy) for strategy in strategies]
            
            return StrategyListResponse(
                strategies=strategy_responses,
                total=total,
                skip=request.skip,
                limit=request.limit
            )
            
        except Exception as e:
            logger.error(f"获取策略列表失败: {e}")
            raise
    
    async def get_strategy(self, db: Session, strategy_id: str) -> Optional[StrategyResponse]:
        """获取单个策略"""
        try:
            strategy = db.query(Strategy).filter(Strategy.strategy_id == strategy_id).first()
            if not strategy:
                return None
            
            return self._strategy_to_response(strategy)
            
        except Exception as e:
            logger.error(f"获取策略失败: {e}")
            raise
    
    async def update_strategy(self, db: Session, strategy_id: str, strategy_data: StrategyUpdate) -> Optional[StrategyResponse]:
        """更新策略"""
        try:
            strategy = db.query(Strategy).filter(Strategy.strategy_id == strategy_id).first()
            if not strategy:
                return None
            
            # 验证因子（如果有更新）
            if strategy_data.factors:
                await self._validate_factors(db, strategy_data.factors)
            
            # 更新字段
            update_data = strategy_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                if field == 'factors' and value:
                    setattr(strategy, field, [factor.dict() for factor in value])
                elif field == 'filters' and value:
                    setattr(strategy, field, value.dict())
                elif field == 'config' and value:
                    setattr(strategy, field, value.dict())
                else:
                    setattr(strategy, field, value)
            
            db.commit()
            db.refresh(strategy)
            
            logger.info(f"策略更新成功: {strategy_id}")
            return self._strategy_to_response(strategy)
            
        except Exception as e:
            logger.error(f"更新策略失败: {e}")
            db.rollback()
            raise
    
    async def delete_strategy(self, db: Session, strategy_id: str) -> bool:
        """删除策略"""
        try:
            strategy = db.query(Strategy).filter(Strategy.strategy_id == strategy_id).first()
            if not strategy:
                return False
            
            db.delete(strategy)
            db.commit()
            
            logger.info(f"策略删除成功: {strategy_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除策略失败: {e}")
            db.rollback()
            raise
    
    async def execute_strategy(self, db: Session, strategy_id: str, request: StrategyExecutionRequest) -> StrategyExecutionResult:
        """执行策略"""
        try:
            strategy = db.query(Strategy).filter(Strategy.strategy_id == strategy_id).first()
            if not strategy:
                raise ValueError(f"策略不存在: {strategy_id}")
            
            if not strategy.is_active:
                raise ValueError(f"策略已禁用: {strategy_id}")
            
            execution_date = request.execution_date or datetime.now().strftime("%Y-%m-%d")
            start_time = datetime.now()
            
            # 创建执行记录
            execution = StrategyExecution(
                strategy_id=strategy.id,
                execution_date=execution_date,
                is_dry_run=request.dry_run,
                is_saved=request.save_result,
                status="running"
            )
            
            try:
                # 执行策略选股
                selected_stocks = await self._execute_stock_selection(strategy, execution_date)
                
                # 计算执行时间
                execution_time = (datetime.now() - start_time).total_seconds()
                
                # 更新执行记录
                execution.execution_time = execution_time
                execution.stock_count = len(selected_stocks)
                execution.status = "success"
                execution.selected_stocks = [stock.dict() for stock in selected_stocks]
                
                # 保存执行记录
                if request.save_result:
                    db.add(execution)
                    
                    # 更新策略统计
                    strategy.execution_count += 1
                    strategy.last_executed_at = datetime.now()
                    strategy.last_result_count = len(selected_stocks)
                    
                    # 更新平均执行时间
                    if strategy.avg_execution_time:
                        strategy.avg_execution_time = (strategy.avg_execution_time * (strategy.execution_count - 1) + execution_time) / strategy.execution_count
                    else:
                        strategy.avg_execution_time = execution_time
                    
                    db.commit()
                    db.refresh(execution)
                
                logger.info(f"策略执行成功: {strategy_id}, 选中股票: {len(selected_stocks)}")
                
                return StrategyExecutionResult(
                    execution_id=execution.execution_id,
                    strategy_id=strategy_id,
                    execution_date=execution_date,
                    execution_time=execution_time,
                    stock_count=len(selected_stocks),
                    is_dry_run=request.dry_run,
                    status="success",
                    created_at=execution.created_at or datetime.now()
                )
                
            except Exception as e:
                # 执行失败
                execution_time = (datetime.now() - start_time).total_seconds()
                execution.execution_time = execution_time
                execution.status = "failed"
                execution.error_message = str(e)
                
                if request.save_result:
                    db.add(execution)
                    db.commit()
                
                raise
                
        except Exception as e:
            logger.error(f"执行策略失败: {e}")
            db.rollback()
            raise
    
    async def get_execution_history(self, db: Session, strategy_id: str, limit: int = 20) -> List[StrategyExecutionResult]:
        """获取策略执行历史"""
        try:
            strategy = db.query(Strategy).filter(Strategy.strategy_id == strategy_id).first()
            if not strategy:
                return []
            
            executions = db.query(StrategyExecution)\
                          .filter(StrategyExecution.strategy_id == strategy.id)\
                          .order_by(desc(StrategyExecution.created_at))\
                          .limit(limit)\
                          .all()
            
            return [self._execution_to_result(execution, strategy_id) for execution in executions]
            
        except Exception as e:
            logger.error(f"获取执行历史失败: {e}")
            raise
    
    async def get_execution_detail(self, db: Session, execution_id: str) -> Optional[StrategyExecutionDetail]:
        """获取执行详情"""
        try:
            execution = db.query(StrategyExecution).filter(StrategyExecution.execution_id == execution_id).first()
            if not execution:
                return None
            
            strategy = execution.strategy
            selected_stocks = []
            
            if execution.selected_stocks:
                selected_stocks = [SelectedStock(**stock) for stock in execution.selected_stocks]
            
            return StrategyExecutionDetail(
                execution_id=execution.execution_id,
                strategy_id=strategy.strategy_id,
                execution_date=execution.execution_date,
                execution_time=execution.execution_time or 0,
                stock_count=execution.stock_count or 0,
                is_dry_run=execution.is_dry_run,
                status=execution.status,
                error_message=execution.error_message,
                created_at=execution.created_at,
                selected_stocks=selected_stocks,
                factor_performance=execution.factor_performance or {},
                execution_log=execution.execution_log or []
            )
            
        except Exception as e:
            logger.error(f"获取执行详情失败: {e}")
            raise
    
    async def _validate_factors(self, db: Session, factors: List) -> None:
        """验证因子存在性"""
        factor_ids = [factor.factor_id for factor in factors]
        existing_factors = db.query(Factor).filter(Factor.factor_id.in_(factor_ids)).all()
        existing_ids = {factor.factor_id for factor in existing_factors}
        
        missing_ids = set(factor_ids) - existing_ids
        if missing_ids:
            raise ValueError(f"因子不存在: {', '.join(missing_ids)}")
    
    async def _execute_stock_selection(self, strategy: Strategy, execution_date: str) -> List[SelectedStock]:
        """执行股票选择算法"""
        try:
            # 获取股票池
            stock_pool = await self._get_stock_pool(strategy, execution_date)
            
            # 计算因子得分
            factor_scores = await self._calculate_factor_scores(strategy, stock_pool, execution_date)
            
            # 计算综合得分
            composite_scores = self._calculate_composite_scores(strategy, factor_scores)
            
            # 应用筛选条件
            filtered_stocks = self._apply_filters(strategy, composite_scores)
            
            # 排序并选择top股票
            max_results = strategy.config.get('max_results', 50) if strategy.config else 50
            selected_stocks = sorted(filtered_stocks, key=lambda x: x.composite_score, reverse=True)[:max_results]
            
            # 添加排名
            for i, stock in enumerate(selected_stocks):
                stock.rank = i + 1
            
            return selected_stocks
            
        except Exception as e:
            logger.error(f"股票选择执行失败: {e}")
            raise
    
    async def _get_stock_pool(self, strategy: Strategy, execution_date: str) -> List[Dict]:
        """获取股票池"""
        # 这里应该从数据库或Tushare获取股票数据
        # 现在返回模拟数据
        return [
            {"stock_code": "000001.SZ", "stock_name": "平安银行", "market_cap": 3000000, "price": 15.5, "industry": "银行"},
            {"stock_code": "000002.SZ", "stock_name": "万科A", "market_cap": 2800000, "price": 25.8, "industry": "房地产"},
            {"stock_code": "600036.SH", "stock_name": "招商银行", "market_cap": 15000000, "price": 45.2, "industry": "银行"},
            {"stock_code": "000858.SZ", "stock_name": "五粮液", "market_cap": 8500000, "price": 220.5, "industry": "食品饮料"},
        ]
    
    async def _calculate_factor_scores(self, strategy: Strategy, stock_pool: List[Dict], execution_date: str) -> Dict[str, Dict[str, float]]:
        """计算因子得分"""
        factor_scores = {}
        
        for factor_config in strategy.factors:
            factor_id = factor_config['factor_id']
            if not factor_config.get('is_enabled', True):
                continue
            
            # 这里应该调用实际的因子计算服务
            # 现在返回模拟得分
            scores = {}
            for stock in stock_pool:
                import random
                scores[stock['stock_code']] = random.uniform(-1, 1)
            
            factor_scores[factor_id] = scores
        
        return factor_scores
    
    def _calculate_composite_scores(self, strategy: Strategy, factor_scores: Dict[str, Dict[str, float]]) -> List[SelectedStock]:
        """计算综合得分"""
        composite_scores = []
        
        # 获取所有股票代码
        all_stocks = set()
        for scores in factor_scores.values():
            all_stocks.update(scores.keys())
        
        for stock_code in all_stocks:
            stock_factor_scores = {}
            composite_score = 0.0
            
            for factor_config in strategy.factors:
                factor_id = factor_config['factor_id']
                if not factor_config.get('is_enabled', True):
                    continue
                
                weight = factor_config['weight']
                score = factor_scores.get(factor_id, {}).get(stock_code, 0)
                
                stock_factor_scores[factor_id] = score
                composite_score += weight * score
            
            # 获取股票基本信息（应该从数据库获取）
            stock_name = stock_code.split('.')[0]  # 简化处理
            
            selected_stock = SelectedStock(
                stock_code=stock_code,
                stock_name=stock_name,
                composite_score=composite_score,
                factor_scores=stock_factor_scores,
                rank=0  # 稍后设置
            )
            
            composite_scores.append(selected_stock)
        
        return composite_scores
    
    def _apply_filters(self, strategy: Strategy, stocks: List[SelectedStock]) -> List[SelectedStock]:
        """应用筛选条件"""
        if not strategy.filters:
            return stocks
        
        filtered_stocks = []
        filters = strategy.filters
        
        for stock in stocks:
            # 这里应该应用实际的筛选逻辑
            # 现在简单地返回所有股票
            filtered_stocks.append(stock)
        
        return filtered_stocks
    
    def _strategy_to_response(self, strategy: Strategy) -> StrategyResponse:
        """转换策略模型为响应模型"""
        from app.schemas.strategy import StrategyFactor, StrategyFilter, StrategyConfig
        
        # 转换因子配置
        factors = []
        if strategy.factors:
            for factor_data in strategy.factors:
                factors.append(StrategyFactor(**factor_data))
        
        # 转换筛选条件
        filters = None
        if strategy.filters:
            filters = StrategyFilter(**strategy.filters)
        
        # 转换策略配置
        config = None
        if strategy.config:
            config = StrategyConfig(**strategy.config)
        
        return StrategyResponse(
            strategy_id=strategy.strategy_id,
            name=strategy.name,
            description=strategy.description,
            factors=factors,
            filters=filters,
            config=config,
            is_active=strategy.is_active,
            created_at=strategy.created_at,
            updated_at=strategy.updated_at,
            created_by=strategy.created_by,
            execution_count=strategy.execution_count,
            last_executed_at=strategy.last_executed_at,
            avg_execution_time=strategy.avg_execution_time,
            last_result_count=strategy.last_result_count
        )
    
    def _execution_to_result(self, execution: StrategyExecution, strategy_id: str) -> StrategyExecutionResult:
        """转换执行记录为结果模型"""
        return StrategyExecutionResult(
            execution_id=execution.execution_id,
            strategy_id=strategy_id,
            execution_date=execution.execution_date,
            execution_time=execution.execution_time or 0,
            stock_count=execution.stock_count or 0,
            is_dry_run=execution.is_dry_run,
            status=execution.status,
            error_message=execution.error_message,
            created_at=execution.created_at
        )


# 全局实例
strategy_management_service = StrategyManagementService()