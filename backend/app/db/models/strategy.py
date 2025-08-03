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
    start_time = Column(DateTime, nullable=False, comment="开始时间")
    end_time = Column(DateTime, comment="结束时间")
    total_time = Column(Float, comment="总耗时（秒）")
    
    # 执行状态
    status = Column(String(20), nullable=False, default="pending", comment="执行状态")
    current_stage = Column(String(50), comment="当前阶段")
    overall_progress = Column(Float, default=0.0, comment="总体进度")
    
    # 股票筛选条件
    stock_filter = Column(JSON, comment="股票筛选条件")
    is_dry_run = Column(Boolean, default=False, comment="是否为模拟执行")
    
    # 执行统计
    initial_stock_count = Column(Integer, comment="初始股票数量")
    filtered_stock_count = Column(Integer, comment="筛选后股票数量")
    final_stock_count = Column(Integer, comment="最终选中股票数量")
    
    # 执行摘要
    data_fetch_summary = Column(JSON, comment="数据获取摘要")
    factor_summaries = Column(JSON, comment="因子计算摘要")
    stages = Column(JSON, comment="各阶段进度")
    
    # 错误信息
    error_message = Column(Text, comment="错误信息")
    
    # 执行日志
    logs = Column(JSON, comment="执行日志")
    
    # 执行结果 - 存储为JSON
    selected_stocks = Column(JSON, comment="选中的股票列表")
    factor_performance = Column(JSON, comment="因子表现统计")
    
    # 时间字段
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
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


class SelectionResult(Base):
    """选股结果"""
    __tablename__ = "selection_results"
    
    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("strategy_executions.id"), nullable=False, comment="执行ID")
    
    # 股票信息
    symbol = Column(String(20), nullable=False, comment="股票代码")
    name = Column(String(100), comment="股票名称")
    
    # 评分信息
    total_score = Column(Float, comment="总评分")
    rank = Column(Integer, comment="排名")
    factor_scores = Column(JSON, comment="各因子得分")
    
    # 股票属性
    price = Column(Float, comment="当前价格")
    market_cap = Column(Float, comment="市值")
    pe_ratio = Column(Float, comment="市盈率")
    pb_ratio = Column(Float, comment="市净率")
    
    # 时间字段
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    
    # 关联关系
    execution = relationship("StrategyExecution", backref="results")
    
    def __repr__(self):
        return f"<SelectionResult(id={self.id}, symbol='{self.symbol}', rank={self.rank})>"