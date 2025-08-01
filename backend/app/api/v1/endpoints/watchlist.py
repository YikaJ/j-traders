"""
自选股管理API接口
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.db.database import get_db
from app.db.models.watchlist import Watchlist
from app.db.models.stock import Stock
from app.services.tushare_service import tushare_service
from app.schemas.watchlist import (
    WatchlistResponse, 
    WatchlistCreate, 
    WatchlistUpdate,
    StockSearchResponse
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[WatchlistResponse])
async def get_watchlist(
    user_id: str = "default",
    db: Session = Depends(get_db)
):
    """
    获取自选股列表
    
    Args:
        user_id: 用户ID，默认为default
        db: 数据库会话
    
    Returns:
        自选股列表
    """
    try:
        watchlist_items = db.query(Watchlist).filter(
            Watchlist.user_id == user_id
        ).order_by(Watchlist.added_at.desc()).all()
        
        result = []
        for item in watchlist_items:
            # 获取股票基础信息
            stock_info = db.query(Stock).filter(Stock.symbol == item.symbol).first()
            
            result.append(WatchlistResponse(
                id=item.id,
                symbol=item.symbol,
                name=stock_info.name if stock_info else item.name or item.symbol,
                notes=item.notes or "",
                tags=item.tags or "",
                addedAt=item.added_at.isoformat() if item.added_at else "",
                alertEnabled=item.alert_enabled or False,
                alertPriceHigh=item.alert_price_high,
                alertPriceLow=item.alert_price_low,
                alertPctChange=item.alert_pct_change
            ))
        
        return result
    
    except Exception as e:
        logger.error(f"获取自选股列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取自选股列表失败")


@router.post("/", response_model=WatchlistResponse)
async def add_to_watchlist(
    watchlist_data: WatchlistCreate,
    user_id: str = "default",
    db: Session = Depends(get_db)
):
    """
    添加股票到自选股
    
    Args:
        watchlist_data: 自选股数据
        user_id: 用户ID
        db: 数据库会话
    
    Returns:
        添加的自选股信息
    """
    try:
        # 检查是否已存在
        existing = db.query(Watchlist).filter(
            Watchlist.symbol == watchlist_data.symbol,
            Watchlist.user_id == user_id
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="该股票已在自选股中")
        
        # 获取股票名称
        stock_name = watchlist_data.name
        if not stock_name:
            # 从股票基础信息表获取
            stock_info = db.query(Stock).filter(Stock.symbol == watchlist_data.symbol).first()
            if stock_info:
                stock_name = stock_info.name
            else:
                # 尝试从Tushare搜索获取
                try:
                    search_results = await tushare_service.search_stocks(watchlist_data.symbol, 1)
                    if search_results:
                        stock_name = search_results[0]['name']
                except Exception as e:
                    logger.warning(f"获取股票名称失败: {e}")
                    stock_name = watchlist_data.symbol
        
        # 创建自选股记录
        new_watchlist = Watchlist(
            symbol=watchlist_data.symbol,
            name=stock_name,
            user_id=user_id,
            notes=watchlist_data.notes or "",
            tags=watchlist_data.tags or "",
            alert_enabled=watchlist_data.alertEnabled or False,
            alert_price_high=watchlist_data.alertPriceHigh,
            alert_price_low=watchlist_data.alertPriceLow,
            alert_pct_change=watchlist_data.alertPctChange
        )
        
        db.add(new_watchlist)
        db.commit()
        db.refresh(new_watchlist)
        
        return WatchlistResponse(
            id=new_watchlist.id,
            symbol=new_watchlist.symbol,
            name=new_watchlist.name,
            notes=new_watchlist.notes or "",
            tags=new_watchlist.tags or "",
            addedAt=new_watchlist.added_at.isoformat(),
            alertEnabled=new_watchlist.alert_enabled or False,
            alertPriceHigh=new_watchlist.alert_price_high,
            alertPriceLow=new_watchlist.alert_price_low,
            alertPctChange=new_watchlist.alert_pct_change
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加自选股失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="添加自选股失败")


@router.put("/{watchlist_id}", response_model=WatchlistResponse)
async def update_watchlist(
    watchlist_id: int,
    watchlist_data: WatchlistUpdate,
    db: Session = Depends(get_db)
):
    """
    更新自选股信息
    
    Args:
        watchlist_id: 自选股ID
        watchlist_data: 更新数据
        db: 数据库会话
    
    Returns:
        更新后的自选股信息
    """
    try:
        watchlist_item = db.query(Watchlist).filter(Watchlist.id == watchlist_id).first()
        if not watchlist_item:
            raise HTTPException(status_code=404, detail="自选股不存在")
        
        # 更新字段
        if watchlist_data.notes is not None:
            watchlist_item.notes = watchlist_data.notes
        if watchlist_data.tags is not None:
            watchlist_item.tags = watchlist_data.tags
        if watchlist_data.alertEnabled is not None:
            watchlist_item.alert_enabled = watchlist_data.alertEnabled
        if watchlist_data.alertPriceHigh is not None:
            watchlist_item.alert_price_high = watchlist_data.alertPriceHigh
        if watchlist_data.alertPriceLow is not None:
            watchlist_item.alert_price_low = watchlist_data.alertPriceLow
        if watchlist_data.alertPctChange is not None:
            watchlist_item.alert_pct_change = watchlist_data.alertPctChange
        
        db.commit()
        db.refresh(watchlist_item)
        
        return WatchlistResponse(
            id=watchlist_item.id,
            symbol=watchlist_item.symbol,
            name=watchlist_item.name,
            notes=watchlist_item.notes or "",
            tags=watchlist_item.tags or "",
            addedAt=watchlist_item.added_at.isoformat(),
            alertEnabled=watchlist_item.alert_enabled or False,
            alertPriceHigh=watchlist_item.alert_price_high,
            alertPriceLow=watchlist_item.alert_price_low,
            alertPctChange=watchlist_item.alert_pct_change
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新自选股失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="更新自选股失败")


@router.delete("/{watchlist_id}")
async def remove_from_watchlist(
    watchlist_id: int,
    db: Session = Depends(get_db)
):
    """
    从自选股中移除股票
    
    Args:
        watchlist_id: 自选股ID
        db: 数据库会话
    
    Returns:
        操作结果
    """
    try:
        watchlist_item = db.query(Watchlist).filter(Watchlist.id == watchlist_id).first()
        if not watchlist_item:
            raise HTTPException(status_code=404, detail="自选股不存在")
        
        db.delete(watchlist_item)
        db.commit()
        
        return {"message": "已从自选股中移除", "symbol": watchlist_item.symbol}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"移除自选股失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="移除自选股失败")


@router.get("/search", response_model=List[StockSearchResponse])
async def search_stocks(
    keyword: str,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    搜索股票
    
    Args:
        keyword: 搜索关键词（股票代码或名称）
        limit: 返回结果数量限制
        db: 数据库会话
    
    Returns:
        股票搜索结果
    """
    try:
        if not keyword.strip():
            raise HTTPException(status_code=400, detail="搜索关键词不能为空")
        
        # 先从本地数据库搜索
        stocks = db.query(Stock).filter(
            (Stock.symbol.contains(keyword)) |
            (Stock.name.contains(keyword))
        ).limit(limit).all()
        
        result = []
        for stock in stocks:
            result.append(StockSearchResponse(
                symbol=stock.symbol,
                name=stock.name,
                industry=stock.industry or "",
                area=stock.area or "",
                market=stock.market or "",
                listDate=stock.list_date or ""
            ))
        
        # 如果本地结果不足，尝试从Tushare搜索
        if len(result) < min(limit, 5):
            try:
                tushare_results = await tushare_service.search_stocks(keyword, limit - len(result))
                for item in tushare_results:
                    # 避免重复
                    if not any(r.symbol == item['symbol'] for r in result):
                        result.append(StockSearchResponse(
                            symbol=item['symbol'],
                            name=item['name'],
                            industry=item.get('industry', ''),
                            area=item.get('area', ''),
                            market=item.get('market', ''),
                            listDate=item.get('list_date', '')
                        ))
            except Exception as e:
                logger.warning(f"Tushare搜索失败: {e}")
        
        # 如果还是没有结果，返回模拟数据
        if not result:
            result = _get_mock_search_results(keyword, limit)
        
        return result[:limit]
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"搜索股票失败: {e}")
        raise HTTPException(status_code=500, detail="搜索股票失败")


def _get_mock_search_results(keyword: str, limit: int) -> List[StockSearchResponse]:
    """获取模拟搜索结果"""
    mock_stocks = [
        {"symbol": "600519.SH", "name": "贵州茅台", "industry": "食品饮料", "area": "贵州"},
        {"symbol": "000858.SZ", "name": "五粮液", "industry": "食品饮料", "area": "四川"},
        {"symbol": "300750.SZ", "name": "宁德时代", "industry": "电池", "area": "福建"},
        {"symbol": "000001.SZ", "name": "平安银行", "industry": "银行", "area": "广东"},
        {"symbol": "600036.SH", "name": "招商银行", "industry": "银行", "area": "广东"},
    ]
    
    # 根据关键词过滤
    filtered = [
        stock for stock in mock_stocks 
        if keyword.lower() in stock["symbol"].lower() or keyword in stock["name"]
    ]
    
    if not filtered:
        # 如果没有匹配，返回前几个
        filtered = mock_stocks[:limit]
    
    result = []
    for stock in filtered[:limit]:
        result.append(StockSearchResponse(
            symbol=stock["symbol"],
            name=stock["name"],
            industry=stock.get("industry", ""),
            area=stock.get("area", ""),
            market="SH" if stock["symbol"].endswith(".SH") else "SZ",
            listDate="20100101"
        ))
    
    return result