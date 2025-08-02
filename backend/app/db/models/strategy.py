"""
策略管理数据库模型
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, Float, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base
import uuid


class Strategy(Base):
    """策略模型"""
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(String(100), unique=True, index=True, nullable=False, comment="策略唯一ID")
    name = Column(String(200), nullable=False, comment="策略名称")
    description = Column(Text, comment="策略描述")
    
    # 因子配置 - 存储为JSON
    factors = Column(JSON, nullable=False, comment="因子配置列表")
    
    # 筛选条件 - 存储为JSON  
    filters = Column(JSON, comment="筛选条件配置")
    
    # 策略配置 - 存储为JSON
    config = Column(JSON, comment="策略配置")
    
    # 状态字段
    is_active = Column(Boolean, default=True, comment="是否启用")
    
    # 创建者信息
    created_by = Column(String(100), comment="创建者")
    
    # 统计字段
    execution_count = Column(Integer, default=0, comment="执行次数")
    last_executed_at = Column(DateTime, comment="最后执行时间")
    avg_execution_time = Column(Float, comment="平均执行时间（秒）")
    last_result_count = Column(Integer, comment="最后一次选股数量")
    
    # 时间字段
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关联关系
    executions = relationship("StrategyExecution", back_populates="strategy", cascade="all, delete-orphan")
    
    def __init__(self, **kwargs):
        if not kwargs.get('strategy_id'):
            kwargs['strategy_id'] = str(uuid.uuid4())
        super().__init__(**kwargs)
    
    def __repr__(self):
        return f"<Strategy(id={self.id}, strategy_id='{self.strategy_id}', name='{self.name}')>"


class StrategyExecution(Base):
    """策略执行记录"""
    __tablename__ = "strategy_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(String(100), unique=True, index=True, nullable=False, comment="执行唯一ID")
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False, comment="策略ID")
    
    # 执行信息
    execution_date = Column(String(10), nullable=False, comment="执行日期（YYYY-MM-DD）")
    execution_time = Column(Float, comment="执行耗时（秒）")
    stock_count = Column(Integer, comment="选中股票数量")
    is_dry_run = Column(Boolean, default=False, comment="是否为模拟执行")
    
    # 执行状态
    status = Column(String(20), nullable=False, comment="执行状态：success, failed, timeout")
    error_message = Column(Text, comment="错误信息")
    
    # 执行结果 - 存储为JSON
    selected_stocks = Column(JSON, comment="选中的股票列表")
    factor_performance = Column(JSON, comment="因子表现统计")
    execution_log = Column(JSON, comment="执行日志")
    
    # 是否保存结果
    is_saved = Column(Boolean, default=True, comment="是否保存结果")
    
    # 时间字段
    created_at = Column(DateTime, server_default=func.now(), comment="执行时间")
    
    # 关联关系
    strategy = relationship("Strategy", back_populates="executions")
    
    def __init__(self, **kwargs):
        if not kwargs.get('execution_id'):
            kwargs['execution_id'] = str(uuid.uuid4())
        super().__init__(**kwargs)
    
    def __repr__(self):
        return f"<StrategyExecution(id={self.id}, execution_id='{self.execution_id}', strategy_id={self.strategy_id})>"


class StrategyTemplate(Base):
    """策略模板"""
    __tablename__ = "strategy_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(String(100), unique=True, index=True, nullable=False, comment="模板唯一ID")
    name = Column(String(200), nullable=False, comment="模板名称")
    description = Column(Text, comment="模板描述")
    category = Column(String(50), comment="模板分类")
    
    # 模板配置 - 存储为JSON
    factors = Column(JSON, nullable=False, comment="因子配置模板")
    filters = Column(JSON, comment="筛选条件模板")
    config = Column(JSON, comment="策略配置模板")
    
    # 状态字段
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_builtin = Column(Boolean, default=False, comment="是否内置模板")
    
    # 统计字段
    usage_count = Column(Integer, default=0, comment="使用次数")
    
    # 时间字段
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    def __init__(self, **kwargs):
        if not kwargs.get('template_id'):
            kwargs['template_id'] = str(uuid.uuid4())
        super().__init__(**kwargs)
    
    def __repr__(self):
        return f"<StrategyTemplate(id={self.id}, template_id='{self.template_id}', name='{self.name}')>"