"""
策略执行相关的数据模型
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
from app.schemas.strategy import SelectedStock


class StockScope(str, Enum):
    """股票范围"""
    ALL = "all"                    # 全部股票
    INDUSTRY = "industry"          # 按行业筛选
    CONCEPT = "concept"            # 按概念筛选
    INDEX = "index"                # 按指数成分股筛选
    CUSTOM = "custom"              # 自定义股票列表


class MarketType(str, Enum):
    """市场类型"""
    ALL = "all"                    # 全部市场
    MAIN_BOARD = "main"            # 主板
    SMALL_MEDIUM = "sme"           # 中小板
    GROWTH = "gem"                 # 创业板
    STAR = "star"                  # 科创板
    BEIJING = "bj"                 # 北交所


class ExecutionStatus(str, Enum):
    """执行状态"""
    PENDING = "pending"            # 等待执行
    RUNNING = "running"            # 执行中
    DATA_FETCHING = "data_fetching"  # 数据获取中
    FACTOR_CALCULATING = "factor_calculating"  # 因子计算中
    RANKING = "ranking"            # 排序计算中
    FILTERING = "filtering"        # 筛选中
    COMPLETED = "completed"        # 执行完成
    FAILED = "failed"              # 执行失败
    CANCELLED = "cancelled"        # 已取消


class LogLevel(str, Enum):
    """日志级别"""
    INFO = "info"
    WARNING = "warning" 
    ERROR = "error"
    DEBUG = "debug"


class StockFilter(BaseModel):
    """股票筛选条件"""
    scope: StockScope = Field(..., description="股票范围")
    
    # 市场筛选
    markets: Optional[List[MarketType]] = Field(None, description="市场类型")
    
    # 行业筛选
    industries: Optional[List[str]] = Field(None, description="行业代码列表")
    exclude_industries: Optional[List[str]] = Field(None, description="排除的行业代码")
    
    # 概念筛选
    concepts: Optional[List[str]] = Field(None, description="概念代码列表")
    
    # 指数成分股
    index_codes: Optional[List[str]] = Field(None, description="指数代码列表")
    
    # 自定义股票列表
    custom_stocks: Optional[List[str]] = Field(None, description="自定义股票代码列表")
    
    # 基础筛选
    min_market_cap: Optional[float] = Field(None, ge=0, description="最小市值（万元）")
    max_market_cap: Optional[float] = Field(None, ge=0, description="最大市值（万元）")
    min_price: Optional[float] = Field(None, ge=0, description="最小股价（元）")
    max_price: Optional[float] = Field(None, ge=0, description="最大股价（元）")
    min_turnover: Optional[float] = Field(None, ge=0, le=100, description="最小换手率（%）")
    max_turnover: Optional[float] = Field(None, ge=0, le=100, description="最大换手率（%）")
    
    # 特殊股票筛选
    exclude_st: bool = Field(True, description="排除ST股票")
    exclude_new_stock: bool = Field(True, description="排除新股（上市不足60天）")
    exclude_suspend: bool = Field(True, description="排除停牌股票")
    
    # 流动性筛选
    min_avg_volume: Optional[float] = Field(None, ge=0, description="最小平均成交量（手）")
    min_list_days: Optional[int] = Field(60, ge=0, description="最小上市天数")
    
    @validator('max_market_cap')
    def validate_market_cap(cls, v, values):
        if v and 'min_market_cap' in values and values['min_market_cap']:
            if v <= values['min_market_cap']:
                raise ValueError("最大市值必须大于最小市值")
        return v
    
    @validator('max_price')
    def validate_price(cls, v, values):
        if v and 'min_price' in values and values['min_price']:
            if v <= values['min_price']:
                raise ValueError("最大股价必须大于最小股价")
        return v


class FactorDataRequest(BaseModel):
    """因子数据请求"""
    factor_id: str = Field(..., description="因子ID")
    required_fields: List[str] = Field(..., description="所需数据字段")
    start_date: Optional[str] = Field(None, description="开始日期")
    end_date: Optional[str] = Field(None, description="结束日期")
    period: Optional[int] = Field(None, description="数据周期（天）")


class ExecutionLog(BaseModel):
    """执行日志"""
    timestamp: datetime = Field(..., description="时间戳")
    level: LogLevel = Field(..., description="日志级别")
    stage: str = Field(..., description="执行阶段")
    message: str = Field(..., description="日志消息")
    details: Optional[Dict[str, Any]] = Field(None, description="详细信息")
    progress: Optional[float] = Field(None, ge=0, le=100, description="进度百分比")


class StageProgress(BaseModel):
    """阶段进度"""
    stage_name: str = Field(..., description="阶段名称")
    status: ExecutionStatus = Field(..., description="阶段状态")
    progress: float = Field(0, ge=0, le=100, description="进度百分比")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    error_message: Optional[str] = Field(None, description="错误信息")


class RateLimitSettings(BaseModel):
    """频率限制设置"""
    max_calls_per_minute: int = Field(10, ge=1, le=100, description="每分钟最大API调用次数")
    max_calls_per_hour: int = Field(200, ge=10, le=1000, description="每小时最大API调用次数")
    max_calls_per_day: int = Field(1000, ge=100, le=10000, description="每天最大API调用次数")
    concurrent_limit: int = Field(3, ge=1, le=10, description="并发调用限制")


class StrategyExecutionRequest(BaseModel):
    """策略执行请求"""
    execution_date: Optional[str] = Field(None, description="执行日期（YYYY-MM-DD）")
    stock_filter: StockFilter = Field(..., description="股票筛选条件")
    dry_run: bool = Field(False, description="是否为模拟执行")
    save_result: bool = Field(True, description="是否保存执行结果")
    enable_cache: bool = Field(True, description="是否启用数据缓存")
    max_execution_time: Optional[int] = Field(300, ge=60, le=3600, description="最大执行时间（秒）")
    rate_limit: Optional[RateLimitSettings] = Field(None, description="API频率限制设置")


class DataFetchSummary(BaseModel):
    """数据获取摘要"""
    total_stocks: int = Field(..., description="股票总数")
    fetched_stocks: int = Field(..., description="成功获取数据的股票数")
    failed_stocks: int = Field(..., description="获取失败的股票数")
    cache_hits: int = Field(0, description="缓存命中数")
    api_calls: int = Field(0, description="API调用次数")
    data_size_mb: float = Field(0, description="数据大小（MB）")
    fetch_time: float = Field(..., description="获取耗时（秒）")


class FactorCalculationSummary(BaseModel):
    """因子计算摘要"""
    factor_id: str = Field(..., description="因子ID")
    calculated_stocks: int = Field(..., description="计算成功的股票数")
    failed_stocks: int = Field(..., description="计算失败的股票数")
    calculation_time: float = Field(..., description="计算耗时（秒）")
    min_value: Optional[float] = Field(None, description="最小值")
    max_value: Optional[float] = Field(None, description="最大值")
    mean_value: Optional[float] = Field(None, description="平均值")
    std_value: Optional[float] = Field(None, description="标准差")


class StrategyExecutionResult(BaseModel):
    """策略执行结果"""
    execution_id: str = Field(..., description="执行ID")
    strategy_id: str = Field(..., description="策略ID")
    execution_date: str = Field(..., description="执行日期")
    status: ExecutionStatus = Field(..., description="执行状态")
    
    # 执行时间信息
    start_time: datetime = Field(..., description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    total_time: Optional[float] = Field(None, description="总耗时（秒）")
    
    # 执行参数
    stock_filter: StockFilter = Field(..., description="使用的股票筛选条件")
    is_dry_run: bool = Field(..., description="是否为模拟执行")
    
    # 执行进度
    stages: List[StageProgress] = Field(default_factory=list, description="各阶段进度")
    current_stage: Optional[str] = Field(None, description="当前阶段")
    overall_progress: float = Field(0, ge=0, le=100, description="总体进度")
    
    # 数据统计
    initial_stock_count: Optional[int] = Field(None, description="初始股票数量")
    filtered_stock_count: Optional[int] = Field(None, description="筛选后股票数量")
    final_stock_count: Optional[int] = Field(None, description="最终选中股票数量")
    
    # 执行摘要
    data_fetch_summary: Optional[DataFetchSummary] = Field(None, description="数据获取摘要")
    factor_summaries: List[FactorCalculationSummary] = Field(default_factory=list, description="因子计算摘要")
    
    # 错误信息
    error_message: Optional[str] = Field(None, description="错误信息")
    
    # 执行日志
    logs: List[ExecutionLog] = Field(default_factory=list, description="执行日志")


class StrategyExecutionDetailResult(StrategyExecutionResult):
    """详细的策略执行结果"""
    selected_stocks: List[SelectedStock] = Field(default_factory=list, description="选中的股票列表")
    factor_performance: Dict[str, Any] = Field(default_factory=dict, description="因子表现统计")


class StockUniverse(BaseModel):
    """股票池信息"""
    scope_type: StockScope = Field(..., description="股票池类型")
    scope_params: Dict[str, Any] = Field(..., description="股票池参数")
    total_stocks: int = Field(..., description="股票总数")
    stock_codes: List[str] = Field(..., description="股票代码列表")
    last_updated: datetime = Field(..., description="最后更新时间")


class AvailableScope(BaseModel):
    """可用的股票范围选项"""
    industries: List[Dict[str, str]] = Field(..., description="可用行业列表")
    concepts: List[Dict[str, str]] = Field(..., description="可用概念列表")
    indices: List[Dict[str, str]] = Field(..., description="可用指数列表")
    markets: List[Dict[str, str]] = Field(..., description="可用市场列表")


class ExecutionProgress(BaseModel):
    """实时执行进度"""
    execution_id: str = Field(..., description="执行ID")
    status: ExecutionStatus = Field(..., description="当前状态")
    current_stage: str = Field(..., description="当前阶段")
    overall_progress: float = Field(..., ge=0, le=100, description="总体进度")
    stage_progress: float = Field(..., ge=0, le=100, description="当前阶段进度")
    estimated_remaining: Optional[int] = Field(None, description="预计剩余时间（秒）")
    latest_log: Optional[ExecutionLog] = Field(None, description="最新日志")
    

class CancelExecutionRequest(BaseModel):
    """取消执行请求"""
    reason: Optional[str] = Field(None, description="取消原因")