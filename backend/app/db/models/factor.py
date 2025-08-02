"""
因子数据库模型
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, Float, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base


class Factor(Base):
    """因子模型"""
    __tablename__ = "factors"
    
    id = Column(Integer, primary_key=True, index=True)
    factor_id = Column(String(100), unique=True, index=True, nullable=False, comment="因子ID")
    name = Column(String(200), nullable=False, comment="因子名称")
    display_name = Column(String(200), nullable=False, comment="显示名称")
    description = Column(Text, comment="因子描述")
    category = Column(String(50), nullable=False, comment="因子分类")
    
    # 核心字段：Python公式代码
    formula = Column(Text, nullable=False, comment="Python公式代码")
    
    # 配置字段
    input_fields = Column(JSON, comment="输入字段列表")
    default_parameters = Column(JSON, comment="默认参数配置")
    parameter_schema = Column(JSON, comment="参数验证schema")
    calculation_method = Column(String(50), default="custom", comment="计算方法")
    
    # 状态字段
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_builtin = Column(Boolean, default=False, comment="是否内置因子")
    
    # 统计字段
    usage_count = Column(Integer, default=0, comment="使用次数")
    last_used_at = Column(DateTime, comment="最后使用时间")
    
    # 时间字段
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 版本控制
    version = Column(String(20), default="1.0.0", comment="版本号")
    
    def __repr__(self):
        return f"<Factor(id={self.id}, factor_id='{self.factor_id}', name='{self.name}')>"


class FactorFormulaHistory(Base):
    """因子公式历史记录"""
    __tablename__ = "factor_formula_history"
    
    id = Column(Integer, primary_key=True, index=True)
    factor_id = Column(String(100), nullable=False, index=True, comment="因子ID")
    
    # 公式变更记录
    old_formula = Column(Text, comment="旧公式")
    new_formula = Column(Text, nullable=False, comment="新公式")
    old_description = Column(Text, comment="旧描述")
    new_description = Column(Text, comment="新描述")
    
    # 变更信息
    changed_by = Column(String(100), comment="变更人")
    change_reason = Column(Text, comment="变更原因")
    
    # 时间字段
    created_at = Column(DateTime, server_default=func.now(), comment="变更时间")
    
    def __repr__(self):
        return f"<FactorFormulaHistory(id={self.id}, factor_id='{self.factor_id}')>"


class FactorValue(Base):
    """因子值记录"""
    __tablename__ = "factor_values"
    
    id = Column(Integer, primary_key=True, index=True)
    factor_id = Column(String(100), nullable=False, index=True, comment="因子ID")
    symbol = Column(String(20), nullable=False, comment="股票代码")
    execution_id = Column(Integer, ForeignKey("strategy_executions.id"), comment="执行ID")
    
    # 因子值
    value = Column(Float, nullable=False, comment="因子值")
    percentile = Column(Float, comment="百分位数")
    rank = Column(Integer, comment="排名")
    
    # 时间字段
    calculated_at = Column(DateTime, server_default=func.now(), comment="计算时间")
    
    # 关联关系
    execution = relationship("StrategyExecution", backref="factor_values")
    
    def __repr__(self):
        return f"<FactorValue(id={self.id}, factor_id='{self.factor_id}', symbol='{self.symbol}')>"


class WeightPreset(Base):
    """权重预设模型"""
    __tablename__ = "weight_presets"
    
    id = Column(String(100), primary_key=True, index=True, comment="预设ID")
    name = Column(String(200), nullable=False, comment="预设名称")
    description = Column(Text, comment="预设描述")
    
    # 配置字段
    applicable_categories = Column(JSON, comment="适用分类列表")
    weights = Column(JSON, comment="权重配置")
    is_default = Column(Boolean, default=False, comment="是否为默认预设")
    
    # 统计字段
    usage_count = Column(Integer, default=0, comment="使用次数")
    last_used_at = Column(DateTime, comment="最后使用时间")
    
    # 时间字段
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    def __repr__(self):
        return f"<WeightPreset(id='{self.id}', name='{self.name}')>"