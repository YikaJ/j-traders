"""
市场数据相关的Pydantic模型
"""

from pydantic import BaseModel
from typing import Optional


class MarketIndexResponse(BaseModel):
    """市场指数响应模型"""
    symbol: str
    name: str
    price: float
    change: float
    changePercent: float
    volume: int
    amount: float
    tradeDate: str


class StockQuoteResponse(BaseModel):
    """股票行情响应模型"""
    symbol: str
    name: str
    price: float
    change: float
    changePercent: float
    volume: int
    amount: float


class StockHistoryData(BaseModel):
    """股票历史数据点"""
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    amount: float


class StockHistoryResponse(BaseModel):
    """股票历史数据响应模型"""
    symbol: str
    data: list[StockHistoryData]