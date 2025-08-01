"""
Tushare数据服务
集成Tushare API获取股票数据
"""

import tushare as ts
import pandas as pd
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.core.config import settings

logger = logging.getLogger(__name__)


class TushareService:
    """Tushare数据服务类"""
    
    def __init__(self):
        self.token = settings.TUSHARE_TOKEN
        self.pro = None
        self.executor = ThreadPoolExecutor(max_workers=5)
        self._init_api()
    
    def _init_api(self):
        """初始化Tushare API"""
        if not self.token:
            logger.warning("Tushare token未配置，将使用免费接口")
            return
        
        try:
            ts.set_token(self.token)
            self.pro = ts.pro_api()
            logger.info("Tushare API初始化成功")
        except Exception as e:
            logger.error(f"Tushare API初始化失败: {e}")
            raise
    
    async def get_stock_list(self, exchange: Optional[str] = None) -> pd.DataFrame:
        """
        获取股票列表
        
        Args:
            exchange: 交易所代码 SSE-上交所 SZSE-深交所
        
        Returns:
            股票基础信息DataFrame
        """
        def _fetch():
            try:
                if self.pro:
                    # 使用pro接口
                    df = self.pro.stock_basic(
                        exchange=exchange,
                        list_status='L',  # 上市状态
                        fields='ts_code,symbol,name,area,industry,market,list_date'
                    )
                else:
                    # 使用免费接口
                    df = ts.get_stock_basics()
                    df.reset_index(inplace=True)
                    df.rename(columns={'code': 'symbol'}, inplace=True)
                
                logger.info(f"获取股票列表成功，共{len(df)}只股票")
                return df
            except Exception as e:
                logger.error(f"获取股票列表失败: {e}")
                return pd.DataFrame()
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _fetch)
    
    async def get_stock_daily(
        self, 
        symbol: str, 
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 5000
    ) -> pd.DataFrame:
        """
        获取股票日线数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期 YYYYMMDD
            end_date: 结束日期 YYYYMMDD
            limit: 数据条数限制
        
        Returns:
            股票日线数据DataFrame
        """
        def _fetch():
            try:
                if self.pro:
                    # 使用pro接口
                    df = self.pro.daily(
                        ts_code=symbol,
                        start_date=start_date,
                        end_date=end_date,
                        limit=limit
                    )
                    
                    # 获取基本指标
                    basic_df = self.pro.daily_basic(
                        ts_code=symbol,
                        start_date=start_date,
                        end_date=end_date,
                        limit=limit,
                        fields='ts_code,trade_date,turnover_rate,turnover_rate_f,volume_ratio,pe,pe_ttm,pb,ps,ps_ttm,dv_ratio,dv_ttm,total_share,float_share,free_share,total_mv,circ_mv'
                    )
                    
                    # 合并数据
                    if not basic_df.empty:
                        df = df.merge(basic_df, on=['ts_code', 'trade_date'], how='left')
                else:
                    # 使用免费接口
                    df = ts.get_hist_data(symbol, start=start_date, end=end_date)
                    if df is not None:
                        df.reset_index(inplace=True)
                        df.rename(columns={'date': 'trade_date'}, inplace=True)
                
                logger.info(f"获取{symbol}日线数据成功，共{len(df)}条")
                return df
            except Exception as e:
                logger.error(f"获取{symbol}日线数据失败: {e}")
                return pd.DataFrame()
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _fetch)
    
    async def get_market_indices(self, trade_date: Optional[str] = None) -> pd.DataFrame:
        """
        获取市场指数数据
        
        Args:
            trade_date: 交易日期 YYYYMMDD
        
        Returns:
            市场指数数据DataFrame
        """
        def _fetch():
            try:
                # 主要指数代码，只返回主要的指数
                indices = [
                    '000001.SH',  # 上证指数
                    '399001.SZ',  # 深证成指
                    '399006.SZ',  # 创业板指
                    '000300.SH',  # 沪深300
                    '000905.SH',  # 中证500 (只保留一个)
                ]
                
                all_data = []
                for index_code in indices:
                    try:
                        if self.pro:
                            # 获取指数日线数据
                            df = self.pro.index_daily(
                                ts_code=index_code,
                                trade_date=trade_date,
                                limit=1
                            )
                            
                            # 如果没有指定日期，获取最新数据
                            if df.empty and not trade_date:
                                df = self.pro.index_daily(
                                    ts_code=index_code,
                                    limit=1
                                )
                        else:
                            # 免费接口处理
                            df = pd.DataFrame()  # 免费接口限制较多
                        
                        if not df.empty:
                            # 添加指数名称
                            df['index_name'] = self._get_index_name(index_code)
                            all_data.append(df)
                        
                        # API限制，添加延时
                        time.sleep(0.1)
                    except Exception as e:
                        logger.warning(f"获取指数{index_code}数据失败: {e}")
                        continue
                
                if all_data:
                    result_df = pd.concat(all_data, ignore_index=True)
                    logger.info(f"获取市场指数数据成功，共{len(result_df)}条")
                    return result_df
                else:
                    return pd.DataFrame()
            except Exception as e:
                logger.error(f"获取市场指数数据失败: {e}")
                return pd.DataFrame()
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _fetch)
    
    async def get_index_history(self, symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None, limit: int = 30) -> pd.DataFrame:
        """
        获取指数历史数据
        
        Args:
            symbol: 指数代码
            start_date: 开始日期 YYYYMMDD
            end_date: 结束日期 YYYYMMDD
            limit: 数据条数限制
        
        Returns:
            指数历史数据DataFrame
        """
        def _fetch():
            try:
                if self.pro:
                    # 使用pro接口获取指数历史数据
                    df = self.pro.index_daily(
                        ts_code=symbol,
                        start_date=start_date,
                        end_date=end_date,
                        limit=limit
                    )
                    
                    if not df.empty:
                        # 添加指数名称
                        df['index_name'] = self._get_index_name(symbol)
                        logger.info(f"获取{symbol}历史数据成功，共{len(df)}条")
                        return df
                    else:
                        logger.warning(f"未获取到{symbol}的历史数据")
                        return pd.DataFrame()
                else:
                    # 免费接口限制较多
                    logger.warning("免费接口不支持指数历史数据获取")
                    return pd.DataFrame()
            except Exception as e:
                logger.error(f"获取{symbol}历史数据失败: {e}")
                return pd.DataFrame()
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _fetch)
    
    async def get_realtime_quotes(self, symbols: List[str]) -> pd.DataFrame:
        """
        获取实时行情数据
        
        Args:
            symbols: 股票代码列表
        
        Returns:
            实时行情DataFrame
        """
        def _fetch():
            try:
                if not symbols:
                    return pd.DataFrame()
                
                # 将symbols转换为tushare格式
                ts_codes = []
                for symbol in symbols:
                    if '.' not in symbol:
                        # 如果没有后缀，根据代码判断
                        if symbol.startswith('6'):
                            ts_codes.append(f"{symbol}.SH")
                        else:
                            ts_codes.append(f"{symbol}.SZ")
                    else:
                        ts_codes.append(symbol)
                
                if self.pro:
                    # 批量获取实时数据
                    df = self.pro.realtime_quote(ts_code=','.join(ts_codes))
                    
                    # 如果实时数据获取失败，尝试获取最新日线数据
                    if df.empty:
                        logger.warning("实时数据获取失败，尝试获取最新日线数据")
                        all_data = []
                        for ts_code in ts_codes:
                            try:
                                daily_df = self.pro.daily(ts_code=ts_code, limit=1)
                                if not daily_df.empty:
                                    # 转换为实时数据格式
                                    daily_df['code'] = daily_df['ts_code']
                                    daily_df['name'] = daily_df['ts_code']  # 需要从股票基础信息获取
                                    daily_df['price'] = daily_df['close']
                                    daily_df['change'] = daily_df['change']
                                    daily_df['changepercent'] = daily_df['pct_chg']
                                    daily_df['volume'] = daily_df['vol']
                                    daily_df['amount'] = daily_df['amount']
                                    all_data.append(daily_df)
                                
                                time.sleep(0.1)
                            except Exception as e:
                                logger.warning(f"获取{ts_code}数据失败: {e}")
                                continue
                        
                        if all_data:
                            df = pd.concat(all_data, ignore_index=True)
                else:
                    # 使用免费接口
                    df = ts.get_realtime_quotes(ts_codes)
                
                logger.info(f"获取实时行情成功，共{len(df)}只股票")
                return df
            except Exception as e:
                logger.error(f"获取实时行情失败: {e}")
                return pd.DataFrame()
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _fetch)
    
    async def search_stocks(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        搜索股票
        
        Args:
            keyword: 搜索关键词（股票代码或名称）
            limit: 返回结果数量限制
        
        Returns:
            股票搜索结果列表
        """
        try:
            # 获取股票列表
            stock_df = await self.get_stock_list()
            if stock_df.empty:
                return []
            
            # 搜索匹配
            mask = (
                stock_df['ts_code'].str.contains(keyword, case=False, na=False) |
                stock_df['name'].str.contains(keyword, case=False, na=False)
            )
            
            result_df = stock_df[mask].head(limit)
            
            # 转换为字典列表
            results = []
            for _, row in result_df.iterrows():
                results.append({
                    'symbol': row.get('ts_code', ''),
                    'name': row.get('name', ''),
                    'industry': row.get('industry', ''),
                    'area': row.get('area', ''),
                    'market': row.get('market', ''),
                    'list_date': row.get('list_date', '')
                })
            
            logger.info(f"股票搜索'{keyword}'成功，返回{len(results)}个结果")
            return results
        except Exception as e:
            logger.error(f"股票搜索失败: {e}")
            return []
    
    async def get_trade_calendar(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取交易日历
        
        Args:
            start_date: 开始日期 YYYYMMDD
            end_date: 结束日期 YYYYMMDD
        
        Returns:
            交易日历DataFrame
        """
        def _fetch():
            try:
                if self.pro:
                    df = self.pro.trade_cal(
                        start_date=start_date,
                        end_date=end_date,
                        exchange='SSE'  # 上交所日历
                    )
                else:
                    # 免费接口没有交易日历，返回空DataFrame
                    df = pd.DataFrame()
                
                logger.info(f"获取交易日历成功，{start_date}到{end_date}")
                return df
            except Exception as e:
                logger.error(f"获取交易日历失败: {e}")
                return pd.DataFrame()
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _fetch)
    
    def _get_index_name(self, symbol: str) -> str:
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
    
    def is_trade_day(self, date: str) -> bool:
        """
        判断是否为交易日
        
        Args:
            date: 日期字符串 YYYYMMDD
        
        Returns:
            是否为交易日
        """
        try:
            # 简单判断：周一到周五且不是节假日
            # 这里可以结合交易日历做更精确的判断
            dt = datetime.strptime(date, '%Y%m%d')
            weekday = dt.weekday()
            return weekday < 5  # 0-4 表示周一到周五
        except Exception:
            return False


# 创建全局实例
tushare_service = TushareService()