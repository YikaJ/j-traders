"""
股票数据API接口
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from datetime import datetime

from app.db.database import get_db
from app.services.stock_sync_service import stock_sync_service
from app.schemas.stock import (
    StockListResponse, 
    StockSyncResponse, 
    StockSearchResponse,
    StockSyncInfoResponse
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/list", response_model=List[StockListResponse])
async def get_stock_list(
    keyword: Optional[str] = None,
    market: Optional[str] = None,
    industry: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    获取股票列表
    
    Args:
        keyword: 搜索关键词（股票代码或名称）
        market: 市场类型（SZ/SH）
        industry: 行业分类
        limit: 返回数量限制
        offset: 偏移量
        db: 数据库会话
    
    Returns:
        股票列表
    """
    try:
        from app.db.models.stock import Stock
        
        # 构建查询
        query = db.query(Stock).filter(Stock.is_active == True)
        
        # 添加搜索条件
        if keyword:
            query = query.filter(
                (Stock.symbol.like(f'%{keyword}%')) |
                (Stock.name.like(f'%{keyword}%'))
            )
        
        if market:
            query = query.filter(Stock.market == market.upper())
        
        if industry:
            query = query.filter(Stock.industry.like(f'%{industry}%'))
        
        # 分页和排序
        stocks = query.order_by(Stock.symbol).offset(offset).limit(limit).all()
        
        # 转换为响应格式
        result = []
        for stock in stocks:
            result.append(StockListResponse(
                symbol=stock.symbol,
                name=stock.name,
                industry=stock.industry or "",
                area=stock.area or "",
                market=stock.market or "",
                list_date=stock.list_date or "",
                list_status=stock.list_status or "L",
                is_active=stock.is_active
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取股票列表失败")


@router.get("/search", response_model=List[StockSearchResponse])
async def search_stocks(
    q: str,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    搜索股票
    
    Args:
        q: 搜索关键词
        limit: 返回数量限制
        db: 数据库会话
    
    Returns:
        搜索结果
    """
    try:
        if not q or len(q.strip()) < 1:
            return []
        
        stocks = await stock_sync_service.search_stocks(db, q.strip(), limit)
        
        result = []
        for stock in stocks:
            result.append(StockSearchResponse(
                symbol=stock["symbol"],
                name=stock["name"],
                industry=stock.get("industry", ""),
                area=stock.get("area", ""),
                market=stock.get("market", "")
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"搜索股票失败: {e}")
        raise HTTPException(status_code=500, detail="搜索股票失败")


@router.get("/sync/info", response_model=StockSyncInfoResponse)
async def get_sync_info(db: Session = Depends(get_db)):
    """
    获取股票数据同步信息
    
    Args:
        db: 数据库会话
    
    Returns:
        同步信息
    """
    try:
        sync_info = await stock_sync_service.get_last_sync_info(db)
        
        return StockSyncInfoResponse(
            last_sync_time=sync_info["last_sync_time"],
            stock_count=sync_info["stock_count"],
            sync_available=sync_info["sync_available"]
        )
        
    except Exception as e:
        logger.error(f"获取同步信息失败: {e}", exc_info=True)
        # 在开发环境下返回更详细的错误信息
        if settings.DEBUG:
            raise HTTPException(status_code=500, detail=f"获取同步信息失败: {str(e)}")
        else:
            raise HTTPException(status_code=500, detail="获取同步信息失败")


@router.post("/sync", response_model=StockSyncResponse)
async def sync_stock_data(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    同步股票数据
    
    Args:
        background_tasks: 后台任务
        db: 数据库会话
    
    Returns:
        同步结果
    """
    try:
        logger.info("开始同步股票数据...")
        
        # 执行同步
        sync_result = await stock_sync_service.sync_stock_list(db)
        
        return StockSyncResponse(
            success=True,
            message="股票数据同步完成",
            total_fetched=sync_result["total_fetched"],
            new_stocks=sync_result["new_stocks"],
            updated_stocks=sync_result["updated_stocks"],
            errors=sync_result["errors"],
            duration=sync_result["duration"]
        )
        
    except Exception as e:
        logger.error(f"同步股票数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"同步股票数据失败: {str(e)}")


@router.get("/stats")
async def get_stock_stats(db: Session = Depends(get_db)):
    """
    获取股票统计信息
    
    Args:
        db: 数据库会话
    
    Returns:
        统计信息
    """
    try:
        stats = await stock_sync_service.get_stock_count(db)
        
        return {
            "total_stocks": stats["total"],
            "active_stocks": stats["active"],
            "sz_market_stocks": stats["sz_market"],
            "sh_market_stocks": stats["sh_market"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取股票统计失败: {e}")
        raise HTTPException(status_code=500, detail="获取股票统计失败")


@router.get("/{symbol}")
async def get_stock_detail(
    symbol: str,
    db: Session = Depends(get_db)
):
    """
    获取股票详细信息
    
    Args:
        symbol: 股票代码
        db: 数据库会话
    
    Returns:
        股票详细信息
    """
    try:
        from app.db.models.stock import Stock
        
        stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
        
        if not stock:
            raise HTTPException(status_code=404, detail="股票不存在")
        
        return {
            "symbol": stock.symbol,
            "name": stock.name,
            "industry": stock.industry,
            "area": stock.area,
            "market": stock.market,
            "list_date": stock.list_date,
            "list_status": stock.list_status,
            "total_share": stock.total_share,
            "float_share": stock.float_share,
            "is_active": stock.is_active,
            "created_at": stock.created_at.isoformat() if stock.created_at else None,
            "updated_at": stock.updated_at.isoformat() if stock.updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取股票详情失败: {e}")
        raise HTTPException(status_code=500, detail="获取股票详情失败")