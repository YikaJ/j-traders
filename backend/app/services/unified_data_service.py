"""
统一数据源管理服务
支持内存、数据库、API三种数据源的统一访问
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from enum import Enum
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.services.tushare_service import TushareService
from app.db.models.stock import Stock, StockDaily, MarketIndex
from app.core.config import settings

logger = logging.getLogger(__name__)


class DataSourceType(Enum):
    """数据源类型"""
    MEMORY = "memory"
    DATABASE = "database"
    API = "api"


class DataType(Enum):
    """数据类型"""
    STOCK_BASIC = "stock_basic"
    STOCK_DAILY = "stock_daily"
    MARKET_INDEX = "market_index"
    FINANCIAL_DATA = "financial_data"


class CacheStrategy(Enum):
    """缓存策略"""
    NO_CACHE = "no_cache"           # 不缓存，直接从API获取
    CACHE_FIRST = "cache_first"      # 优先使用缓存
    API_FIRST = "api_first"          # 优先使用API
    SMART_CACHE = "smart_cache"      # 智能缓存策略


class UnifiedDataService:
    """统一数据源管理服务"""
    
    def __init__(self):
        self.tushare_service = TushareService()
        self.memory_cache = {}  # 内存缓存
        self.cache_ttl = {}     # 缓存过期时间
        
    async def get_data(
        self,
        data_type: DataType,
        symbols: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        cache_strategy: CacheStrategy = CacheStrategy.SMART_CACHE,
        db: Optional[Session] = None
    ) -> pd.DataFrame:
        """
        统一数据获取接口
        
        Args:
            data_type: 数据类型
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            cache_strategy: 缓存策略
            db: 数据库会话
            
        Returns:
            数据DataFrame
        """
        try:
            if cache_strategy == CacheStrategy.NO_CACHE:
                return await self._fetch_from_api(data_type, symbols, start_date, end_date)
            
            elif cache_strategy == CacheStrategy.CACHE_FIRST:
                return await self._get_cache_first(data_type, symbols, start_date, end_date, db)
            
            elif cache_strategy == CacheStrategy.API_FIRST:
                return await self._get_api_first(data_type, symbols, start_date, end_date, db)
            
            elif cache_strategy == CacheStrategy.SMART_CACHE:
                return await self._get_smart_cache(data_type, symbols, start_date, end_date, db)
            
        except Exception as e:
            logger.error(f"获取数据失败: {e}")
            return pd.DataFrame()
    
    async def _get_smart_cache(
        self,
        data_type: DataType,
        symbols: Optional[List[str]],
        start_date: Optional[str],
        end_date: Optional[str],
        db: Session
    ) -> pd.DataFrame:
        """智能缓存策略"""
        
        # 1. 检查内存缓存
        memory_data = self._get_from_memory_cache(data_type, symbols, start_date, end_date)
        if not memory_data.empty:
            logger.debug(f"从内存缓存获取{data_type.value}数据")
            return memory_data
        
        # 2. 检查数据库缓存
        db_data = await self._get_from_database(data_type, symbols, start_date, end_date, db)
        if not db_data.empty:
            # 更新内存缓存
            self._update_memory_cache(data_type, db_data, symbols, start_date, end_date)
            logger.debug(f"从数据库缓存获取{data_type.value}数据")
            return db_data
        
        # 3. 从API获取
        api_data = await self._fetch_from_api(data_type, symbols, start_date, end_date)
        if not api_data.empty:
            # 保存到数据库和内存
            await self._save_to_database(data_type, api_data, db)
            self._update_memory_cache(data_type, api_data, symbols, start_date, end_date)
            logger.debug(f"从API获取{data_type.value}数据")
            return api_data
        
        return pd.DataFrame()
    
    async def _get_cache_first(
        self,
        data_type: DataType,
        symbols: Optional[List[str]],
        start_date: Optional[str],
        end_date: Optional[str],
        db: Session
    ) -> pd.DataFrame:
        """缓存优先策略"""
        
        # 1. 检查内存缓存
        memory_data = self._get_from_memory_cache(data_type, symbols, start_date, end_date)
        if not memory_data.empty:
            return memory_data
        
        # 2. 检查数据库缓存
        db_data = await self._get_from_database(data_type, symbols, start_date, end_date, db)
        if not db_data.empty:
            self._update_memory_cache(data_type, db_data, symbols, start_date, end_date)
            return db_data
        
        # 3. 从API获取
        api_data = await self._fetch_from_api(data_type, symbols, start_date, end_date)
        if not api_data.empty:
            await self._save_to_database(data_type, api_data, db)
            self._update_memory_cache(data_type, api_data, symbols, start_date, end_date)
            return api_data
        
        return pd.DataFrame()
    
    async def _get_api_first(
        self,
        data_type: DataType,
        symbols: Optional[List[str]],
        start_date: Optional[str],
        end_date: Optional[str],
        db: Session
    ) -> pd.DataFrame:
        """API优先策略"""
        
        # 1. 从API获取
        api_data = await self._fetch_from_api(data_type, symbols, start_date, end_date)
        if not api_data.empty:
            await self._save_to_database(data_type, api_data, db)
            self._update_memory_cache(data_type, api_data, symbols, start_date, end_date)
            return api_data
        
        # 2. 检查缓存作为备选
        memory_data = self._get_from_memory_cache(data_type, symbols, start_date, end_date)
        if not memory_data.empty:
            return memory_data
        
        db_data = await self._get_from_database(data_type, symbols, start_date, end_date, db)
        if not db_data.empty:
            self._update_memory_cache(data_type, db_data, symbols, start_date, end_date)
            return db_data
        
        return pd.DataFrame()
    
    def _get_from_memory_cache(
        self,
        data_type: DataType,
        symbols: Optional[List[str]],
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> pd.DataFrame:
        """从内存缓存获取数据"""
        cache_key = self._generate_cache_key(data_type, symbols, start_date, end_date)
        
        if cache_key in self.memory_cache:
            cache_data = self.memory_cache[cache_key]
            cache_time = self.cache_ttl.get(cache_key)
            
            # 检查缓存是否过期（5分钟）
            if cache_time and (datetime.now() - cache_time).seconds < 300:
                return cache_data
        
        return pd.DataFrame()
    
    async def _get_from_database(
        self,
        data_type: DataType,
        symbols: Optional[List[str]],
        start_date: Optional[str],
        end_date: Optional[str],
        db: Session
    ) -> pd.DataFrame:
        """从数据库获取数据"""
        try:
            if data_type == DataType.STOCK_BASIC:
                return await self._get_stock_basic_from_db(symbols, db)
            elif data_type == DataType.STOCK_DAILY:
                return await self._get_stock_daily_from_db(symbols, start_date, end_date, db)
            elif data_type == DataType.MARKET_INDEX:
                return await self._get_market_index_from_db(symbols, start_date, end_date, db)
            else:
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"从数据库获取{data_type.value}数据失败: {e}")
            return pd.DataFrame()
    
    async def _fetch_from_api(
        self,
        data_type: DataType,
        symbols: Optional[List[str]],
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> pd.DataFrame:
        """从API获取数据"""
        try:
            if data_type == DataType.STOCK_BASIC:
                return await self.tushare_service.get_stock_list()
            elif data_type == DataType.STOCK_DAILY:
                if symbols:
                    all_data = []
                    for symbol in symbols:
                        data = await self.tushare_service.get_stock_daily(symbol, start_date, end_date)
                        if not data.empty:
                            all_data.append(data)
                    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()
                return pd.DataFrame()
            elif data_type == DataType.MARKET_INDEX:
                # 获取主要指数数据
                indices = ['000001.SH', '399001.SZ', '399006.SZ']  # 上证、深证、创业板
                all_data = []
                for index in indices:
                    data = await self.tushare_service.get_stock_daily(index, start_date, end_date)
                    if not data.empty:
                        all_data.append(data)
                return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()
            else:
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"从API获取{data_type.value}数据失败: {e}")
            return pd.DataFrame()
    
    async def _save_to_database(
        self,
        data_type: DataType,
        data: pd.DataFrame,
        db: Session
    ) -> None:
        """保存数据到数据库"""
        try:
            if data_type == DataType.STOCK_BASIC:
                await self._save_stock_basic_to_db(data, db)
            elif data_type == DataType.STOCK_DAILY:
                await self._save_stock_daily_to_db(data, db)
            elif data_type == DataType.MARKET_INDEX:
                await self._save_market_index_to_db(data, db)
        except Exception as e:
            logger.error(f"保存{data_type.value}数据到数据库失败: {e}")
    
    def _update_memory_cache(
        self,
        data_type: DataType,
        data: pd.DataFrame,
        symbols: Optional[List[str]],
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> None:
        """更新内存缓存"""
        cache_key = self._generate_cache_key(data_type, symbols, start_date, end_date)
        self.memory_cache[cache_key] = data
        self.cache_ttl[cache_key] = datetime.now()
    
    def _generate_cache_key(
        self,
        data_type: DataType,
        symbols: Optional[List[str]],
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> str:
        """生成缓存键"""
        symbols_str = "_".join(symbols) if symbols else "all"
        return f"{data_type.value}_{symbols_str}_{start_date}_{end_date}"
    
    # 数据库操作方法
    async def _get_stock_basic_from_db(self, symbols: Optional[List[str]], db: Session) -> pd.DataFrame:
        """从数据库获取股票基础信息"""
        query = db.query(Stock)
        if symbols:
            query = query.filter(Stock.symbol.in_(symbols))
        
        stocks = query.all()
        if not stocks:
            return pd.DataFrame()
        
        data = []
        for stock in stocks:
            data.append({
                'ts_code': stock.symbol,
                'symbol': stock.symbol,
                'name': stock.name,
                'area': stock.area,
                'industry': stock.industry,
                'market': stock.market,
                'list_date': stock.list_date,
                'list_status': stock.list_status,
                'total_share': stock.total_share,
                'float_share': stock.float_share
            })
        
        return pd.DataFrame(data)
    
    async def _get_stock_daily_from_db(
        self,
        symbols: Optional[List[str]],
        start_date: Optional[str],
        end_date: Optional[str],
        db: Session
    ) -> pd.DataFrame:
        """从数据库获取股票日线数据"""
        query = db.query(StockDaily)
        
        if symbols:
            query = query.filter(StockDaily.symbol.in_(symbols))
        if start_date:
            query = query.filter(StockDaily.trade_date >= start_date)
        if end_date:
            query = query.filter(StockDaily.trade_date <= end_date)
        
        daily_data = query.order_by(StockDaily.trade_date).all()
        if not daily_data:
            return pd.DataFrame()
        
        data = []
        for record in daily_data:
            data.append({
                'ts_code': record.symbol,
                'trade_date': record.trade_date,
                'open': record.open,
                'high': record.high,
                'low': record.low,
                'close': record.close,
                'pre_close': record.pre_close,
                'change': record.change,
                'pct_chg': record.pct_chg,
                'vol': record.vol,
                'amount': record.amount,
                'turnover_rate': record.turnover_rate,
                'turnover_rate_f': record.turnover_rate_f,
                'volume_ratio': record.volume_ratio,
                'pe': record.pe,
                'pe_ttm': record.pe_ttm,
                'pb': record.pb,
                'ps': record.ps,
                'ps_ttm': record.ps_ttm,
                'dv_ratio': record.dv_ratio,
                'dv_ttm': record.dv_ttm,
                'total_share': record.total_share,
                'float_share': record.float_share,
                'free_share': record.free_share,
                'total_mv': record.total_mv,
                'circ_mv': record.circ_mv
            })
        
        return pd.DataFrame(data)
    
    async def _get_market_index_from_db(
        self,
        symbols: Optional[List[str]],
        start_date: Optional[str],
        end_date: Optional[str],
        db: Session
    ) -> pd.DataFrame:
        """从数据库获取市场指数数据"""
        query = db.query(MarketIndex)
        
        if symbols:
            query = query.filter(MarketIndex.symbol.in_(symbols))
        if start_date:
            query = query.filter(MarketIndex.trade_date >= start_date)
        if end_date:
            query = query.filter(MarketIndex.trade_date <= end_date)
        
        index_data = query.order_by(MarketIndex.trade_date).all()
        if not index_data:
            return pd.DataFrame()
        
        data = []
        for record in index_data:
            data.append({
                'ts_code': record.symbol,
                'trade_date': record.trade_date,
                'open': record.open,
                'high': record.high,
                'low': record.low,
                'close': record.close,
                'pre_close': record.pre_close,
                'change': record.change,
                'pct_chg': record.pct_chg,
                'vol': record.vol,
                'amount': record.amount
            })
        
        return pd.DataFrame(data)
    
    async def _save_stock_basic_to_db(self, data: pd.DataFrame, db: Session) -> None:
        """保存股票基础信息到数据库"""
        for _, row in data.iterrows():
            stock = Stock(
                symbol=row.get('ts_code', ''),
                name=row.get('name', ''),
                industry=row.get('industry', ''),
                area=row.get('area', ''),
                market=row.get('market', ''),
                list_date=row.get('list_date', ''),
                list_status=row.get('list_status', 'L'),
                total_share=row.get('total_share'),
                float_share=row.get('float_share')
            )
            db.merge(stock)
        db.commit()
    
    async def _save_stock_daily_to_db(self, data: pd.DataFrame, db: Session) -> None:
        """保存股票日线数据到数据库"""
        for _, row in data.iterrows():
            daily = StockDaily(
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
                amount=row.get('amount'),
                turnover_rate=row.get('turnover_rate'),
                turnover_rate_f=row.get('turnover_rate_f'),
                volume_ratio=row.get('volume_ratio'),
                pe=row.get('pe'),
                pe_ttm=row.get('pe_ttm'),
                pb=row.get('pb'),
                ps=row.get('ps'),
                ps_ttm=row.get('ps_ttm'),
                dv_ratio=row.get('dv_ratio'),
                dv_ttm=row.get('dv_ttm'),
                total_share=row.get('total_share'),
                float_share=row.get('float_share'),
                free_share=row.get('free_share'),
                total_mv=row.get('total_mv'),
                circ_mv=row.get('circ_mv')
            )
            db.merge(daily)
        db.commit()
    
    async def _save_market_index_to_db(self, data: pd.DataFrame, db: Session) -> None:
        """保存市场指数数据到数据库"""
        for _, row in data.iterrows():
            index = MarketIndex(
                symbol=row.get('ts_code', ''),
                name=row.get('name', ''),
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
            db.merge(index)
        db.commit()
    

    
    def clear_memory_cache(self, data_type: Optional[DataType] = None) -> None:
        """清理内存缓存"""
        if data_type:
            keys_to_remove = [k for k in self.memory_cache.keys() if k.startswith(data_type.value)]
            for key in keys_to_remove:
                del self.memory_cache[key]
                del self.cache_ttl[key]
        else:
            self.memory_cache.clear()
            self.cache_ttl.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return {
            "memory_cache_size": len(self.memory_cache),
            "cache_keys": list(self.memory_cache.keys()),
            "cache_ttl_size": len(self.cache_ttl)
        }


# 全局实例
unified_data_service = UnifiedDataService() 