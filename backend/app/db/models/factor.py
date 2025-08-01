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