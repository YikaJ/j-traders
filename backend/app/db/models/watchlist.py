"""
自选股相关模型
"""

from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean
from sqlalchemy.sql import func
from app.db.database import Base


class Watchlist(Base):
    """自选股表"""
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True, comment="股票代码")
    name = Column(String(100), comment="股票名称")
    
    # 用户信息（暂时不实现用户系统，默认为单用户）
    user_id = Column(String(50), default="default", comment="用户ID")
    
    # 自选股信息
    notes = Column(Text, comment="备注信息")
    tags = Column(String(200), comment="标签，逗号分隔")
    
    # 提醒设置
    alert_enabled = Column(Boolean, default=False, comment="是否启用价格提醒")
    alert_price_high = Column(String(20), comment="价格上限提醒")
    alert_price_low = Column(String(20), comment="价格下限提醒")
    alert_pct_change = Column(String(10), comment="涨跌幅提醒阈值")
    
    # 元数据
    added_at = Column(DateTime, server_default=func.now(), comment="添加时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    def __repr__(self):
        return f"<Watchlist(symbol='{self.symbol}', name='{self.name}')>"


class WatchlistGroup(Base):
    """自选股分组表"""
    __tablename__ = "watchlist_groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="分组名称")
    description = Column(Text, comment="分组描述")
    color = Column(String(10), comment="分组颜色")
    
    # 用户信息
    user_id = Column(String(50), default="default", comment="用户ID")
    
    # 排序
    sort_order = Column(Integer, default=0, comment="排序顺序")
    
    # 元数据
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    def __repr__(self):
        return f"<WatchlistGroup(id={self.id}, name='{self.name}')>"


class WatchlistGroupMember(Base):
    """自选股分组成员关系表"""
    __tablename__ = "watchlist_group_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, nullable=False, comment="分组ID")
    watchlist_id = Column(Integer, nullable=False, comment="自选股ID")
    
    # 元数据
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    
    def __repr__(self):
        return f"<WatchlistGroupMember(group_id={self.group_id}, watchlist_id={self.watchlist_id})>"