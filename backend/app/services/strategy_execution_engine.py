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
from app.schemas.strategy import SelectedStock
from app.schemas.factors import StrategyExecutionResponse, SelectionResult as SelectionResultSchema
from app.db.models.factor import Factor, FactorValue
from app.db.models.strategy import Strategy as StrategyModel, StrategyExecution, SelectionResult
from app.db.models.stock import Stock, StockDaily
from app.services.tushare_service import tushare_service
from app.services.unified_factor_service import unified_factor_service
from app.services.cache_service import cache_service
from app.services.enhanced_data_fetcher import enhanced_data_fetcher, RateLimitConfig

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
    """数据获取器（包装增强数据获取器）"""
    
    def __init__(self, execution_id: str, logger: ExecutionLogger, enable_cache: bool = True, 
                 rate_limit_config: Optional[RateLimitConfig] = None):
        self.execution_id = execution_id
        self.logger = logger
        self.enable_cache = enable_cache
        self.enhanced_fetcher = enhanced_data_fetcher
        
        # 如果提供了频率限制配置，创建新的增强获取器实例
        if rate_limit_config:
            from app.services.enhanced_data_fetcher import EnhancedDataFetcher
            self.enhanced_fetcher = EnhancedDataFetcher(rate_limit_config)
    
    async def fetch_strategy_data(self, strategy: Any, stock_codes: List[str], 
                                 execution_date: str) -> Tuple[pd.DataFrame, DataFetchSummary]:
        """根据策略需求智能获取数据"""
        return await self.enhanced_fetcher.fetch_strategy_data(
            strategy, stock_codes, execution_date, self.logger
        )
    
    async def fetch_stock_data(self, stock_codes: List[str], required_fields: List[str], 
                              trade_date: str) -> Tuple[pd.DataFrame, DataFetchSummary]:
        """传统的股票数据获取（向后兼容）"""
        # 创建一个虚拟策略对象来包装字段需求
        class MockStrategy:
            def __init__(self, fields):
                self.factors = [MockFactor(fields)]
        
        class MockFactor:
            def __init__(self, fields):
                self.is_enabled = True
                self.factor_id = "legacy_fetch"
                # 构造简单的因子代码来表示所需字段
                self.factor_code = f"def calculate(data):\n    return data[{fields}].sum()"
        
        mock_strategy = MockStrategy(required_fields)
        return await self.fetch_strategy_data(mock_strategy, stock_codes, trade_date)
    
    async def get_stock_historical_data(self, symbol: str, end_date: str, db: Session,
                                      days: int = 252) -> pd.DataFrame:
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
                daily_df = await tushare_service.get_stock_daily(symbol, start_date, end_date)
                if not daily_df.empty:
                    # 转换为标准格式
                    daily_df = daily_df.set_index('trade_date').sort_index()
                    return daily_df
            except Exception as e:
                self.logger.log(LogLevel.WARNING, "data_fetching", 
                               f"从Tushare获取{symbol}数据失败: {e}")
            
            return pd.DataFrame()
        
        except Exception as e:
            self.logger.log(LogLevel.WARNING, "data_fetching", 
                           f"获取{symbol}历史数据失败: {e}")
            return pd.DataFrame()


class FactorCalculator:
    """因子计算器"""
    
    def __init__(self, execution_id: str, logger: ExecutionLogger):
        self.execution_id = execution_id
        self.logger = logger
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def calculate_factors(self, strategy: Any, stock_data: pd.DataFrame) -> Tuple[Dict[str, pd.Series], List[FactorCalculationSummary]]:
        """计算所有因子"""
        factor_results = {}
        summaries = []
        
        self.logger.log(LogLevel.INFO, "factor_calculation", 
                       f"开始计算{len(strategy.factors)}个因子")
        
        for i, factor_config in enumerate(strategy.factors):
            if not factor_config.is_enabled:
                continue
                
            id = factor_config.id
            self.logger.log(LogLevel.INFO, "factor_calculation", 
                           f"计算因子 {id} ({i+1}/{len(strategy.factors)})")
            
            start_time = time.time()
            
            try:
                # 获取因子定义
                factor_def = unified_factor_service.get_factor_by_id(id, db)
                if not factor_def:
                    self.logger.log(LogLevel.ERROR, "factor_calculation", 
                                   f"因子 {id} 定义不存在")
                    continue
                
                # 计算因子值
                factor_values = await self._calculate_single_factor(factor_def, stock_data)
                
                if factor_values is not None and not factor_values.empty:
                    factor_results[id] = factor_values
                    
                    # 统计信息
                    calculation_time = time.time() - start_time
                    valid_values = factor_values.dropna()
                    
                    summary = FactorCalculationSummary(
                        factor_id=id,
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
                                   f"因子 {id} 计算完成: {len(valid_values)}只股票，耗时{calculation_time:.2f}秒")
                else:
                    self.logger.log(LogLevel.WARNING, "factor_calculation", 
                                   f"因子 {id} 计算结果为空")
                
                # 更新进度
                progress = (i + 1) / len(strategy.factors) * 100
                self.logger.log(LogLevel.INFO, "factor_calculation", 
                               f"因子计算进度: {progress:.1f}%", progress=progress)
                
            except Exception as e:
                self.logger.log(LogLevel.ERROR, "factor_calculation", 
                               f"计算因子 {id} 失败: {str(e)}")
        
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
    
    async def execute_single_factor(self, factor_code: str, data: pd.DataFrame) -> float:
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
                self.logger.log(LogLevel.WARNING, "factor_calculation", 
                               f"执行因子计算失败: {e}")
                return 0.0
        
        # 在线程池中执行
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(self.executor, _run_factor)
        return result
    
    def normalize_factor_values(self, factor_values: Dict[str, float]) -> Dict[str, float]:
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


class StockSelector:
    """股票选择器"""
    
    def __init__(self, execution_id: str, logger: ExecutionLogger):
        self.execution_id = execution_id
        self.logger = logger
    
    async def select_stocks(self, strategy: Any, factor_results: Dict[str, pd.Series], 
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
                    
                id = factor_config.id
                if id in factor_results:
                    factor_value = factor_results[id].get(stock_code, 0)
                    stock_factor_scores[id] = float(factor_value)
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
    
    async def get_stock_pool(self, strategy: Any, execution_date: str, db: Session) -> List[Dict[str, Any]]:
        """获取股票池"""
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
                if hasattr(strategy, 'exclude_st') and strategy.exclude_st and ('ST' in stock.name or '*ST' in stock.name):
                    continue
                
                if hasattr(strategy, 'exclude_new_stock') and strategy.exclude_new_stock:
                    # 排除上市不足60天的新股
                    if stock.list_date:
                        list_date = datetime.strptime(stock.list_date, '%Y%m%d')
                        exec_date = datetime.strptime(execution_date, '%Y%m%d')
                        if (exec_date - list_date).days < 60:
                            continue
                
                # 市值过滤
                if hasattr(strategy, 'min_market_cap') and strategy.min_market_cap and latest_data.total_mv:
                    if latest_data.total_mv < strategy.min_market_cap:
                        continue
                
                if hasattr(strategy, 'max_market_cap') and strategy.max_market_cap and latest_data.total_mv:
                    if latest_data.total_mv > strategy.max_market_cap:
                        continue
                
                # 换手率过滤
                if hasattr(strategy, 'min_turnover') and strategy.min_turnover and latest_data.turnover_rate:
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
            self.logger.log(LogLevel.ERROR, "stock_filtering", f"获取股票池失败: {e}")
            raise ValueError(f"无法获取股票池: {e}")
    
    def _generate_mock_stock_pool(self) -> List[Dict[str, Any]]:
        """生成模拟股票池"""
        return [
            {"symbol": "000001.SZ", "name": "平安银行", "industry": "银行", "area": "深圳", "latest_data": None},
            {"symbol": "000002.SZ", "name": "万科A", "industry": "房地产", "area": "深圳", "latest_data": None},
            {"symbol": "600036.SH", "name": "招商银行", "industry": "银行", "area": "上海", "latest_data": None},
            {"symbol": "000858.SZ", "name": "五粮液", "industry": "食品饮料", "area": "深圳", "latest_data": None},
        ]


class StrategyExecutionEngine:
    """策略执行引擎主类"""
    
    def __init__(self):
        self.running_executions: Dict[str, StrategyExecutionResult] = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def execute_strategy(self, db: Session, strategy: Any, 
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
                                                              exec_logger, progress_tracker, db)
            progress_tracker.complete_stage()
            execution_result.initial_stock_count = len(stock_universe)
            
            # 阶段3: 数据获取
            progress_tracker.start_stage("data_fetching")
            
            # 配置频率限制
            rate_limit_config = None
            if request.rate_limit:
                rate_limit_config = RateLimitConfig(
                    max_calls_per_minute=request.rate_limit.max_calls_per_minute,
                    max_calls_per_hour=request.rate_limit.max_calls_per_hour,
                    max_calls_per_day=request.rate_limit.max_calls_per_day,
                    concurrent_limit=request.rate_limit.concurrent_limit
                )
            
            data_fetcher = DataFetcher(execution_id, exec_logger, request.enable_cache, rate_limit_config)
            
            # 使用新的智能数据获取
            stock_data, data_summary = await data_fetcher.fetch_strategy_data(
                strategy, stock_universe, execution_date
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
            
            # 保存执行结果到数据库
            try:
                from app.db.models.strategy import StrategyExecution as ExecutionModel
                
                # 获取策略的数据库ID
                strategy_db_id = None
                if hasattr(strategy, 'id'):
                    strategy_db_id = strategy.id
                else:
                    # 如果没有id字段，尝试从数据库查询
                    from app.db.models.strategy import Strategy as StrategyModel
                    db_strategy = db.query(StrategyModel).filter(
                        StrategyModel.strategy_id == strategy.strategy_id
                    ).first()
                    if db_strategy:
                        strategy_db_id = db_strategy.id
                
                if strategy_db_id is None:
                    logger.warning(f"无法找到策略的数据库ID: {strategy.strategy_id}")
                    strategy_db_id = 1  # 使用默认值
                
                # 创建数据库记录
                db_record = ExecutionModel(
                    execution_id=execution_id,
                    strategy_id=strategy_db_id,
                    execution_date=execution_date,
                    start_time=execution_result.start_time,
                    end_time=execution_result.end_time,
                    total_time=execution_result.total_time,
                    status=execution_result.status.value,
                    current_stage=execution_result.current_stage,
                    overall_progress=execution_result.overall_progress,
                    stock_filter=execution_result.stock_filter.dict() if execution_result.stock_filter else None,
                    is_dry_run=execution_result.is_dry_run,
                    initial_stock_count=execution_result.initial_stock_count,
                    filtered_stock_count=execution_result.filtered_stock_count,
                    final_stock_count=execution_result.final_stock_count,
                    data_fetch_summary=execution_result.data_fetch_summary.dict() if execution_result.data_fetch_summary else None,
                    factor_summaries=[summary.dict() for summary in execution_result.factor_summaries],
                    stages=[stage.dict() for stage in execution_result.stages],
                    error_message=execution_result.error_message,
                    logs=[log.dict() for log in execution_result.logs],
                    selected_stocks=[stock.dict() for stock in execution_result.selected_stocks] if hasattr(execution_result, 'selected_stocks') else None,
                    factor_performance=execution_result.factor_performance if hasattr(execution_result, 'factor_performance') else None
                )
                
                db.add(db_record)
                db.commit()
                
                logger.info(f"执行结果已保存到数据库: {execution_id}")
                
            except Exception as e:
                logger.error(f"保存执行结果到数据库失败: {e}")
                db.rollback()
            
            # 从正在执行列表中移除
            if execution_id in self.running_executions:
                del self.running_executions[execution_id]
        
        return execution_result
    
    async def _stage_initialization(self, strategy: Any, request: StrategyExecutionRequest,
                                   logger: ExecutionLogger, tracker: ProgressTracker):
        """初始化阶段"""
        logger.log(LogLevel.INFO, "initialization", f"策略ID: {strategy.strategy_id}")
        logger.log(LogLevel.INFO, "initialization", f"策略名称: {strategy.name}")
        logger.log(LogLevel.INFO, "initialization", f"启用因子数量: {len([f for f in strategy.factors if f.is_enabled])}")
        logger.log(LogLevel.INFO, "initialization", f"执行日期: {request.execution_date}")
        logger.log(LogLevel.INFO, "initialization", f"股票范围: {request.stock_filter.scope.value}")
        tracker.update_stage_progress(100.0)
    
    async def _stage_stock_filtering(self, stock_filter: StockFilter, execution_date: str,
                                    logger: ExecutionLogger, tracker: ProgressTracker, db: Session) -> List[str]:
        """股票筛选阶段"""
        logger.log(LogLevel.INFO, "stock_filtering", f"开始股票筛选，范围: {stock_filter.scope.value}")
        
        from app.db.models.stock import Stock
        
        # 根据筛选条件获取股票列表
        if stock_filter.scope == StockScope.ALL:
            # 全部股票
            stocks = db.query(Stock.symbol).filter(
                Stock.is_active == True,
                Stock.list_status == 'L'  # 只选择上市股票
            ).all()
            stock_codes = [stock.symbol for stock in stocks]
            
        elif stock_filter.scope == StockScope.INDUSTRY:
            # 按行业筛选
            if stock_filter.industries:
                stocks = db.query(Stock.symbol).filter(
                    Stock.is_active == True,
                    Stock.list_status == 'L',
                    Stock.industry.in_(stock_filter.industries)
                ).all()
                stock_codes = [stock.symbol for stock in stocks]
                logger.log(LogLevel.INFO, "stock_filtering", 
                          f"按行业筛选: {stock_filter.industries}, 找到 {len(stock_codes)} 只股票")
            else:
                stock_codes = []
                logger.log(LogLevel.WARNING, "stock_filtering", "未选择任何行业")
                
        elif stock_filter.scope == StockScope.CUSTOM:
            # 自定义股票代码
            if stock_filter.custom_stocks:
                stock_codes = stock_filter.custom_stocks
                logger.log(LogLevel.INFO, "stock_filtering", 
                          f"自定义股票代码: {len(stock_codes)} 只股票")
            else:
                stock_codes = []
                logger.log(LogLevel.WARNING, "stock_filtering", "未输入自定义股票代码")
        else:
            # 默认返回空列表
            stock_codes = []
            logger.log(LogLevel.WARNING, "stock_filtering", f"未知的筛选范围: {stock_filter.scope}")
        
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
    
    async def _get_required_fields(self, strategy: Any) -> List[str]:
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
        # 首先从正在执行的列表中查找
        if execution_id in self.running_executions:
            return self.running_executions[execution_id]
        
        # 如果不在正在执行的列表中，尝试从数据库获取
        try:
            from app.db.models.strategy import StrategyExecution as ExecutionModel
            from app.db.database import get_db
            from app.schemas.strategy_execution import ExecutionStatus, StockFilter, DataFetchSummary, FactorCalculationSummary, StageProgress, ExecutionLog
            
            # 获取数据库会话
            db = next(get_db())
            
            # 从数据库查询执行记录
            execution_record = db.query(ExecutionModel).filter(
                ExecutionModel.execution_id == execution_id
            ).first()
            
            if execution_record:
                # 反序列化JSON字段
                stock_filter = None
                if execution_record.stock_filter:
                    stock_filter = StockFilter(**execution_record.stock_filter)
                
                data_fetch_summary = None
                if execution_record.data_fetch_summary:
                    data_fetch_summary = DataFetchSummary(**execution_record.data_fetch_summary)
                
                factor_summaries = []
                if execution_record.factor_summaries:
                    factor_summaries = [FactorCalculationSummary(**summary) for summary in execution_record.factor_summaries]
                
                stages = []
                if execution_record.stages:
                    stages = [StageProgress(**stage) for stage in execution_record.stages]
                
                logs = []
                if execution_record.logs:
                    logs = [ExecutionLog(**log) for log in execution_record.logs]
                
                # 构造执行结果对象
                result = StrategyExecutionResult(
                    execution_id=execution_record.execution_id,
                    strategy_id=execution_record.strategy_id,
                    execution_date=execution_record.execution_date,
                    status=ExecutionStatus(execution_record.status),
                    start_time=execution_record.start_time,
                    end_time=execution_record.end_time,
                    total_time=execution_record.total_time,
                    stock_filter=stock_filter,
                    is_dry_run=execution_record.is_dry_run,
                    stages=stages,
                    current_stage=execution_record.current_stage,
                    overall_progress=execution_record.overall_progress,
                    initial_stock_count=execution_record.initial_stock_count,
                    filtered_stock_count=execution_record.filtered_stock_count,
                    final_stock_count=execution_record.final_stock_count,
                    data_fetch_summary=data_fetch_summary,
                    factor_summaries=factor_summaries,
                    error_message=execution_record.error_message,
                    logs=logs
                )
                
                return result
            
        except Exception as e:
            logger.error(f"从数据库获取执行进度失败: {e}")
        
        return None
    
    async def cancel_execution(self, execution_id: str, reason: str = None) -> bool:
        """取消执行"""
        if execution_id in self.running_executions:
            execution = self.running_executions[execution_id]
            execution.status = ExecutionStatus.CANCELLED
            execution.error_message = reason or "用户取消执行"
            execution.end_time = datetime.now()
            return True
        return False
    
    async def get_available_scopes(self, db: Session) -> AvailableScope:
        """获取可用的股票范围选项"""
        try:
            # 从数据库中获取所有不重复的行业
            from sqlalchemy import distinct
            from app.db.models.stock import Stock
            
            # 查询所有不重复的行业，排除空值
            industry_results = db.query(distinct(Stock.industry)).filter(
                Stock.industry.isnot(None),
                Stock.industry != '',
                Stock.is_active == True
            ).all()
            
            # 转换为前端需要的格式
            industries = []
            for result in industry_results:
                industry_name = result[0]  # distinct查询返回的是元组
                if industry_name and industry_name.strip():
                    # 使用行业名称作为code和name
                    industries.append({
                        "code": industry_name,
                        "name": industry_name
                    })
            
            # 按名称排序
            industries.sort(key=lambda x: x['name'])
            
            return AvailableScope(
                industries=industries,
                concepts=[],  # 暂时为空
                indices=[],   # 暂时为空
                markets=[]    # 暂时为空
            )
            
        except Exception as e:
            logger.error(f"获取行业数据失败: {e}")
            # 返回空列表作为fallback
            return AvailableScope(
                industries=[],
                concepts=[],
                indices=[],
                markets=[]
            )


# 全局实例
strategy_execution_engine = StrategyExecutionEngine()