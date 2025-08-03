"""
因子相关的Pydantic模型
"""

from pydantic import BaseModel
from typing import Optional, List, Any, Dict


class FactorBase(BaseModel):
    """因子基础模型"""
    id: str
    name: str
    display_name: str
    description: Optional[str] = None
    category: str
    code: str
    input_fields: Optional[List[str]] = None
    default_parameters: Optional[Dict[str, Any]] = None
    parameter_schema: Optional[Dict[str, Any]] = None
    calculation_method: Optional[str] = "custom"
    is_active: Optional[bool] = True
    is_builtin: Optional[bool] = False
    usage_count: Optional[int] = 0
    last_used_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    version: Optional[str] = "1.0.0"


class FactorCreate(BaseModel):
    """创建因子请求模型"""
    id: Optional[str] = None  # 可选，后端会自动生成
    name: str
    display_name: str
    description: Optional[str] = None
    category: str
    code: str
    input_fields: Optional[List[str]] = None
    default_parameters: Optional[Dict[str, Any]] = None
    parameter_schema: Optional[Dict[str, Any]] = None
    calculation_method: Optional[str] = "custom"
    is_active: Optional[bool] = True
    is_builtin: Optional[bool] = False
    usage_count: Optional[int] = 0
    last_used_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    version: Optional[str] = "1.0.0"


class FactorUpdate(BaseModel):
    """更新因子请求模型"""
    name: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    code: Optional[str] = None
    input_fields: Optional[List[str]] = None
    default_parameters: Optional[Dict[str, Any]] = None
    parameter_schema: Optional[Dict[str, Any]] = None
    calculation_method: Optional[str] = None
    is_active: Optional[bool] = None
    is_builtin: Optional[bool] = None
    version: Optional[str] = None


class FactorResponse(FactorBase):
    """因子响应模型"""
    pass


class FactorTestRequest(BaseModel):
    """因子测试请求模型"""
    id: str
    code: str
    input_fields: Optional[List[str]] = None
    parameters: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Any]] = None


class FactorTestResult(BaseModel):
    """单个股票的因子测试结果"""
    is_valid: bool
    errors: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    result: Optional[Any] = None


class FactorTestResponse(BaseModel):
    """因子测试响应模型"""
    id: str
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