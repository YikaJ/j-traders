"""
股票数据Schema
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class StockBase(BaseModel):
    """股票基础信息"""
    symbol: str
    name: str
    industry: Optional[str] = None
    area: Optional[str] = None
    market: Optional[str] = None


class StockListResponse(StockBase):
    """股票列表响应"""
    list_date: Optional[str] = None
    list_status: Optional[str] = None
    is_active: bool = True


class StockSearchResponse(StockBase):
    """股票搜索响应"""
    pass


class StockDetailResponse(StockBase):
    """股票详细信息响应"""
    list_date: Optional[str] = None
    list_status: Optional[str] = None
    total_share: Optional[float] = None
    float_share: Optional[float] = None
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class StockSyncResponse(BaseModel):
    """股票同步响应"""
    success: bool
    message: str
    total_fetched: int
    new_stocks: int
    updated_stocks: int
    errors: int
    duration: float


class StockSyncInfoResponse(BaseModel):
    """股票同步信息响应"""
    last_sync_time: Optional[str] = None
    stock_count: Dict[str, int]
    sync_available: bool


class StockStatsResponse(BaseModel):
    """股票统计响应"""
    total_stocks: int
    active_stocks: int
    sz_market_stocks: int
    sh_market_stocks: int
    timestamp: str