"""
策略执行引擎
负责策略的完整执行流程：股票筛选、数据获取、因子计算、排序选股
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from sqlalchemy.orm import Session
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.schemas.strategy_execution import (
    StrategyExecutionRequest, StrategyExecutionResult, StrategyExecutionDetailResult,
    StockFilter, StockScope, ExecutionStatus, ExecutionLog, LogLevel,
    StageProgress, DataFetchSummary, FactorCalculationSummary, 
    FactorDataRequest, StockUniverse, AvailableScope
)
from app.schemas.strategy import SelectedStock, Strategy
from app.services.tushare_service import tushare_service
from app.services.factor_service import factor_service
from app.services.cache_service import cache_service
from app.db.models.strategy import Strategy as StrategyModel

logger = logging.getLogger(__name__)


class ExecutionLogger:
    """执行日志记录器"""
    
    def __init__(self, execution_id: str):
        self.execution_id = execution_id
        self.logs: List[ExecutionLog] = []
        
    def log(self, level: LogLevel, stage: str, message: str, 
            details: Optional[Dict[str, Any]] = None, progress: Optional[float] = None):
        """记录日志"""
        log_entry = ExecutionLog(
            timestamp=datetime.now(),
            level=level,
            stage=stage,
            message=message,
            details=details,
            progress=progress
        )
        self.logs.append(log_entry)
        
        # 同时输出到系统日志
        log_msg = f"[{self.execution_id}] [{stage}] {message}"
        if level == LogLevel.INFO:
            logger.info(log_msg)
        elif level == LogLevel.WARNING:
            logger.warning(log_msg)
        elif level == LogLevel.ERROR:
            logger.error(log_msg)
        elif level == LogLevel.DEBUG:
            logger.debug(log_msg)
    
    def get_logs(self) -> List[ExecutionLog]:
        """获取所有日志"""
        return self.logs.copy()


class ProgressTracker:
    """进度跟踪器"""
    
    def __init__(self, execution_id: str):
        self.execution_id = execution_id
        self.stages: Dict[str, StageProgress] = {}
        self.current_stage: Optional[str] = None
        
    def start_stage(self, stage_name: str, description: str = None):
        """开始新阶段"""
        self.current_stage = stage_name
        self.stages[stage_name] = StageProgress(
            stage_name=stage_name,
            status=ExecutionStatus.RUNNING,
            progress=0.0,
            start_time=datetime.now()
        )
    
    def update_stage_progress(self, progress: float, message: str = None):
        """更新当前阶段进度"""
        if self.current_stage and self.current_stage in self.stages:
            self.stages[self.current_stage].progress = progress
    
    def complete_stage(self, success: bool = True, error_message: str = None):
        """完成当前阶段"""
        if self.current_stage and self.current_stage in self.stages:
            stage = self.stages[self.current_stage]
            stage.end_time = datetime.now()
            stage.progress = 100.0
            stage.status = ExecutionStatus.COMPLETED if success else ExecutionStatus.FAILED
            if error_message:
                stage.error_message = error_message
    
    def get_overall_progress(self) -> float:
        """计算总体进度"""
        if not self.stages:
            return 0.0
        
        stage_weights = {
            "initialization": 5,
            "stock_filtering": 10,
            "data_fetching": 40,
            "factor_calculation": 35,
            "ranking_selection": 8,
            "finalization": 2
        }
        
        total_weight = 0
        weighted_progress = 0
        
        for stage_name, stage in self.stages.items():
            weight = stage_weights.get(stage_name, 1)
            total_weight += weight
            weighted_progress += stage.progress * weight
        
        return weighted_progress / total_weight if total_weight > 0 else 0.0


class DataFetcher:
    """数据获取器"""
    
    def __init__(self, execution_id: str, logger: ExecutionLogger, enable_cache: bool = True):
        self.execution_id = execution_id
        self.logger = logger
        self.enable_cache = enable_cache
        self.cache_hits = 0
        self.api_calls = 0
        self.total_data_size = 0
    
    async def fetch_stock_data(self, stock_codes: List[str], required_fields: List[str], 
                              trade_date: str) -> Tuple[pd.DataFrame, DataFetchSummary]:
        """获取股票数据"""
        start_time = time.time()
        total_stocks = len(stock_codes)
        fetched_data = []
        failed_stocks = []
        
        self.logger.log(LogLevel.INFO, "data_fetching", 
                       f"开始获取{total_stocks}只股票的数据，字段: {', '.join(required_fields)}")
        
        # 分批处理，避免API限制
        batch_size = 100
        batches = [stock_codes[i:i + batch_size] for i in range(0, len(stock_codes), batch_size)]
        
        for i, batch in enumerate(batches):
            try:
                self.logger.log(LogLevel.INFO, "data_fetching", 
                               f"处理第{i+1}/{len(batches)}批股票 ({len(batch)}只)")
                
                # 尝试从缓存获取
                cache_key = f"stock_data_{trade_date}_{hash(tuple(sorted(required_fields)))}"
                cached_data = None
                
                if self.enable_cache:
                    cached_data = await cache_service.get(cache_key)
                    if cached_data:
                        self.cache_hits += len(batch)
                
                if cached_data is None:
                    # 从Tushare获取数据
                    batch_data = await self._fetch_from_tushare(batch, required_fields, trade_date)
                    self.api_calls += 1
                    
                    # 缓存数据
                    if self.enable_cache and batch_data is not None:
                        await cache_service.set(cache_key, batch_data, expire=3600)  # 缓存1小时
                else:
                    batch_data = cached_data
                
                if batch_data is not None and not batch_data.empty:
                    fetched_data.append(batch_data)
                    self.total_data_size += len(batch_data) * len(batch_data.columns) * 8  # 估算大小
                else:
                    failed_stocks.extend(batch)
                
                # 更新进度
                progress = (i + 1) / len(batches) * 100
                self.logger.log(LogLevel.INFO, "data_fetching", 
                               f"数据获取进度: {progress:.1f}%", progress=progress)
                
                # 避免API限制
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.log(LogLevel.ERROR, "data_fetching", 
                               f"获取第{i+1}批数据失败: {str(e)}")
                failed_stocks.extend(batch)
        
        # 合并数据
        if fetched_data:
            combined_data = pd.concat(fetched_data, ignore_index=True)
        else:
            combined_data = pd.DataFrame()
        
        fetch_time = time.time() - start_time
        fetched_stocks = len(combined_data) if not combined_data.empty else 0
        
        summary = DataFetchSummary(
            total_stocks=total_stocks,
            fetched_stocks=fetched_stocks,
            failed_stocks=len(failed_stocks),
            cache_hits=self.cache_hits,
            api_calls=self.api_calls,
            data_size_mb=self.total_data_size / (1024 * 1024),
            fetch_time=fetch_time
        )
        
        self.logger.log(LogLevel.INFO, "data_fetching", 
                       f"数据获取完成: 成功{fetched_stocks}只，失败{len(failed_stocks)}只，耗时{fetch_time:.2f}秒")
        
        return combined_data, summary
    
    async def _fetch_from_tushare(self, stock_codes: List[str], fields: List[str], 
                                 trade_date: str) -> Optional[pd.DataFrame]:
        """从Tushare获取数据"""
        try:
            # 这里应该调用具体的Tushare API
            # 目前返回模拟数据
            data = []
            for code in stock_codes:
                row = {'ts_code': code, 'trade_date': trade_date}
                # 添加模拟的字段数据
                for field in fields:
                    if field in ['close', 'open', 'high', 'low']:
                        row[field] = np.random.uniform(10, 100)
                    elif field in ['vol', 'amount']:
                        row[field] = np.random.uniform(1000, 100000)
                    elif field in ['turnover_rate', 'pe', 'pb']:
                        row[field] = np.random.uniform(0.1, 50)
                    else:
                        row[field] = np.random.uniform(-1, 1)
                data.append(row)
            
            return pd.DataFrame(data)
            
        except Exception as e:
            self.logger.log(LogLevel.ERROR, "data_fetching", 
                           f"从Tushare获取数据失败: {str(e)}")
            return None


class FactorCalculator:
    """因子计算器"""
    
    def __init__(self, execution_id: str, logger: ExecutionLogger):
        self.execution_id = execution_id
        self.logger = logger
    
    async def calculate_factors(self, strategy: Strategy, stock_data: pd.DataFrame) -> Tuple[Dict[str, pd.Series], List[FactorCalculationSummary]]:
        """计算所有因子"""
        factor_results = {}
        summaries = []
        
        self.logger.log(LogLevel.INFO, "factor_calculation", 
                       f"开始计算{len(strategy.factors)}个因子")
        
        for i, factor_config in enumerate(strategy.factors):
            if not factor_config.is_enabled:
                continue
                
            factor_id = factor_config.factor_id
            self.logger.log(LogLevel.INFO, "factor_calculation", 
                           f"计算因子 {factor_id} ({i+1}/{len(strategy.factors)})")
            
            start_time = time.time()
            
            try:
                # 获取因子定义
                factor_def = await factor_service.get_factor_by_id(factor_id)
                if not factor_def:
                    self.logger.log(LogLevel.ERROR, "factor_calculation", 
                                   f"因子 {factor_id} 定义不存在")
                    continue
                
                # 计算因子值
                factor_values = await self._calculate_single_factor(factor_def, stock_data)
                
                if factor_values is not None and not factor_values.empty:
                    factor_results[factor_id] = factor_values
                    
                    # 统计信息
                    calculation_time = time.time() - start_time
                    valid_values = factor_values.dropna()
                    
                    summary = FactorCalculationSummary(
                        factor_id=factor_id,
                        calculated_stocks=len(valid_values),
                        failed_stocks=len(factor_values) - len(valid_values),
                        calculation_time=calculation_time,
                        min_value=float(valid_values.min()) if len(valid_values) > 0 else None,
                        max_value=float(valid_values.max()) if len(valid_values) > 0 else None,
                        mean_value=float(valid_values.mean()) if len(valid_values) > 0 else None,
                        std_value=float(valid_values.std()) if len(valid_values) > 0 else None
                    )
                    summaries.append(summary)
                    
                    self.logger.log(LogLevel.INFO, "factor_calculation", 
                                   f"因子 {factor_id} 计算完成: {len(valid_values)}只股票，耗时{calculation_time:.2f}秒")
                else:
                    self.logger.log(LogLevel.WARNING, "factor_calculation", 
                                   f"因子 {factor_id} 计算结果为空")
                
                # 更新进度
                progress = (i + 1) / len(strategy.factors) * 100
                self.logger.log(LogLevel.INFO, "factor_calculation", 
                               f"因子计算进度: {progress:.1f}%", progress=progress)
                
            except Exception as e:
                self.logger.log(LogLevel.ERROR, "factor_calculation", 
                               f"计算因子 {factor_id} 失败: {str(e)}")
        
        return factor_results, summaries
    
    async def _calculate_single_factor(self, factor_def: Any, stock_data: pd.DataFrame) -> Optional[pd.Series]:
        """计算单个因子"""
        try:
            # 这里应该执行因子的计算公式
            # 目前返回模拟数据
            stock_codes = stock_data['ts_code'].tolist()
            
            # 模拟因子计算结果
            factor_values = pd.Series(
                np.random.normal(0, 1, len(stock_codes)),
                index=stock_codes,
                name=factor_def.factor_id
            )
            
            return factor_values
            
        except Exception as e:
            self.logger.log(LogLevel.ERROR, "factor_calculation", 
                           f"因子计算执行失败: {str(e)}")
            return None


class StockSelector:
    """股票选择器"""
    
    def __init__(self, execution_id: str, logger: ExecutionLogger):
        self.execution_id = execution_id
        self.logger = logger
    
    async def select_stocks(self, strategy: Strategy, factor_results: Dict[str, pd.Series], 
                           stock_data: pd.DataFrame) -> List[SelectedStock]:
        """执行股票选择"""
        self.logger.log(LogLevel.INFO, "ranking_selection", "开始计算综合得分和选股")
        
        # 获取所有股票代码
        all_stocks = set()
        for factor_values in factor_results.values():
            all_stocks.update(factor_values.index)
        
        if not all_stocks:
            self.logger.log(LogLevel.WARNING, "ranking_selection", "没有可用的股票数据")
            return []
        
        # 计算综合得分
        composite_scores = {}
        factor_scores_dict = {}
        
        for stock_code in all_stocks:
            stock_factor_scores = {}
            composite_score = 0.0
            
            for factor_config in strategy.factors:
                if not factor_config.is_enabled:
                    continue
                    
                factor_id = factor_config.factor_id
                if factor_id in factor_results:
                    factor_value = factor_results[factor_id].get(stock_code, 0)
                    stock_factor_scores[factor_id] = float(factor_value)
                    composite_score += factor_config.weight * factor_value
            
            composite_scores[stock_code] = composite_score
            factor_scores_dict[stock_code] = stock_factor_scores
        
        # 排序
        sorted_stocks = sorted(composite_scores.items(), key=lambda x: x[1], reverse=True)
        
        # 选择top股票
        max_results = strategy.config.max_results if strategy.config else 50
        selected_count = min(len(sorted_stocks), max_results)
        
        selected_stocks = []
        for i in range(selected_count):
            stock_code, composite_score = sorted_stocks[i]
            
            # 获取股票基础信息
            stock_info = stock_data[stock_data['ts_code'] == stock_code].iloc[0] if not stock_data.empty else {}
            
            selected_stock = SelectedStock(
                stock_code=stock_code,
                stock_name=stock_info.get('name', stock_code.split('.')[0]),
                composite_score=float(composite_score),
                factor_scores=factor_scores_dict.get(stock_code, {}),
                rank=i + 1,
                market_cap=stock_info.get('total_mv'),
                price=stock_info.get('close'),
                industry=stock_info.get('industry')
            )
            selected_stocks.append(selected_stock)
        
        self.logger.log(LogLevel.INFO, "ranking_selection", 
                       f"选股完成: 从{len(all_stocks)}只股票中选出{len(selected_stocks)}只")
        
        return selected_stocks


class StrategyExecutionEngine:
    """策略执行引擎主类"""
    
    def __init__(self):
        self.running_executions: Dict[str, StrategyExecutionResult] = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def execute_strategy(self, db: Session, strategy: Strategy, 
                              request: StrategyExecutionRequest) -> StrategyExecutionResult:
        """执行策略的主要方法"""
        execution_id = str(uuid.uuid4())
        execution_date = request.execution_date or datetime.now().strftime("%Y-%m-%d")
        
        # 创建执行结果对象
        execution_result = StrategyExecutionResult(
            execution_id=execution_id,
            strategy_id=strategy.strategy_id,
            execution_date=execution_date,
            status=ExecutionStatus.PENDING,
            start_time=datetime.now(),
            stock_filter=request.stock_filter,
            is_dry_run=request.dry_run
        )
        
        # 注册正在执行的任务
        self.running_executions[execution_id] = execution_result
        
        # 创建日志记录器和进度跟踪器
        exec_logger = ExecutionLogger(execution_id)
        progress_tracker = ProgressTracker(execution_id)
        
        try:
            exec_logger.log(LogLevel.INFO, "initialization", "策略执行开始")
            
            # 阶段1: 初始化
            progress_tracker.start_stage("initialization")
            await self._stage_initialization(strategy, request, exec_logger, progress_tracker)
            progress_tracker.complete_stage()
            
            # 阶段2: 股票筛选
            progress_tracker.start_stage("stock_filtering")
            stock_universe = await self._stage_stock_filtering(request.stock_filter, execution_date, 
                                                              exec_logger, progress_tracker)
            progress_tracker.complete_stage()
            execution_result.initial_stock_count = len(stock_universe)
            
            # 阶段3: 数据获取
            progress_tracker.start_stage("data_fetching")
            required_fields = await self._get_required_fields(strategy)
            data_fetcher = DataFetcher(execution_id, exec_logger, request.enable_cache)
            stock_data, data_summary = await data_fetcher.fetch_stock_data(
                stock_universe, required_fields, execution_date
            )
            progress_tracker.complete_stage()
            execution_result.data_fetch_summary = data_summary
            
            # 阶段4: 因子计算
            progress_tracker.start_stage("factor_calculation")
            factor_calculator = FactorCalculator(execution_id, exec_logger)
            factor_results, factor_summaries = await factor_calculator.calculate_factors(strategy, stock_data)
            progress_tracker.complete_stage()
            execution_result.factor_summaries = factor_summaries
            
            # 阶段5: 排序选股
            progress_tracker.start_stage("ranking_selection")
            stock_selector = StockSelector(execution_id, exec_logger)
            selected_stocks = await stock_selector.select_stocks(strategy, factor_results, stock_data)
            progress_tracker.complete_stage()
            execution_result.final_stock_count = len(selected_stocks)
            
            # 阶段6: 完成
            progress_tracker.start_stage("finalization")
            execution_result.status = ExecutionStatus.COMPLETED
            execution_result.end_time = datetime.now()
            execution_result.total_time = (execution_result.end_time - execution_result.start_time).total_seconds()
            progress_tracker.complete_stage()
            
            exec_logger.log(LogLevel.INFO, "finalization", 
                           f"策略执行成功完成，选中{len(selected_stocks)}只股票，总耗时{execution_result.total_time:.2f}秒")
            
        except Exception as e:
            # 处理执行失败
            execution_result.status = ExecutionStatus.FAILED
            execution_result.error_message = str(e)
            execution_result.end_time = datetime.now()
            
            if progress_tracker.current_stage:
                progress_tracker.complete_stage(False, str(e))
            
            exec_logger.log(LogLevel.ERROR, "execution", f"策略执行失败: {str(e)}")
        
        finally:
            # 更新执行结果
            execution_result.logs = exec_logger.get_logs()
            execution_result.stages = list(progress_tracker.stages.values())
            execution_result.overall_progress = progress_tracker.get_overall_progress()
            
            # 从正在执行列表中移除
            if execution_id in self.running_executions:
                del self.running_executions[execution_id]
        
        return execution_result
    
    async def _stage_initialization(self, strategy: Strategy, request: StrategyExecutionRequest,
                                   logger: ExecutionLogger, tracker: ProgressTracker):
        """初始化阶段"""
        logger.log(LogLevel.INFO, "initialization", f"策略ID: {strategy.strategy_id}")
        logger.log(LogLevel.INFO, "initialization", f"策略名称: {strategy.name}")
        logger.log(LogLevel.INFO, "initialization", f"启用因子数量: {len([f for f in strategy.factors if f.is_enabled])}")
        logger.log(LogLevel.INFO, "initialization", f"执行日期: {request.execution_date}")
        logger.log(LogLevel.INFO, "initialization", f"股票范围: {request.stock_filter.scope.value}")
        tracker.update_stage_progress(100.0)
    
    async def _stage_stock_filtering(self, stock_filter: StockFilter, execution_date: str,
                                    logger: ExecutionLogger, tracker: ProgressTracker) -> List[str]:
        """股票筛选阶段"""
        logger.log(LogLevel.INFO, "stock_filtering", f"开始股票筛选，范围: {stock_filter.scope.value}")
        
        # 这里应该根据筛选条件获取股票列表
        # 目前返回模拟数据
        if stock_filter.scope == StockScope.ALL:
            # 全部股票
            stock_codes = [f"{str(i).zfill(6)}.{'SZ' if i < 500000 else 'SH'}" 
                          for i in range(1, 5000)]  # 模拟4999只股票
        elif stock_filter.scope == StockScope.INDUSTRY:
            # 按行业筛选
            stock_codes = [f"{str(i).zfill(6)}.SZ" for i in range(1, 500)]  # 模拟499只
        else:
            # 其他筛选条件
            stock_codes = [f"{str(i).zfill(6)}.SH" for i in range(600000, 600100)]  # 模拟100只
        
        # 应用基础筛选条件
        filtered_codes = await self._apply_basic_filters(stock_codes, stock_filter, logger)
        
        logger.log(LogLevel.INFO, "stock_filtering", 
                   f"股票筛选完成: 初始{len(stock_codes)}只 -> 筛选后{len(filtered_codes)}只")
        tracker.update_stage_progress(100.0)
        
        return filtered_codes
    
    async def _apply_basic_filters(self, stock_codes: List[str], stock_filter: StockFilter,
                                  logger: ExecutionLogger) -> List[str]:
        """应用基础筛选条件"""
        filtered_codes = stock_codes.copy()
        
        # 排除ST股票
        if stock_filter.exclude_st:
            # 这里应该查询ST股票列表
            st_stocks = [code for code in filtered_codes if 'ST' in code]  # 模拟
            filtered_codes = [code for code in filtered_codes if code not in st_stocks]
            logger.log(LogLevel.INFO, "stock_filtering", f"排除ST股票: {len(st_stocks)}只")
        
        # 排除新股
        if stock_filter.exclude_new_stock:
            # 这里应该查询新股列表
            new_stocks = []  # 模拟：暂无新股
            filtered_codes = [code for code in filtered_codes if code not in new_stocks]
            logger.log(LogLevel.INFO, "stock_filtering", f"排除新股: {len(new_stocks)}只")
        
        # 排除停牌股票
        if stock_filter.exclude_suspend:
            # 这里应该查询停牌股票列表
            suspend_stocks = []  # 模拟：暂无停牌
            filtered_codes = [code for code in filtered_codes if code not in suspend_stocks]
            logger.log(LogLevel.INFO, "stock_filtering", f"排除停牌股票: {len(suspend_stocks)}只")
        
        return filtered_codes
    
    async def _get_required_fields(self, strategy: Strategy) -> List[str]:
        """获取策略所需的数据字段"""
        required_fields = set(['ts_code', 'trade_date', 'close', 'open', 'high', 'low', 'vol'])
        
        # 根据因子获取所需字段
        for factor_config in strategy.factors:
            if factor_config.is_enabled:
                # 这里应该从因子定义中获取所需字段
                # 目前添加常用字段
                required_fields.update(['amount', 'turnover_rate', 'pe', 'pb', 'total_mv'])
        
        return list(required_fields)
    
    def get_execution_progress(self, execution_id: str) -> Optional[StrategyExecutionResult]:
        """获取执行进度"""
        return self.running_executions.get(execution_id)
    
    async def cancel_execution(self, execution_id: str, reason: str = None) -> bool:
        """取消执行"""
        if execution_id in self.running_executions:
            execution = self.running_executions[execution_id]
            execution.status = ExecutionStatus.CANCELLED
            execution.error_message = reason or "用户取消执行"
            execution.end_time = datetime.now()
            return True
        return False
    
    async def get_available_scopes(self) -> AvailableScope:
        """获取可用的股票范围选项"""
        # 这里应该从数据库或Tushare获取实际的选项
        return AvailableScope(
            industries=[
                {"code": "IT", "name": "信息技术"},
                {"code": "FIN", "name": "金融"},
                {"code": "HC", "name": "医疗保健"},
                {"code": "CS", "name": "消费"},
                {"code": "IND", "name": "工业"},
            ],
            concepts=[
                {"code": "AI", "name": "人工智能"},
                {"code": "5G", "name": "5G通信"},
                {"code": "NEW_ENERGY", "name": "新能源"},
                {"code": "CHIP", "name": "芯片"},
            ],
            indices=[
                {"code": "000001.SH", "name": "上证指数"},
                {"code": "399001.SZ", "name": "深证成指"},
                {"code": "399006.SZ", "name": "创业板指"},
                {"code": "000300.SH", "name": "沪深300"},
            ],
            markets=[
                {"code": "main", "name": "主板"},
                {"code": "sme", "name": "中小板"},
                {"code": "gem", "name": "创业板"},
                {"code": "star", "name": "科创板"},
            ]
        )


# 全局实例
strategy_execution_engine = StrategyExecutionEngine()