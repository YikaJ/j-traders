"""
因子相关的Pydantic模型
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class FactorTagBase(BaseModel):
    """因子标签基础模型"""
    name: str = Field(..., description="标签名称")
    display_name: str = Field(..., description="显示名称")
    description: Optional[str] = Field(None, description="标签描述")
    color: Optional[str] = Field("#3B82F6", description="标签颜色")


class FactorTagCreate(FactorTagBase):
    """创建因子标签请求模型"""
    pass


class FactorTagUpdate(BaseModel):
    """更新因子标签请求模型"""
    display_name: Optional[str] = Field(None, description="显示名称")
    description: Optional[str] = Field(None, description="标签描述")
    color: Optional[str] = Field(None, description="标签颜色")
    is_active: Optional[bool] = Field(None, description="是否启用")


class FactorTagResponse(FactorTagBase):
    """因子标签响应模型"""
    id: int
    is_active: bool
    usage_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FactorTagRelationCreate(BaseModel):
    """创建因子标签关联请求模型"""
    factor_id: str = Field(..., description="因子ID")
    tag_ids: List[int] = Field(..., description="标签ID列表")


class FactorTagRelationResponse(BaseModel):
    """因子标签关联响应模型"""
    factor_id: str
    tag_ids: List[int]
    tags: List[FactorTagResponse]

    class Config:
        from_attributes = True


# 现有的因子模型保持不变
class FactorBase(BaseModel):
    """因子基础模型"""
    name: str = Field(..., description="因子名称")
    display_name: str = Field(..., description="显示名称")
    description: Optional[str] = Field(None, description="因子描述")
    code: str = Field(..., description="因子代码")
    normalization_method: str = Field(default="z_score", description="标准化方法")
    normalization_code: Optional[str] = Field(None, description="标准化代码")
    default_parameters: Dict[str, Any] = Field(default={}, description="默认参数配置")
    parameter_schema: Optional[Dict[str, Any]] = Field(None, description="参数验证schema")
    calculation_method: str = Field(default="custom", description="计算方法")


class FactorCreate(FactorBase):
    """创建因子请求模型"""
    pass


class FactorUpdate(BaseModel):
    """更新因子请求模型"""
    name: Optional[str] = Field(None, description="因子名称")
    display_name: Optional[str] = Field(None, description="显示名称")
    description: Optional[str] = Field(None, description="因子描述")
    code: Optional[str] = Field(None, description="因子代码")
    normalization_method: Optional[str] = Field(None, description="标准化方法")
    normalization_code: Optional[str] = Field(None, description="标准化代码")
    default_parameters: Optional[Dict[str, Any]] = Field(None, description="默认参数配置")
    parameter_schema: Optional[Dict[str, Any]] = Field(None, description="参数验证schema")
    calculation_method: Optional[str] = Field(None, description="计算方法")
    is_active: Optional[bool] = Field(None, description="是否启用")


class FactorResponse(FactorBase):
    """因子响应模型"""
    id: str
    is_active: bool
    is_builtin: bool
    usage_count: int
    last_used_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    version: str
    tags: Optional[List[FactorTagResponse]] = Field(default=[], description="关联的标签")

    class Config:
        from_attributes = True


class FactorTestRequest(BaseModel):
    """因子测试请求模型"""
    test_data: Dict[str, Any] = Field(..., description="测试数据")
    parameters: Optional[Dict[str, Any]] = Field(default={}, description="测试参数")


class FactorTestResponse(BaseModel):
    """因子测试响应模型"""
    success: bool
    result: Optional[Dict[str, Any]] = Field(None, description="测试结果")
    error: Optional[str] = Field(None, description="错误信息")
    execution_time: Optional[float] = Field(None, description="执行时间(秒)")


class FactorTestResult(BaseModel):
    """单个股票的因子测试结果"""
    is_valid: bool
    errors: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    result: Optional[Any] = None


class FactorValidationResult(BaseModel):
    """因子代码验证结果"""
    id: str
    is_valid: bool
    errors: Optional[List[str]] = None
    warnings: Optional[List[str]] = None


# 策略相关模型
class StrategyBase(BaseModel):
    """策略基础模型"""
    name: str
    description: Optional[str] = None
    factorIds: List[int]  # 使用的因子ID列表
    factorWeights: Optional[Dict[str, float]] = None  # 因子权重
    maxResults: Optional[int] = 50  # 最大结果数量
    minMarketCap: Optional[float] = None  # 最小市值过滤
    maxMarketCap: Optional[float] = None  # 最大市值过滤
    excludeSt: Optional[bool] = True  # 排除ST股票
    excludeNewStock: Optional[bool] = True  # 排除新股
    minTurnover: Optional[float] = None  # 最小换手率


class StrategyCreate(StrategyBase):
    """创建策略请求模型"""
    pass


class StrategyUpdate(BaseModel):
    """更新策略请求模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    factorIds: Optional[List[int]] = None
    factorWeights: Optional[Dict[str, float]] = None
    maxResults: Optional[int] = None
    minMarketCap: Optional[float] = None
    maxMarketCap: Optional[float] = None
    excludeSt: Optional[bool] = None
    excludeNewStock: Optional[bool] = None
    minTurnover: Optional[float] = None
    isActive: Optional[bool] = None


class StrategyResponse(StrategyBase):
    """策略响应模型"""
    id: int
    isActive: bool
    executionCount: int
    lastExecutedAt: Optional[str] = None
    avgExecutionTime: Optional[float] = None
    createdAt: str
    updatedAt: str
    
    class Config:
        from_attributes = True


class StrategyExecutionRequest(BaseModel):
    """策略执行请求模型"""
    executionDate: Optional[str] = None  # 执行日期，默认为今天
    dryRun: Optional[bool] = False  # 是否为测试运行


class SelectionResult(BaseModel):
    """选股结果模型"""
    symbol: str
    name: str
    totalScore: float
    rank: int
    factorScores: Dict[str, float]  # 各因子得分
    price: Optional[float] = None
    marketCap: Optional[float] = None
    peRatio: Optional[float] = None
    pbRatio: Optional[float] = None


class StrategyExecutionResponse(BaseModel):
    """策略执行响应模型"""
    executionId: int
    success: bool
    message: str
    executionTime: float
    totalStocks: int
    resultCount: int
    results: List[SelectionResult]
    statistics: Dict[str, Any]


# 权重预设相关模型
class WeightPreset(BaseModel):
    """权重预设模型"""
    id: str
    name: str
    description: str
    applicable_categories: List[str]
    weights: Dict[str, float]  # 因子ID到权重的映射
    is_default: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class WeightPresetCreate(BaseModel):
    """创建权重预设请求模型"""
    name: str
    description: str
    applicable_categories: List[str]
    weights: Dict[str, float]
    is_default: bool = False


class WeightPresetUpdate(BaseModel):
    """更新权重预设请求模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    applicable_categories: Optional[List[str]] = None
    weights: Optional[Dict[str, float]] = None
    is_default: Optional[bool] = None


class WeightValidationResult(BaseModel):
    """权重验证结果"""
    is_valid: bool
    total_weight: float
    message: str
    warnings: List[str] = []


class WeightOptimizationResult(BaseModel):
    """权重优化结果"""
    optimized_factors: List[Dict[str, Any]]  # 优化后的因子列表
    optimization_method: str
    performance_metrics: Dict[str, float]
    recommendations: List[str]
    analysis_details: Dict[str, Any]


class WeightSuggestionRequest(BaseModel):
    """权重建议请求模型"""
    factors: List[Dict[str, Any]]  # 因子列表
    optimization_method: str = "correlation_adjusted"
    target_volatility: Optional[float] = None
    target_return: Optional[float] = None