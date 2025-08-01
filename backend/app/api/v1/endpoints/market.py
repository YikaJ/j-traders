"""
大盘监控API接口
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from datetime import datetime, timedelta

from app.db.database import get_db
from app.db.models.stock import MarketIndex, StockDaily
from app.services.tushare_service import tushare_service
from app.schemas.market import MarketIndexResponse, StockQuoteResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/indices", response_model=List[MarketIndexResponse])
async def get_market_indices(
    trade_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取市场指数数据
    
    Args:
        trade_date: 交易日期 YYYYMMDD，默认为最新交易日
        db: 数据库会话
    
    Returns:
        市场指数列表
    """
    try:
        # 先从数据库获取数据
        query = db.query(MarketIndex)
        if trade_date:
            query = query.filter(MarketIndex.trade_date == trade_date)
        
        db_indices = query.order_by(MarketIndex.trade_date.desc()).limit(10).all()
        
        # 如果数据库没有数据或数据过旧，从Tushare获取
        if not db_indices or (not trade_date and len(db_indices) < 3):
            logger.info("从Tushare获取最新指数数据")
            try:
                indices_df = await tushare_service.get_market_indices(trade_date)
                if not indices_df.empty:
                    # 保存到数据库
                    for _, row in indices_df.iterrows():
                        index_data = MarketIndex(
                            symbol=row.get('ts_code', ''),
                            name=row.get('ts_code', ''),  # 这里需要映射到中文名称
                            trade_date=row.get('trade_date', ''),
                            open=row.get('open'),
                            high=row.get('high'),
                            low=row.get('low'),
                            close=row.get('close'),
                            pre_close=row.get('pre_close'),
                            change=row.get('change'),
                            pct_chg=row.get('pct_chg'),
                            vol=row.get('vol'),
                            amount=row.get('amount')
                        )
                        db.merge(index_data)  # 使用merge避免重复
                    
                    db.commit()
                    # 重新查询
                    db_indices = query.order_by(MarketIndex.trade_date.desc()).limit(10).all()
            except Exception as e:
                logger.warning(f"获取Tushare数据失败，使用模拟数据: {e}")
        
        # 如果还是没有数据，返回模拟数据
        if not db_indices:
            return _get_mock_indices()
        
        # 转换为响应模型
        result = []
        for index in db_indices:
            result.append(MarketIndexResponse(
                symbol=index.symbol,
                name=_get_index_name(index.symbol),
                price=index.close or 0,
                change=index.change or 0,
                changePercent=index.pct_chg or 0,
                volume=int(index.vol or 0),
                amount=index.amount or 0,
                tradeDate=index.trade_date
            ))
        
        return result
    
    except Exception as e:
        logger.error(f"获取市场指数失败: {e}")
        raise HTTPException(status_code=500, detail="获取市场指数失败")


@router.get("/quotes", response_model=List[StockQuoteResponse])
async def get_stock_quotes(
    symbols: str,
    db: Session = Depends(get_db)
):
    """
    获取股票实时行情
    
    Args:
        symbols: 股票代码列表，逗号分隔
        db: 数据库会话
    
    Returns:
        股票行情列表
    """
    try:
        symbol_list = [s.strip() for s in symbols.split(',') if s.strip()]
        if not symbol_list:
            raise HTTPException(status_code=400, detail="股票代码不能为空")
        
        # 先尝试从Tushare获取实时数据
        try:
            quotes_df = await tushare_service.get_realtime_quotes(symbol_list)
            if not quotes_df.empty:
                result = []
                for _, row in quotes_df.iterrows():
                    result.append(StockQuoteResponse(
                        symbol=row.get('code', ''),
                        name=row.get('name', ''),
                        price=float(row.get('price', 0)),
                        change=float(row.get('change', 0)),
                        changePercent=float(row.get('changepercent', 0)),
                        volume=int(row.get('volume', 0)),
                        amount=float(row.get('amount', 0))
                    ))
                return result
        except Exception as e:
            logger.warning(f"获取实时行情失败，使用历史数据: {e}")
        
        # 如果实时数据获取失败，从数据库获取最新历史数据
        result = []
        for symbol in symbol_list:
            latest_data = db.query(StockDaily).filter(
                StockDaily.symbol == symbol
            ).order_by(StockDaily.trade_date.desc()).first()
            
            if latest_data:
                result.append(StockQuoteResponse(
                    symbol=latest_data.symbol,
                    name=latest_data.symbol,  # 这里需要从stock表获取名称
                    price=latest_data.close or 0,
                    change=latest_data.change or 0,
                    changePercent=latest_data.pct_chg or 0,
                    volume=int(latest_data.vol or 0),
                    amount=latest_data.amount or 0
                ))
            else:
                # 返回模拟数据
                result.append(_get_mock_quote(symbol))
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取股票行情失败: {e}")
        raise HTTPException(status_code=500, detail="获取股票行情失败")


@router.get("/history/{symbol}")
async def get_stock_history(
    symbol: str,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """
    获取股票历史数据
    
    Args:
        symbol: 股票代码
        days: 获取天数，默认30天
        db: 数据库会话
    
    Returns:
        股票历史数据
    """
    try:
        # 从数据库获取历史数据
        history_data = db.query(StockDaily).filter(
            StockDaily.symbol == symbol
        ).order_by(StockDaily.trade_date.desc()).limit(days).all()
        
        # 如果数据不足，尝试从Tushare获取
        if len(history_data) < min(days, 10):
            try:
                end_date = datetime.now().strftime('%Y%m%d')
                start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
                
                daily_df = await tushare_service.get_stock_daily(
                    symbol, start_date, end_date
                )
                
                if not daily_df.empty:
                    # 保存到数据库
                    for _, row in daily_df.iterrows():
                        daily_data = StockDaily(
                            symbol=row.get('ts_code', ''),
                            trade_date=row.get('trade_date', ''),
                            open=row.get('open'),
                            high=row.get('high'),
                            low=row.get('low'),
                            close=row.get('close'),
                            pre_close=row.get('pre_close'),
                            change=row.get('change'),
                            pct_chg=row.get('pct_chg'),
                            vol=row.get('vol'),
                            amount=row.get('amount')
                        )
                        db.merge(daily_data)
                    
                    db.commit()
                    # 重新查询
                    history_data = db.query(StockDaily).filter(
                        StockDaily.symbol == symbol
                    ).order_by(StockDaily.trade_date.desc()).limit(days).all()
                    
            except Exception as e:
                logger.warning(f"获取{symbol}历史数据失败: {e}")
        
        # 转换为响应格式
        result = {
            "symbol": symbol,
            "data": []
        }
        
        for data in reversed(history_data):  # 按时间正序
            result["data"].append({
                "date": data.trade_date,
                "open": data.open,
                "high": data.high,
                "low": data.low,
                "close": data.close,
                "volume": data.vol,
                "amount": data.amount
            })
        
        # 如果没有数据，返回模拟数据
        if not result["data"]:
            result["data"] = _get_mock_history(symbol, days)
        
        return result
    
    except Exception as e:
        logger.error(f"获取{symbol}历史数据失败: {e}")
        raise HTTPException(status_code=500, detail="获取历史数据失败")


def _get_index_name(symbol: str) -> str:
    """获取指数中文名称"""
    index_names = {
        "000001.SH": "上证指数",
        "399001.SZ": "深证成指",
        "399006.SZ": "创业板指",
        "000300.SH": "沪深300",
        "000905.SH": "中证500",
        "399905.SZ": "中证500"
    }
    return index_names.get(symbol, symbol)


def _get_mock_indices() -> List[MarketIndexResponse]:
    """获取模拟指数数据"""
    return [
        MarketIndexResponse(
            symbol="000001.SH",
            name="上证指数",
            price=3245.12,
            change=15.43,
            changePercent=0.48,
            volume=245600000,
            amount=1234567890,
            tradeDate=datetime.now().strftime('%Y%m%d')
        ),
        MarketIndexResponse(
            symbol="399001.SZ",
            name="深证成指",
            price=10234.56,
            change=-23.45,
            changePercent=-0.23,
            volume=189400000,
            amount=987654321,
            tradeDate=datetime.now().strftime('%Y%m%d')
        ),
        MarketIndexResponse(
            symbol="399006.SZ",
            name="创业板指",
            price=2156.78,
            change=8.92,
            changePercent=0.42,
            volume=156700000,
            amount=654321987,
            tradeDate=datetime.now().strftime('%Y%m%d')
        )
    ]


def _get_mock_quote(symbol: str) -> StockQuoteResponse:
    """获取模拟股票行情"""
    import random
    
    base_price = random.uniform(10, 100)
    change = random.uniform(-2, 2)
    
    return StockQuoteResponse(
        symbol=symbol,
        name=f"股票{symbol}",
        price=base_price,
        change=change,
        changePercent=(change / base_price) * 100,
        volume=random.randint(100000, 10000000),
        amount=random.uniform(1000000, 100000000)
    )


def _get_mock_history(symbol: str, days: int) -> List[dict]:
    """获取模拟历史数据"""
    import random
    
    data = []
    base_price = random.uniform(20, 80)
    
    for i in range(days):
        date = (datetime.now() - timedelta(days=days-i-1)).strftime('%Y%m%d')
        
        # 模拟价格波动
        change = random.uniform(-0.05, 0.05)
        base_price *= (1 + change)
        
        high = base_price * random.uniform(1.0, 1.05)
        low = base_price * random.uniform(0.95, 1.0)
        open_price = random.uniform(low, high)
        close = base_price
        
        data.append({
            "date": date,
            "open": round(open_price, 2),
            "high": round(high, 2),
            "low": round(low, 2),
            "close": round(close, 2),
            "volume": random.randint(100000, 5000000),
            "amount": random.uniform(1000000, 50000000)
        })
    
    return data