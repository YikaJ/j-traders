"""
内置因子库相关的Pydantic模型
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum


class FactorCategory(str, Enum):
    """因子分类枚举"""
    TREND = "trend"           # 趋势类
    MOMENTUM = "momentum"     # 动量类  
    VOLUME = "volume"         # 价量类
    VOLATILITY = "volatility" # 波动率类
    VALUATION = "valuation"   # 估值类
    ALPHA101_EXTENDED = "alpha101_extended"  # Alpha101扩展因子
    ALPHA101_MORE_FACTORS = "alpha101_more_factors"  # Alpha101更多因子
    ALPHA101_PHASE2 = "alpha101_phase2"  # Alpha101第二阶段因子


class CalculationMethod(str, Enum):
    """计算方法枚举"""
    TALIB = "talib"          # 使用TA-Lib库
    CUSTOM = "custom"        # 自定义计算
    FORMULA = "formula"      # 公式计算


class FactorParameters(BaseModel):
    """因子参数模型"""
    period: Optional[int] = Field(None, ge=1, le=252, description="周期参数")
    fast_period: Optional[int] = Field(None, ge=1, le=100, description="快线周期")
    slow_period: Optional[int] = Field(None, ge=1, le=100, description="慢线周期")
    signal_period: Optional[int] = Field(None, ge=1, le=50, description="信号线周期")
    multiplier: Optional[float] = Field(None, ge=0.1, le=10.0, description="乘数参数")
    custom_params: Dict[str, Any] = Field(default_factory=dict, description="自定义参数")


class BuiltinFactorBase(BaseModel):
    """内置因子基础模型"""
    name: str = Field(..., max_length=100, description="因子英文名称")
    display_name: str = Field(..., max_length=100, description="因子显示名称")
    description: Optional[str] = Field(None, description="因子描述")
    category: FactorCategory = Field(..., description="因子分类")
    calculation_method: CalculationMethod = Field(..., description="计算方法")
    formula: Optional[str] = Field(None, description="计算公式")
    default_parameters: FactorParameters = Field(default_factory=FactorParameters, description="默认参数")
    parameter_schema: Dict[str, Any] = Field(default_factory=dict, description="参数验证schema")
    input_fields: List[str] = Field(default_factory=list, description="需要的输入字段")
    output_type: str = Field("single", description="输出类型")
    is_active: bool = Field(True, description="是否启用")


class BuiltinFactorCreate(BuiltinFactorBase):
    """创建内置因子请求模型"""
    pass


class BuiltinFactorUpdate(BaseModel):
    """更新内置因子请求模型"""
    display_name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    default_parameters: Optional[FactorParameters] = None
    is_active: Optional[bool] = None


class BuiltinFactorResponse(BuiltinFactorBase):
    """内置因子响应模型"""
    id: str = Field(..., description="因子ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class FactorPreviewRequest(BaseModel):
    """因子预览请求模型"""
    factor_id: str = Field(..., description="因子ID")
    parameters: FactorParameters = Field(default_factory=FactorParameters, description="参数配置")
    sample_stocks: Optional[List[str]] = Field(None, description="样本股票代码列表")


class FactorPreviewResult(BaseModel):
    """因子预览结果模型"""
    factor_id: str = Field(..., description="因子ID")
    parameters: FactorParameters = Field(..., description="使用的参数")
    sample_data: List[Dict[str, float]] = Field(..., description="样本数据")
    statistics: Dict[str, float] = Field(..., description="统计信息")
    chart_data: List[Dict[str, Any]] = Field(..., description="图表数据")
    calculation_time: float = Field(..., description="计算耗时")


class ValidationResult(BaseModel):
    """参数验证结果模型"""
    is_valid: bool = Field(..., description="是否有效")
    error_message: Optional[str] = Field(None, description="错误信息")
    warnings: List[str] = Field(default_factory=list, description="警告信息")


# =============================================================================
# 策略配置相关模型
# =============================================================================

class WeightPresetType(str, Enum):
    """权重预设类型枚举"""
    EQUAL = "equal"                    # 等权重
    MARKET_CAP = "market_cap"         # 市值加权
    INVERSE_VOLATILITY = "inverse_vol" # 反波动率加权
    RISK_PARITY = "risk_parity"       # 风险平价
    CUSTOM = "custom"                  # 自定义


class SelectedFactor(BaseModel):
    """选择的因子模型"""
    factor_id: str = Field(..., description="因子ID")
    factor_type: str = Field(..., description="因子类型：builtin/custom")
    factor_name: str = Field(..., description="因子名称")
    parameters: FactorParameters = Field(default_factory=FactorParameters, description="参数配置")
    weight: float = Field(..., ge=0.0, le=1.0, description="权重")
    is_enabled: bool = Field(True, description="是否启用")


class StrategyConfigBase(BaseModel):
    """策略配置基础模型"""
    name: str = Field(..., max_length=100, description="策略名称")
    description: Optional[str] = Field(None, description="策略描述")
    factors: List[SelectedFactor] = Field(..., description="因子配置列表")
    filters: Dict[str, Any] = Field(default_factory=dict, description="筛选条件")
    max_results: int = Field(100, ge=1, le=1000, description="最大结果数量")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    
    @validator('factors')
    def validate_weights_sum(cls, v):
        """验证权重总和"""
        if not v:  # 如果因子列表为空，跳过验证
            return v
        
        total_weight = sum(f.weight for f in v if f.is_enabled)
        if not (0.99 <= total_weight <= 1.01):  # 允许1%的误差
            raise ValueError('启用因子的权重总和必须等于100%')
        return v


class StrategyConfigCreate(StrategyConfigBase):
    """创建策略配置请求模型"""
    pass


class StrategyConfigUpdate(BaseModel):
    """更新策略配置请求模型"""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    factors: Optional[List[SelectedFactor]] = None
    filters: Optional[Dict[str, Any]] = None
    max_results: Optional[int] = Field(None, ge=1, le=1000)
    tags: Optional[List[str]] = None
    
    @validator('factors')
    def validate_weights_sum(cls, v):
        """验证权重总和"""
        if v is None:  # 如果不更新因子配置，跳过验证
            return v
        
        total_weight = sum(f.weight for f in v if f.is_enabled)
        if not (0.99 <= total_weight <= 1.01):
            raise ValueError('启用因子的权重总和必须等于100%')
        return v


class StrategyConfigResponse(StrategyConfigBase):
    """策略配置响应模型"""
    id: str = Field(..., description="策略配置ID")
    created_by: Optional[str] = Field(None, description="创建者")
    last_used_at: Optional[datetime] = Field(None, description="最后使用时间")
    usage_count: int = Field(0, description="使用次数")
    is_template: bool = Field(False, description="是否为模板")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class StrategyPreviewResult(BaseModel):
    """策略预览结果模型"""
    config_summary: Dict[str, Any] = Field(..., description="配置摘要")
    factor_weights: List[Dict[str, Any]] = Field(..., description="因子权重信息")
    estimated_results: Dict[str, int] = Field(..., description="预期结果数量")
    risk_assessment: Dict[str, str] = Field(..., description="风险评估")
    recommendations: List[str] = Field(..., description="建议列表")


class PaginatedStrategies(BaseModel):
    """分页策略列表模型"""
    items: List[StrategyConfigResponse] = Field(..., description="策略列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="页面大小")
    pages: int = Field(..., description="总页数")


class BatchOperationResult(BaseModel):
    """批量操作结果模型"""
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    failed_items: List[Dict[str, str]] = Field(..., description="失败项目详情")


# =============================================================================
# 策略模板相关模型
# =============================================================================

class StrategyTemplateCategory(str, Enum):
    """策略模板分类枚举"""
    VALUE = "value"           # 价值投资
    GROWTH = "growth"         # 成长投资  
    TECHNICAL = "technical"   # 技术面
    MOMENTUM = "momentum"     # 动量策略
    QUALITY = "quality"       # 质量因子


class RiskLevel(str, Enum):
    """风险等级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class StrategyTemplateBase(BaseModel):
    """策略模板基础模型"""
    name: str = Field(..., max_length=100, description="模板名称")
    display_name: str = Field(..., max_length=100, description="显示名称")
    description: Optional[str] = Field(None, description="模板描述")
    category: StrategyTemplateCategory = Field(..., description="模板分类")
    factor_configs: List[Dict[str, Any]] = Field(..., description="因子配置")
    default_weights: Dict[str, float] = Field(..., description="默认权重")
    applicable_markets: List[str] = Field(default_factory=list, description="适用市场")
    risk_level: RiskLevel = Field(..., description="风险等级")
    expected_return_range: str = Field(..., description="预期收益范围")
    usage_scenarios: str = Field(..., description="使用场景")
    is_active: bool = Field(True, description="是否启用")


class StrategyTemplateResponse(StrategyTemplateBase):
    """策略模板响应模型"""
    id: str = Field(..., description="模板ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class TemplateCustomizations(BaseModel):
    """模板个性化定制参数"""
    custom_weights: Optional[Dict[str, float]] = Field(None, description="自定义权重")
    additional_filters: Optional[Dict[str, Any]] = Field(None, description="额外筛选条件")
    max_results: Optional[int] = Field(None, ge=1, le=1000, description="最大结果数量")


class WeightPreset(BaseModel):
    """权重预设方案模型"""
    id: str = Field(..., description="预设ID")
    name: str = Field(..., description="预设名称")
    description: str = Field(..., description="预设描述")
    preset_type: WeightPresetType = Field(..., description="预设类型")
    calculation_method: str = Field(..., description="计算方法")
    is_default: bool = Field(False, description="是否为默认")


class WeightOptimizationResult(BaseModel):
    """权重优化结果模型"""
    optimized_weights: Dict[str, float] = Field(..., description="优化后的权重")
    optimization_method: str = Field(..., description="优化方法")
    performance_metrics: Dict[str, float] = Field(..., description="性能指标")
    recommendations: List[str] = Field(..., description="优化建议")


# =============================================================================
# 因子分析相关模型
# =============================================================================

class FactorStatisticsBase(BaseModel):
    """因子统计基础模型"""
    factor_id: str = Field(..., description="因子ID")
    factor_type: str = Field(..., description="因子类型")
    analysis_date: datetime = Field(..., description="分析日期")
    mean_value: float = Field(..., description="均值")
    std_deviation: float = Field(..., description="标准差")
    min_value: float = Field(..., description="最小值")
    max_value: float = Field(..., description="最大值")
    quantile_25: float = Field(..., description="25%分位数")
    quantile_50: float = Field(..., description="50%分位数")
    quantile_75: float = Field(..., description="75%分位数")
    skewness: float = Field(..., description="偏度")
    kurtosis: float = Field(..., description="峰度")
    null_ratio: float = Field(..., description="空值比例")
    effectiveness_score: float = Field(..., description="有效性得分")


class FactorStatisticsResponse(FactorStatisticsBase):
    """因子统计响应模型"""
    id: int = Field(..., description="统计记录ID")
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        from_attributes = True


class CorrelationMatrix(BaseModel):
    """因子相关性矩阵模型"""
    factor_ids: List[str] = Field(..., description="因子ID列表")
    factor_names: List[str] = Field(..., description="因子名称列表")
    correlation_matrix: List[List[float]] = Field(..., description="相关性矩阵")
    p_value_matrix: List[List[float]] = Field(..., description="P值矩阵")
    analysis_date: datetime = Field(..., description="分析日期")
    sample_size: int = Field(..., description="样本数量")


class EffectivenessMetrics(BaseModel):
    """因子有效性指标模型"""
    factor_id: str = Field(..., description="因子ID")
    discriminative_power: float = Field(..., description="区分度")
    stability_score: float = Field(..., description="稳定性得分")
    information_ratio: float = Field(..., description="信息比率")
    quantile_spread: float = Field(..., description="分位数间差异")
    monotonicity: float = Field(..., description="单调性得分")


class QuantileAnalysisResult(BaseModel):
    """分位数分析结果模型"""
    quantile_groups: List[Dict[str, Any]] = Field(..., description="分位数分组")
    performance_metrics: Dict[str, List[float]] = Field(..., description="性能指标")
    statistical_significance: Dict[str, float] = Field(..., description="统计显著性")


class FactorStatisticsResult(BaseModel):
    """因子统计分析结果模型"""
    factors: List[FactorStatisticsResponse] = Field(..., description="因子统计列表")
    analysis_summary: Dict[str, Any] = Field(..., description="分析摘要")


class FactorComparisonResult(BaseModel):
    """因子对比分析结果模型"""
    comparison_data: List[Dict[str, Any]] = Field(..., description="对比数据")
    comparison_charts: List[Dict[str, Any]] = Field(..., description="对比图表")
    insights: List[str] = Field(..., description="分析洞察")


class EffectivenessAnalysisResult(BaseModel):
    """因子有效性分析结果模型"""
    effectiveness_metrics: EffectivenessMetrics = Field(..., description="有效性指标")
    quantile_analysis: QuantileAnalysisResult = Field(..., description="分位数分析")
    recommendations: List[str] = Field(..., description="使用建议")


class FactorCalculationRecord(BaseModel):
    """因子计算记录模型"""
    factor_id: str = Field(..., description="因子ID")
    calculation_date: datetime = Field(..., description="计算日期")
    status: str = Field(..., description="计算状态")
    execution_time: float = Field(..., description="执行耗时")
    sample_count: int = Field(..., description="样本数量")
    success_rate: float = Field(..., description="成功率")