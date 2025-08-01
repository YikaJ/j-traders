"""
大盘监控API接口
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from datetime import datetime, timedelta

from app.db.database import get_db
from app.db.models.stock import MarketIndex, StockDaily, Stock
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
        # 先从数据库获取数据，确保每个指数只返回最新的一条记录
        if trade_date:
            # 如果指定了日期，获取该日期的所有指数数据
            db_indices = db.query(MarketIndex).filter(
                MarketIndex.trade_date == trade_date
            ).all()
        else:
            # 获取每个指数的最新数据
            from sqlalchemy import func
            subquery = db.query(
                MarketIndex.symbol,
                func.max(MarketIndex.trade_date).label('max_date')
            ).group_by(MarketIndex.symbol).subquery()
            
            db_indices = db.query(MarketIndex).join(
                subquery,
                (MarketIndex.symbol == subquery.c.symbol) & 
                (MarketIndex.trade_date == subquery.c.max_date)
            ).all()
        
        # 如果数据库没有数据或数据过旧，从Tushare获取
        if not db_indices or (not trade_date and len(db_indices) < 3):
            logger.info("从Tushare获取最新指数数据")
            try:
                indices_df = await tushare_service.get_market_indices(trade_date)
                if not indices_df.empty:
                    # 保存到数据库，使用merge避免重复
                    for _, row in indices_df.iterrows():
                        index_data = MarketIndex(
                            symbol=row.get('ts_code', ''),
                            name=row.get('index_name', _get_index_name(row.get('ts_code', ''))),
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
                        db.merge(index_data)
                    
                    db.commit()
                    
                    # 重新查询，确保每个指数只返回最新的一条记录
                    if trade_date:
                        db_indices = db.query(MarketIndex).filter(
                            MarketIndex.trade_date == trade_date
                        ).all()
                    else:
                        subquery = db.query(
                            MarketIndex.symbol,
                            func.max(MarketIndex.trade_date).label('max_date')
                        ).group_by(MarketIndex.symbol).subquery()
                        
                        db_indices = db.query(MarketIndex).join(
                            subquery,
                            (MarketIndex.symbol == subquery.c.symbol) & 
                            (MarketIndex.trade_date == subquery.c.max_date)
                        ).all()
            except Exception as e:
                logger.warning(f"获取Tushare数据失败: {e}")
        
        # 如果数据库还是没有数据，尝试直接从Tushare获取最新数据
        if not db_indices:
            logger.info("数据库无数据，直接从Tushare获取最新指数数据")
            try:
                indices_df = await tushare_service.get_market_indices()
                if not indices_df.empty:
                    result = []
                    # 确保每个指数只返回一条记录
                    seen_symbols = set()
                    for _, row in indices_df.iterrows():
                        symbol = row.get('ts_code', '')
                        if symbol not in seen_symbols:
                            seen_symbols.add(symbol)
                            result.append(MarketIndexResponse(
                                symbol=symbol,
                                name=row.get('index_name', _get_index_name(symbol)),
                                price=row.get('close', 0),
                                change=row.get('change', 0),
                                changePercent=row.get('pct_chg', 0),
                                volume=int(row.get('vol', 0)),
                                amount=row.get('amount', 0),
                                tradeDate=row.get('trade_date', '')
                            ))
                    return result
            except Exception as e:
                logger.error(f"直接从Tushare获取数据失败: {e}")
        
        # 转换为响应模型，确保没有重复
        result = []
        seen_symbols = set()
        for index in db_indices:
            if index.symbol not in seen_symbols:
                seen_symbols.add(index.symbol)
                result.append(MarketIndexResponse(
                    symbol=index.symbol,
                    name=index.name or _get_index_name(index.symbol),
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
                    # 获取股票名称
                    stock_name = row.get('name', '')
                    if not stock_name or stock_name == row.get('code', ''):
                        # 从数据库获取股票名称
                        stock_info = db.query(Stock).filter(Stock.symbol == row.get('code', '')).first()
                        if stock_info:
                            stock_name = stock_info.name
                    
                    result.append(StockQuoteResponse(
                        symbol=row.get('code', ''),
                        name=stock_name or row.get('code', ''),
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
                # 获取股票名称
                stock_info = db.query(Stock).filter(Stock.symbol == symbol).first()
                stock_name = stock_info.name if stock_info else symbol
                
                result.append(StockQuoteResponse(
                    symbol=latest_data.symbol,
                    name=stock_name,
                    price=latest_data.close or 0,
                    change=latest_data.change or 0,
                    changePercent=latest_data.pct_chg or 0,
                    volume=int(latest_data.vol or 0),
                    amount=latest_data.amount or 0
                ))
            else:
                # 尝试从Tushare获取该股票的最新数据
                try:
                    daily_df = await tushare_service.get_stock_daily(symbol, limit=1)
                    if not daily_df.empty:
                        row = daily_df.iloc[0]
                        
                        # 获取股票名称
                        stock_info = db.query(Stock).filter(Stock.symbol == symbol).first()
                        stock_name = stock_info.name if stock_info else symbol
                        
                        result.append(StockQuoteResponse(
                            symbol=row.get('ts_code', symbol),
                            name=stock_name,
                            price=row.get('close', 0),
                            change=row.get('change', 0),
                            changePercent=row.get('pct_chg', 0),
                            volume=int(row.get('vol', 0)),
                            amount=row.get('amount', 0)
                        ))
                    else:
                        logger.warning(f"无法获取股票{symbol}的数据")
                        continue
                except Exception as e:
                    logger.warning(f"获取股票{symbol}数据失败: {e}")
                    continue
        
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
    获取股票或指数历史数据
    
    Args:
        symbol: 股票代码或指数代码
        days: 获取天数，默认30天
        db: 数据库会话
    
    Returns:
        历史数据
    """
    try:
        # 判断是否为指数
        is_index = symbol.endswith('.SH') and symbol.startswith('000') or symbol.endswith('.SZ') and symbol.startswith('399')
        
        if is_index:
            # 查询指数历史数据
            history_data = db.query(MarketIndex).filter(
                MarketIndex.symbol == symbol
            ).order_by(MarketIndex.trade_date.desc()).limit(days).all()
            
            # 如果数据不足，尝试从Tushare获取
            if len(history_data) < min(days, 10):
                try:
                    end_date = datetime.now().strftime('%Y%m%d')
                    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
                    
                    # 使用新的指数历史数据方法
                    indices_df = await tushare_service.get_index_history(symbol, start_date, end_date, days)
                    if not indices_df.empty:
                        # 保存到数据库
                        for _, row in indices_df.iterrows():
                            index_record = MarketIndex(
                                symbol=row.get('ts_code', ''),
                                name=row.get('index_name', _get_index_name(row.get('ts_code', ''))),
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
                            db.merge(index_record)
                        
                        db.commit()
                        # 重新查询
                        history_data = db.query(MarketIndex).filter(
                            MarketIndex.symbol == symbol
                        ).order_by(MarketIndex.trade_date.desc()).limit(days).all()
                        
                except Exception as e:
                    logger.warning(f"获取{symbol}指数历史数据失败: {e}")
        else:
            # 查询股票历史数据
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
        
        # 如果数据库没有数据，尝试直接从Tushare获取
        if not result["data"]:
            logger.info(f"数据库无{symbol}历史数据，直接从Tushare获取")
            try:
                if is_index:
                    # 获取指数历史数据
                    end_date = datetime.now().strftime('%Y%m%d')
                    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
                    
                    indices_df = await tushare_service.get_index_history(symbol, start_date, end_date, days)
                    if not indices_df.empty:
                        for _, row in indices_df.iterrows():
                            result["data"].append({
                                "date": row.get('trade_date', ''),
                                "open": row.get('open'),
                                "high": row.get('high'),
                                "low": row.get('low'),
                                "close": row.get('close'),
                                "volume": row.get('vol'),
                                "amount": row.get('amount')
                            })
                else:
                    # 获取股票数据
                    end_date = datetime.now().strftime('%Y%m%d')
                    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
                    
                    daily_df = await tushare_service.get_stock_daily(
                        symbol, start_date, end_date
                    )
                    
                    if not daily_df.empty:
                        for _, row in daily_df.iterrows():
                            result["data"].append({
                                "date": row.get('trade_date', ''),
                                "open": row.get('open'),
                                "high": row.get('high'),
                                "low": row.get('low'),
                                "close": row.get('close'),
                                "volume": row.get('vol'),
                                "amount": row.get('amount')
                            })
                    else:
                        logger.warning(f"Tushare也无法获取{symbol}的历史数据")
            except Exception as e:
                logger.error(f"直接从Tushare获取{symbol}历史数据失败: {e}")
        
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


