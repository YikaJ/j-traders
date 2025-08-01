"""
因子和策略相关模型
"""

from sqlalchemy import Column, String, Float, DateTime, Boolean, Text, Integer, JSON
from sqlalchemy.sql import func
from app.db.database import Base


class Factor(Base):
    """因子定义表"""
    __tablename__ = "factors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="因子名称")
    description = Column(Text, comment="因子描述")
    category = Column(String(50), comment="因子分类：估值/技术/基本面/情绪")
    
    # 因子代码
    code = Column(Text, nullable=False, comment="Python因子计算代码")
    
    # 因子元信息
    is_active = Column(Boolean, default=True, comment="是否启用")
    version = Column(String(20), default="1.0", comment="版本号")
    
    # 统计信息
    usage_count = Column(Integer, default=0, comment="使用次数")
    last_used_at = Column(DateTime, comment="最后使用时间")
    
    # 元数据
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    def __repr__(self):
        return f"<Factor(id={self.id}, name='{self.name}', category='{self.category}')>"


class Strategy(Base):
    """策略定义表"""
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="策略名称")
    description = Column(Text, comment="策略描述")
    
    # 策略配置
    factor_ids = Column(JSON, comment="使用的因子ID列表")
    factor_weights = Column(JSON, comment="因子权重配置")
    max_results = Column(Integer, default=50, comment="最大结果数量")
    
    # 过滤条件
    min_market_cap = Column(Float, comment="最小市值(万元)")
    max_market_cap = Column(Float, comment="最大市值(万元)")
    exclude_st = Column(Boolean, default=True, comment="是否排除ST股票")
    exclude_new_stock = Column(Boolean, default=True, comment="是否排除新股")
    min_turnover = Column(Float, comment="最小换手率")
    
    # 策略状态
    is_active = Column(Boolean, default=True, comment="是否启用")
    
    # 统计信息
    execution_count = Column(Integer, default=0, comment="执行次数")
    last_executed_at = Column(DateTime, comment="最后执行时间")
    avg_execution_time = Column(Float, comment="平均执行时间(秒)")
    
    # 元数据
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    def __repr__(self):
        return f"<Strategy(id={self.id}, name='{self.name}')>"


class StrategyExecution(Base):
    """策略执行记录表"""
    __tablename__ = "strategy_executions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_id = Column(Integer, nullable=False, comment="策略ID")
    
    # 执行信息
    execution_date = Column(String(10), nullable=False, comment="执行日期")
    execution_time = Column(Float, comment="执行耗时(秒)")
    total_stocks = Column(Integer, comment="总股票数")
    result_count = Column(Integer, comment="结果数量")
    
    # 执行状态
    status = Column(String(20), default="running", comment="执行状态：running/completed/failed")
    error_message = Column(Text, comment="错误信息")
    
    # 元数据
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    completed_at = Column(DateTime, comment="完成时间")
    
    def __repr__(self):
        return f"<StrategyExecution(id={self.id}, strategy_id={self.strategy_id}, status='{self.status}')>"


class SelectionResult(Base):
    """选股结果表"""
    __tablename__ = "selection_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    execution_id = Column(Integer, nullable=False, comment="执行记录ID")
    
    # 股票信息
    symbol = Column(String(20), nullable=False, comment="股票代码")
    name = Column(String(100), comment="股票名称")
    
    # 评分信息
    total_score = Column(Float, comment="综合得分")
    rank = Column(Integer, comment="排名")
    
    # 因子得分详情
    factor_scores = Column(JSON, comment="各因子得分详情")
    
    # 股票基本信息（快照）
    price = Column(Float, comment="当时价格")
    market_cap = Column(Float, comment="市值")
    pe_ratio = Column(Float, comment="市盈率")
    pb_ratio = Column(Float, comment="市净率")
    
    # 元数据
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    
    def __repr__(self):
        return f"<SelectionResult(symbol='{self.symbol}', rank={self.rank}, score={self.total_score})>"


class FactorValue(Base):
    """因子值历史表"""
    __tablename__ = "factor_values"

    id = Column(Integer, primary_key=True, autoincrement=True)
    factor_id = Column(Integer, nullable=False, comment="因子ID")
    symbol = Column(String(20), nullable=False, comment="股票代码")
    trade_date = Column(String(10), nullable=False, comment="交易日期")
    
    # 因子值
    value = Column(Float, comment="因子值")
    normalized_value = Column(Float, comment="标准化后的值")
    percentile = Column(Float, comment="百分位数")
    
    # 元数据
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    
    def __repr__(self):
        return f"<FactorValue(factor_id={self.factor_id}, symbol='{self.symbol}', value={self.value})>"


# =============================================================================
# 新增：内置因子库和策略配置增强模型
# =============================================================================

class BuiltinFactor(Base):
    """内置因子定义表"""
    __tablename__ = "builtin_factors"

    id = Column(String(36), primary_key=True, comment="因子ID")
    name = Column(String(100), nullable=False, comment="因子英文名称")
    display_name = Column(String(100), nullable=False, comment="因子显示名称")
    description = Column(Text, comment="因子描述")
    category = Column(String(50), nullable=False, comment="因子分类：trend/momentum/volume/volatility/valuation")
    
    # 计算方法
    calculation_method = Column(String(50), nullable=False, comment="计算方法：talib/custom/formula")
    formula = Column(Text, comment="计算公式或TA-Lib函数名")
    
    # 参数配置
    default_parameters = Column(JSON, comment="默认参数配置")
    parameter_schema = Column(JSON, comment="参数验证schema")
    input_fields = Column(JSON, comment="需要的输入字段 ['close', 'high', 'low', 'volume']")
    output_type = Column(String(20), default="single", comment="输出类型：single/multiple")
    
    # 状态信息
    is_active = Column(Boolean, default=True, comment="是否启用")
    
    # 元数据
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    def __repr__(self):
        return f"<BuiltinFactor(id='{self.id}', name='{self.name}', category='{self.category}')>"


class StrategyConfig(Base):
    """策略配置表"""
    __tablename__ = "strategy_configs"

    id = Column(String(36), primary_key=True, comment="策略配置ID")
    name = Column(String(100), nullable=False, comment="策略名称")
    description = Column(Text, comment="策略描述")
    
    # 因子配置
    factor_configs = Column(JSON, nullable=False, comment="因子配置数组")
    weight_config = Column(JSON, nullable=False, comment="权重配置")
    
    # 过滤条件
    filters = Column(JSON, comment="筛选条件")
    max_results = Column(Integer, default=100, comment="最大结果数量")
    
    # 元信息
    created_by = Column(String(50), comment="创建者")
    tags = Column(String(500), comment="标签，逗号分隔")
    
    # 使用统计
    last_used_at = Column(DateTime, comment="最后使用时间")
    usage_count = Column(Integer, default=0, comment="使用次数")
    is_template = Column(Boolean, default=False, comment="是否为模板")
    
    # 元数据
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    def __repr__(self):
        return f"<StrategyConfig(id='{self.id}', name='{self.name}')>"


class FactorStatistics(Base):
    """因子统计分析表"""
    __tablename__ = "factor_statistics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    factor_id = Column(String(36), nullable=False, comment="因子ID")
    factor_type = Column(String(20), nullable=False, comment="因子类型：builtin/custom")
    analysis_date = Column(DateTime, nullable=False, comment="分析日期")
    
    # 统计指标
    mean_value = Column(Float, comment="均值")
    std_deviation = Column(Float, comment="标准差")
    min_value = Column(Float, comment="最小值")
    max_value = Column(Float, comment="最大值")
    quantile_25 = Column(Float, comment="25%分位数")
    quantile_50 = Column(Float, comment="50%分位数（中位数）")
    quantile_75 = Column(Float, comment="75%分位数")
    skewness = Column(Float, comment="偏度")
    kurtosis = Column(Float, comment="峰度")
    null_ratio = Column(Float, comment="空值比例")
    
    # 有效性指标
    effectiveness_score = Column(Float, comment="有效性得分")
    
    # 元数据
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    
    def __repr__(self):
        return f"<FactorStatistics(factor_id='{self.factor_id}', analysis_date='{self.analysis_date}')>"


class StrategyTemplate(Base):
    """策略模板表"""
    __tablename__ = "strategy_templates"

    id = Column(String(36), primary_key=True, comment="模板ID")
    name = Column(String(100), nullable=False, comment="模板名称")
    display_name = Column(String(100), nullable=False, comment="显示名称")
    description = Column(Text, comment="模板描述")
    category = Column(String(50), comment="模板分类：value/growth/technical/momentum/quality")
    
    # 模板配置
    factor_configs = Column(JSON, nullable=False, comment="因子配置")
    default_weights = Column(JSON, nullable=False, comment="默认权重")
    
    # 适用信息
    applicable_markets = Column(JSON, comment="适用市场")
    risk_level = Column(String(20), comment="风险等级：low/medium/high")
    expected_return_range = Column(String(50), comment="预期收益范围")
    usage_scenarios = Column(Text, comment="使用场景")
    
    # 状态信息
    is_active = Column(Boolean, default=True, comment="是否启用")
    
    # 元数据
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    def __repr__(self):
        return f"<StrategyTemplate(id='{self.id}', name='{self.name}', category='{self.category}')>"


class FactorCorrelation(Base):
    """因子相关性表"""
    __tablename__ = "factor_correlations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    factor1_id = Column(String(36), nullable=False, comment="因子1 ID")
    factor1_type = Column(String(20), nullable=False, comment="因子1类型：builtin/custom")
    factor2_id = Column(String(36), nullable=False, comment="因子2 ID")
    factor2_type = Column(String(20), nullable=False, comment="因子2类型：builtin/custom")
    
    # 相关性指标
    correlation_coefficient = Column(Float, comment="相关系数")
    p_value = Column(Float, comment="P值")
    analysis_date = Column(DateTime, nullable=False, comment="分析日期")
    sample_size = Column(Integer, comment="样本数量")
    
    # 元数据
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    
    def __repr__(self):
        return f"<FactorCorrelation(factor1='{self.factor1_id}', factor2='{self.factor2_id}', correlation={self.correlation_coefficient})>"