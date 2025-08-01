"""
自选股相关的Pydantic模型
"""

from pydantic import BaseModel
from typing import Optional


class WatchlistBase(BaseModel):
    """自选股基础模型"""
    symbol: str
    name: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[str] = None
    alertEnabled: Optional[bool] = False
    alertPriceHigh: Optional[str] = None
    alertPriceLow: Optional[str] = None
    alertPctChange: Optional[str] = None


class WatchlistCreate(WatchlistBase):
    """创建自选股请求模型"""
    pass


class WatchlistUpdate(BaseModel):
    """更新自选股请求模型"""
    notes: Optional[str] = None
    tags: Optional[str] = None
    alertEnabled: Optional[bool] = None
    alertPriceHigh: Optional[str] = None
    alertPriceLow: Optional[str] = None
    alertPctChange: Optional[str] = None


class WatchlistResponse(WatchlistBase):
    """自选股响应模型"""
    id: int
    addedAt: str
    
    class Config:
        from_attributes = True


class StockSearchResponse(BaseModel):
    """股票搜索响应模型"""
    symbol: str
    name: str
    industry: str
    area: str
    market: str
    listDate: str