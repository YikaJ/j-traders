"""
策略管理相关的Pydantic模型
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime


class StrategyFactor(BaseModel):
    """策略中的因子配置"""
    factor_id: str = Field(..., description="因子ID")
    weight: float = Field(..., ge=0, le=1, description="权重，范围0-1")
    is_enabled: bool = Field(True, description="是否启用")
    
    class Config:
        json_schema_extra = {
            "example": {
                "factor_id": "alpha001",
                "weight": 0.3,
                "is_enabled": True
            }
        }


class StrategyFilter(BaseModel):
    """策略筛选条件"""
    min_market_cap: Optional[float] = Field(None, ge=0, description="最小市值（万元）")
    max_market_cap: Optional[float] = Field(None, ge=0, description="最大市值（万元）")
    min_price: Optional[float] = Field(None, ge=0, description="最小股价")
    max_price: Optional[float] = Field(None, ge=0, description="最大股价")
    min_turnover: Optional[float] = Field(None, ge=0, le=100, description="最小换手率（%）")
    max_turnover: Optional[float] = Field(None, ge=0, le=100, description="最大换手率（%）")
    exclude_st: bool = Field(True, description="排除ST股票")
    exclude_new_stock: bool = Field(True, description="排除新股（上市不足60天）")
    exclude_suspend: bool = Field(True, description="排除停牌股票")
    industries: Optional[List[str]] = Field(None, description="包含的行业代码")
    exclude_industries: Optional[List[str]] = Field(None, description="排除的行业代码")


class StrategyConfig(BaseModel):
    """策略配置"""
    max_results: int = Field(50, ge=1, le=1000, description="最大选股数量")
    rebalance_frequency: str = Field("weekly", description="调仓频率：daily, weekly, monthly")
    ranking_method: str = Field("composite", description="排序方法：composite, weighted_sum")
    standardization_method: str = Field("zscore", description="标准化方法：zscore, rank, sign, minmax, robust")
    standardization_lookback: int = Field(252, ge=1, le=1000, description="标准化回看期数")
    
    
class StrategyBase(BaseModel):
    """策略基础模型"""
    name: str = Field(..., min_length=1, max_length=100, description="策略名称")
    description: Optional[str] = Field(None, max_length=500, description="策略描述")
    factors: List[StrategyFactor] = Field(..., min_items=1, description="因子配置列表")
    filters: Optional[StrategyFilter] = Field(None, description="筛选条件")
    config: Optional[StrategyConfig] = Field(None, description="策略配置")
    
    @validator('factors')
    def validate_factors(cls, v):
        if not v:
            raise ValueError("至少需要选择一个因子")
        
        # 检查权重总和
        total_weight = sum(factor.weight for factor in v if factor.is_enabled)
        if abs(total_weight - 1.0) > 0.001:  # 允许小数点误差
            raise ValueError(f"启用因子的权重总和必须为1.0，当前为{total_weight}")
        
        # 检查因子ID重复
        factor_ids = [factor.factor_id for factor in v]
        if len(factor_ids) != len(set(factor_ids)):
            raise ValueError("因子ID不能重复")
            
        return v
    
    @validator('filters')
    def validate_filters(cls, v):
        if v:
            # 验证市值范围
            if v.min_market_cap and v.max_market_cap:
                if v.min_market_cap >= v.max_market_cap:
                    raise ValueError("最小市值必须小于最大市值")
            
            # 验证价格范围
            if v.min_price and v.max_price:
                if v.min_price >= v.max_price:
                    raise ValueError("最小股价必须小于最大股价")
            
            # 验证换手率范围
            if v.min_turnover and v.max_turnover:
                if v.min_turnover >= v.max_turnover:
                    raise ValueError("最小换手率必须小于最大换手率")
        
        return v


class StrategyCreate(StrategyBase):
    """创建策略请求模型"""
    pass


class StrategyUpdate(BaseModel):
    """更新策略请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    factors: Optional[List[StrategyFactor]] = Field(None, min_items=1)
    filters: Optional[StrategyFilter] = None
    config: Optional[StrategyConfig] = None
    is_active: Optional[bool] = None
    
    @validator('factors')
    def validate_factors(cls, v):
        if v is not None:
            # 检查权重总和
            total_weight = sum(factor.weight for factor in v if factor.is_enabled)
            if abs(total_weight - 1.0) > 0.001:
                raise ValueError(f"启用因子的权重总和必须为1.0，当前为{total_weight}")
            
            # 检查因子ID重复
            factor_ids = [factor.factor_id for factor in v]
            if len(factor_ids) != len(set(factor_ids)):
                raise ValueError("因子ID不能重复")
        
        return v


class StrategyResponse(StrategyBase):
    """策略响应模型"""
    strategy_id: str = Field(..., description="策略ID")
    is_active: bool = Field(..., description="是否启用")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    created_by: Optional[str] = Field(None, description="创建者")
    
    # 统计信息
    execution_count: int = Field(0, description="执行次数")
    last_executed_at: Optional[datetime] = Field(None, description="最后执行时间")
    avg_execution_time: Optional[float] = Field(None, description="平均执行时间（秒）")
    last_result_count: Optional[int] = Field(None, description="最后一次选股数量")
    
    class Config:
        from_attributes = True


class StrategyExecutionRequest(BaseModel):
    """策略执行请求"""
    execution_date: Optional[str] = Field(None, description="执行日期（YYYY-MM-DD）")
    dry_run: bool = Field(False, description="是否为模拟执行")
    save_result: bool = Field(True, description="是否保存执行结果")


class StrategyExecutionResult(BaseModel):
    """策略执行结果"""
    execution_id: str = Field(..., description="执行ID")
    strategy_id: str = Field(..., description="策略ID")
    execution_date: str = Field(..., description="执行日期")
    execution_time: float = Field(..., description="执行耗时（秒）")
    stock_count: int = Field(..., description="选中股票数量")
    is_dry_run: bool = Field(..., description="是否为模拟执行")
    status: str = Field(..., description="执行状态：success, failed, timeout")
    error_message: Optional[str] = Field(None, description="错误信息")
    created_at: datetime = Field(..., description="执行时间")


class SelectedStock(BaseModel):
    """选中的股票"""
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    composite_score: float = Field(..., description="综合得分")
    factor_scores: Dict[str, float] = Field(..., description="各因子得分")
    rank: int = Field(..., description="排名")
    market_cap: Optional[float] = Field(None, description="市值（万元）")
    price: Optional[float] = Field(None, description="当前价格")
    industry: Optional[str] = Field(None, description="所属行业")


class StrategyExecutionDetail(StrategyExecutionResult):
    """策略执行详细结果"""
    selected_stocks: List[SelectedStock] = Field(..., description="选中的股票列表")
    factor_performance: Dict[str, Any] = Field(..., description="因子表现统计")
    execution_log: List[str] = Field(..., description="执行日志")


class StrategyListRequest(BaseModel):
    """策略列表查询请求"""
    is_active: Optional[bool] = Field(None, description="是否启用")
    created_by: Optional[str] = Field(None, description="创建者筛选")
    keyword: Optional[str] = Field(None, description="关键词搜索")
    skip: int = Field(0, ge=0, description="跳过记录数")
    limit: int = Field(20, ge=1, le=100, description="返回记录数")


class StrategyListResponse(BaseModel):
    """策略列表响应"""
    strategies: List[StrategyResponse] = Field(..., description="策略列表")
    total: int = Field(..., description="总记录数")
    skip: int = Field(..., description="跳过记录数")
    limit: int = Field(..., description="返回记录数")