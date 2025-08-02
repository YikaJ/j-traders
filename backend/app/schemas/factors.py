"""
因子相关的Pydantic模型
"""

from pydantic import BaseModel
from typing import Optional, List, Any, Dict


class FactorBase(BaseModel):
    """因子基础模型"""
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    code: str
    isActive: Optional[bool] = True
    version: Optional[str] = "1.0"


class FactorCreate(FactorBase):
    """创建因子请求模型"""
    pass


class FactorUpdate(BaseModel):
    """更新因子请求模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    code: Optional[str] = None
    isActive: Optional[bool] = None


class FactorResponse(FactorBase):
    """因子响应模型"""
    id: int
    usageCount: int
    lastUsedAt: Optional[str] = None
    createdAt: str
    updatedAt: str
    
    class Config:
        from_attributes = True


class FactorTestRequest(BaseModel):
    """因子测试请求模型"""
    symbols: List[str]  # 测试股票代码列表
    startDate: Optional[str] = None  # 开始日期 YYYYMMDD
    endDate: Optional[str] = None  # 结束日期 YYYYMMDD


class FactorTestResult(BaseModel):
    """单个股票的因子测试结果"""
    symbol: str
    name: str
    value: float
    percentile: Optional[float] = None  # 百分位数
    rank: Optional[int] = None  # 排名


class FactorTestResponse(BaseModel):
    """因子测试响应模型"""
    success: bool
    message: str
    executionTime: float  # 执行时间（秒）
    results: List[FactorTestResult]
    statistics: Dict[str, Any]  # 统计信息


class FactorValidationResult(BaseModel):
    """因子代码验证结果"""
    is_valid: bool
    error_message: Optional[str] = None
    warnings: List[str] = []


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