"""
股票基础信息模型
"""

from sqlalchemy import Column, String, Float, DateTime, Boolean, Text, Integer
from sqlalchemy.sql import func
from app.db.database import Base


class Stock(Base):
    """股票基础信息表"""
    __tablename__ = "stocks"

    # 主键：股票代码（如：000001.SZ）
    symbol = Column(String(20), primary_key=True, index=True)
    
    # 基础信息
    name = Column(String(100), nullable=False, comment="股票名称")
    industry = Column(String(50), comment="所属行业")
    area = Column(String(50), comment="所属地区")
    market = Column(String(10), comment="市场类型：SZ/SH")
    
    # 上市信息
    list_date = Column(String(10), comment="上市日期")
    list_status = Column(String(10), default="L", comment="上市状态：L上市 D退市 P暂停")
    
    # 基本财务指标
    total_share = Column(Float, comment="总股本(万股)")
    float_share = Column(Float, comment="流通股本(万股)")
    
    # 元数据
    is_active = Column(Boolean, default=True, comment="是否活跃")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    def __repr__(self):
        return f"<Stock(symbol='{self.symbol}', name='{self.name}')>"


class StockDaily(Base):
    """股票日线数据表"""
    __tablename__ = "stock_daily"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True, comment="股票代码")
    trade_date = Column(String(10), nullable=False, index=True, comment="交易日期")
    
    # OHLCV数据
    open = Column(Float, comment="开盘价")
    high = Column(Float, comment="最高价")
    low = Column(Float, comment="最低价")
    close = Column(Float, comment="收盘价")
    pre_close = Column(Float, comment="昨收价")
    change = Column(Float, comment="涨跌额")
    pct_chg = Column(Float, comment="涨跌幅(%)")
    vol = Column(Float, comment="成交量(手)")
    amount = Column(Float, comment="成交额(千元)")
    
    # 技术指标
    turnover_rate = Column(Float, comment="换手率(%)")
    turnover_rate_f = Column(Float, comment="换手率(自由流通股)")
    volume_ratio = Column(Float, comment="量比")
    pe = Column(Float, comment="市盈率")
    pe_ttm = Column(Float, comment="市盈率(TTM)")
    pb = Column(Float, comment="市净率")
    ps = Column(Float, comment="市销率")
    ps_ttm = Column(Float, comment="市销率(TTM)")
    dv_ratio = Column(Float, comment="股息率(%)")
    dv_ttm = Column(Float, comment="股息率(TTM)(%)")
    total_share = Column(Float, comment="总股本(万股)")
    float_share = Column(Float, comment="流通股本(万股)")
    free_share = Column(Float, comment="自由流通股本(万股)")
    total_mv = Column(Float, comment="总市值(万元)")
    circ_mv = Column(Float, comment="流通市值(万元)")
    
    # 元数据
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    
    def __repr__(self):
        return f"<StockDaily(symbol='{self.symbol}', date='{self.trade_date}', close={self.close})>"


class MarketIndex(Base):
    """市场指数表"""
    __tablename__ = "market_indices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True, comment="指数代码")
    name = Column(String(100), nullable=False, comment="指数名称")
    trade_date = Column(String(10), nullable=False, index=True, comment="交易日期")
    
    # OHLCV数据
    open = Column(Float, comment="开盘点数")
    high = Column(Float, comment="最高点数")
    low = Column(Float, comment="最低点数")
    close = Column(Float, comment="收盘点数")
    pre_close = Column(Float, comment="昨收盘点数")
    change = Column(Float, comment="涨跌点")
    pct_chg = Column(Float, comment="涨跌幅(%)")
    vol = Column(Float, comment="成交量(手)")
    amount = Column(Float, comment="成交额(千元)")
    
    # 元数据
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    
    def __repr__(self):
        return f"<MarketIndex(symbol='{self.symbol}', date='{self.trade_date}', close={self.close})>"