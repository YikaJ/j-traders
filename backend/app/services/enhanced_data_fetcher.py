"""
增强的数据获取器
支持频率限制、动态数据获取、缓存优化和并发控制
"""

import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import numpy as np
from collections import defaultdict

from app.services.tushare_service import tushare_service
from app.services.factor_data_analyzer import factor_data_analyzer, TushareInterface
from app.services.cache_service import cache_service
from app.schemas.strategy_execution import (
    ExecutionLog, LogLevel, DataFetchSummary, FactorDataRequest
)

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """频率限制配置"""
    max_calls_per_minute: int = 10      # 每分钟最大调用次数
    max_calls_per_hour: int = 200       # 每小时最大调用次数
    max_calls_per_day: int = 1000       # 每天最大调用次数
    concurrent_limit: int = 3           # 并发限制
    retry_delay: float = 1.0            # 重试延迟（秒）
    max_retries: int = 3                # 最大重试次数


@dataclass
class FetchResult:
    """数据获取结果"""
    interface: str
    stock_codes: List[str]
    data: pd.DataFrame
    success: bool
    error_message: Optional[str] = None
    fetch_time: float = 0.0
    cache_hit: bool = False


class RateLimiter:
    """API频率限制器"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.call_history = []
        self.concurrent_calls = 0
        self.lock = asyncio.Lock()
    
    async def acquire(self) -> bool:
        """获取调用许可"""
        async with self.lock:
            now = time.time()
            
            # 清理过期的调用记录
            minute_ago = now - 60
            hour_ago = now - 3600
            day_ago = now - 86400
            
            self.call_history = [t for t in self.call_history if t > day_ago]
            
            # 检查各级别限制
            minute_calls = len([t for t in self.call_history if t > minute_ago])
            hour_calls = len([t for t in self.call_history if t > hour_ago])
            day_calls = len(self.call_history)
            
            if (minute_calls >= self.config.max_calls_per_minute or
                hour_calls >= self.config.max_calls_per_hour or
                day_calls >= self.config.max_calls_per_day or
                self.concurrent_calls >= self.config.concurrent_limit):
                return False
            
            # 记录调用时间
            self.call_history.append(now)
            self.concurrent_calls += 1
            return True
    
    async def release(self):
        """释放调用许可"""
        async with self.lock:
            self.concurrent_calls = max(0, self.concurrent_calls - 1)
    
    async def wait_for_permit(self):
        """等待获取调用许可"""
        max_wait_time = 60  # 最大等待60秒
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            if await self.acquire():
                return True
            await asyncio.sleep(1)
        
        return False


class EnhancedDataFetcher:
    """增强的数据获取器"""
    
    def __init__(self, rate_limit_config: Optional[RateLimitConfig] = None):
        self.rate_limiter = RateLimiter(rate_limit_config or RateLimitConfig())
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.cache = cache_service
        self.interface_methods = self._init_interface_methods()
    
    def _init_interface_methods(self) -> Dict[str, callable]:
        """初始化接口方法映射"""
        return {
            TushareInterface.DAILY.value: self._fetch_daily_data,
            TushareInterface.DAILY_BASIC.value: self._fetch_daily_basic_data,
            TushareInterface.INCOME.value: self._fetch_income_data,
            TushareInterface.BALANCESHEET.value: self._fetch_balance_data,
            TushareInterface.CASHFLOW.value: self._fetch_cashflow_data,
            TushareInterface.FIN_INDICATOR.value: self._fetch_financial_indicator_data,
        }
    
    async def fetch_strategy_data(
        self,
        strategy: Any,
        stock_codes: List[str],
        execution_date: str,
        logger_instance: Any
    ) -> Tuple[pd.DataFrame, DataFetchSummary]:
        """
        根据策略需求智能获取数据
        
        Args:
            strategy: 策略对象
            stock_codes: 股票代码列表
            execution_date: 执行日期
            logger_instance: 日志记录器
            
        Returns:
            (合并后的数据, 获取摘要)
        """
        start_time = time.time()
        total_stocks = len(stock_codes)
        
        logger_instance.log(
            LogLevel.INFO, "data_fetching",
            f"开始智能数据获取，股票数量: {total_stocks}"
        )
        
        # 分析所有因子的数据需求
        required_interfaces = self._analyze_strategy_requirements(strategy, logger_instance)
        
        # 分批获取数据
        batch_size = 100  # 每批处理100只股票
        all_results = []
        fetch_summary = DataFetchSummary(
            total_stocks=total_stocks,
            fetched_stocks=0,
            failed_stocks=0,
            cache_hits=0,
            api_calls=0,
            data_size_mb=0.0,
            fetch_time=0.0
        )
        
        # 分批处理股票
        for i in range(0, len(stock_codes), batch_size):
            batch_codes = stock_codes[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(stock_codes) + batch_size - 1) // batch_size
            
            logger_instance.log(
                LogLevel.INFO, "data_fetching",
                f"处理批次 {batch_num}/{total_batches}，股票数量: {len(batch_codes)}"
            )
            
            # 并发获取不同接口的数据
            batch_results = await self._fetch_batch_data(
                required_interfaces,
                batch_codes,
                execution_date,
                logger_instance
            )
            
            all_results.extend(batch_results)
            
            # 更新进度
            progress = min(100, (i + len(batch_codes)) / len(stock_codes) * 100)
            logger_instance.log(
                LogLevel.INFO, "data_fetching",
                f"数据获取进度: {progress:.1f}%",
                progress=progress
            )
        
        # 合并数据
        merged_data = self._merge_data_results(all_results, logger_instance)
        
        # 计算摘要统计
        fetch_summary.fetch_time = time.time() - start_time
        fetch_summary.fetched_stocks = len(merged_data) if not merged_data.empty else 0
        fetch_summary.failed_stocks = total_stocks - fetch_summary.fetched_stocks
        
        # 统计缓存命中和API调用
        for result in all_results:
            if result.cache_hit:
                fetch_summary.cache_hits += 1
            else:
                fetch_summary.api_calls += 1
        
        # 估算数据大小
        if not merged_data.empty:
            fetch_summary.data_size_mb = merged_data.memory_usage(deep=True).sum() / 1024 / 1024
        
        logger_instance.log(
            LogLevel.INFO, "data_fetching",
            f"数据获取完成，成功: {fetch_summary.fetched_stocks}只，"
            f"失败: {fetch_summary.failed_stocks}只，"
            f"缓存命中: {fetch_summary.cache_hits}次，"
            f"API调用: {fetch_summary.api_calls}次，"
            f"耗时: {fetch_summary.fetch_time:.2f}秒"
        )
        
        return merged_data, fetch_summary
    
    def _analyze_strategy_requirements(self, strategy: Any, logger_instance: Any) -> Dict[str, List[str]]:
        """分析策略的数据需求"""
        all_requirements = {}
        
        for factor_config in strategy.factors:
            if not factor_config.is_enabled:
                continue
            
            # 获取因子代码
            factor_code = getattr(factor_config, 'factor_code', '') or getattr(factor_config, 'formula', '')
            
            if factor_code:
                # 分析因子需求
                requirements = factor_data_analyzer.analyze_factor_code(factor_code)
                
                # 合并需求
                for interface, fields in requirements.items():
                    if interface not in all_requirements:
                        all_requirements[interface] = set(['ts_code', 'trade_date'])
                    all_requirements[interface].update(fields)
                
                logger_instance.log(
                    LogLevel.DEBUG, "data_fetching",
                    f"因子 {factor_config.factor_id} 需求分析: {requirements}"
                )
        
        # 转换为列表格式
        final_requirements = {k: list(v) for k, v in all_requirements.items()}
        
        logger_instance.log(
            LogLevel.INFO, "data_fetching",
            f"策略数据需求分析完成: {final_requirements}"
        )
        
        return final_requirements
    
    async def _fetch_batch_data(
        self,
        required_interfaces: Dict[str, List[str]],
        stock_codes: List[str],
        execution_date: str,
        logger_instance: Any
    ) -> List[FetchResult]:
        """并发获取批次数据"""
        tasks = []
        
        for interface, fields in required_interfaces.items():
            if interface in self.interface_methods:
                task = self._fetch_interface_data_with_limit(
                    interface, fields, stock_codes, execution_date, logger_instance
                )
                tasks.append(task)
        
        # 并发执行所有接口调用
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                logger_instance.log(
                    LogLevel.ERROR, "data_fetching",
                    f"接口调用异常: {result}"
                )
            elif isinstance(result, FetchResult):
                valid_results.append(result)
        
        return valid_results
    
    async def _fetch_interface_data_with_limit(
        self,
        interface: str,
        fields: List[str],
        stock_codes: List[str],
        execution_date: str,
        logger_instance: Any
    ) -> FetchResult:
        """带频率限制的接口数据获取"""
        # 检查缓存
        cache_key = f"interface_data_{interface}_{execution_date}_{hash(tuple(sorted(stock_codes)))}"
        cached_data = await self.cache.get(cache_key)
        
        if cached_data is not None:
            logger_instance.log(
                LogLevel.DEBUG, "data_fetching",
                f"缓存命中: {interface}"
            )
            return FetchResult(
                interface=interface,
                stock_codes=stock_codes,
                data=cached_data,
                success=True,
                cache_hit=True
            )
        
        # 等待API调用许可
        if not await self.rate_limiter.wait_for_permit():
            return FetchResult(
                interface=interface,
                stock_codes=stock_codes,
                data=pd.DataFrame(),
                success=False,
                error_message="API频率限制，无法获取许可"
            )
        
        try:
            start_time = time.time()
            
            # 调用具体的接口方法
            fetch_method = self.interface_methods.get(interface)
            if not fetch_method:
                raise ValueError(f"不支持的接口: {interface}")
            
            data = await fetch_method(fields, stock_codes, execution_date)
            fetch_time = time.time() - start_time
            
            # 缓存结果
            if not data.empty:
                await self.cache.set(cache_key, data, expire=3600)  # 缓存1小时
            
            logger_instance.log(
                LogLevel.DEBUG, "data_fetching",
                f"接口 {interface} 获取成功，数据量: {len(data)}条，耗时: {fetch_time:.2f}秒"
            )
            
            return FetchResult(
                interface=interface,
                stock_codes=stock_codes,
                data=data,
                success=True,
                fetch_time=fetch_time
            )
        
        except Exception as e:
            logger_instance.log(
                LogLevel.ERROR, "data_fetching",
                f"接口 {interface} 获取失败: {e}"
            )
            return FetchResult(
                interface=interface,
                stock_codes=stock_codes,
                data=pd.DataFrame(),
                success=False,
                error_message=str(e)
            )
        
        finally:
            await self.rate_limiter.release()
    
    async def _fetch_daily_data(self, fields: List[str], stock_codes: List[str], trade_date: str) -> pd.DataFrame:
        """获取日线数据"""
        def _fetch():
            all_data = []
            for code in stock_codes:
                try:
                    data = tushare_service.pro.daily(
                        ts_code=code,
                        trade_date=trade_date.replace('-', ''),
                        fields=','.join(fields)
                    )
                    if not data.empty:
                        all_data.append(data)
                except Exception as e:
                    logger.warning(f"获取股票 {code} 日线数据失败: {e}")
            
            if all_data:
                return pd.concat(all_data, ignore_index=True)
            return pd.DataFrame()
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _fetch)
    
    async def _fetch_daily_basic_data(self, fields: List[str], stock_codes: List[str], trade_date: str) -> pd.DataFrame:
        """获取每日基本面数据"""
        def _fetch():
            try:
                data = tushare_service.pro.daily_basic(
                    trade_date=trade_date.replace('-', ''),
                    fields=','.join(fields)
                )
                # 筛选指定股票
                if not data.empty and 'ts_code' in data.columns:
                    data = data[data['ts_code'].isin(stock_codes)]
                return data
            except Exception as e:
                logger.warning(f"获取每日基本面数据失败: {e}")
                return pd.DataFrame()
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _fetch)
    
    async def _fetch_income_data(self, fields: List[str], stock_codes: List[str], trade_date: str) -> pd.DataFrame:
        """获取利润表数据"""
        def _fetch():
            all_data = []
            # 获取最近的报告期
            report_period = self._get_latest_report_period(trade_date)
            
            for code in stock_codes:
                try:
                    data = tushare_service.pro.income(
                        ts_code=code,
                        period=report_period,
                        fields=','.join(fields)
                    )
                    if not data.empty:
                        all_data.append(data)
                except Exception as e:
                    logger.warning(f"获取股票 {code} 利润表数据失败: {e}")
            
            if all_data:
                return pd.concat(all_data, ignore_index=True)
            return pd.DataFrame()
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _fetch)
    
    async def _fetch_balance_data(self, fields: List[str], stock_codes: List[str], trade_date: str) -> pd.DataFrame:
        """获取资产负债表数据"""
        def _fetch():
            all_data = []
            report_period = self._get_latest_report_period(trade_date)
            
            for code in stock_codes:
                try:
                    data = tushare_service.pro.balancesheet(
                        ts_code=code,
                        period=report_period,
                        fields=','.join(fields)
                    )
                    if not data.empty:
                        all_data.append(data)
                except Exception as e:
                    logger.warning(f"获取股票 {code} 资产负债表数据失败: {e}")
            
            if all_data:
                return pd.concat(all_data, ignore_index=True)
            return pd.DataFrame()
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _fetch)
    
    async def _fetch_cashflow_data(self, fields: List[str], stock_codes: List[str], trade_date: str) -> pd.DataFrame:
        """获取现金流量表数据"""
        def _fetch():
            all_data = []
            report_period = self._get_latest_report_period(trade_date)
            
            for code in stock_codes:
                try:
                    data = tushare_service.pro.cashflow(
                        ts_code=code,
                        period=report_period,
                        fields=','.join(fields)
                    )
                    if not data.empty:
                        all_data.append(data)
                except Exception as e:
                    logger.warning(f"获取股票 {code} 现金流量表数据失败: {e}")
            
            if all_data:
                return pd.concat(all_data, ignore_index=True)
            return pd.DataFrame()
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _fetch)
    
    async def _fetch_financial_indicator_data(self, fields: List[str], stock_codes: List[str], trade_date: str) -> pd.DataFrame:
        """获取财务指标数据"""
        def _fetch():
            all_data = []
            report_period = self._get_latest_report_period(trade_date)
            
            for code in stock_codes:
                try:
                    data = tushare_service.pro.fina_indicator(
                        ts_code=code,
                        period=report_period,
                        fields=','.join(fields)
                    )
                    if not data.empty:
                        all_data.append(data)
                except Exception as e:
                    logger.warning(f"获取股票 {code} 财务指标数据失败: {e}")
            
            if all_data:
                return pd.concat(all_data, ignore_index=True)
            return pd.DataFrame()
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _fetch)
    
    def _get_latest_report_period(self, trade_date: str) -> str:
        """获取最近的财报期"""
        date_obj = datetime.strptime(trade_date, '%Y-%m-%d')
        year = date_obj.year
        month = date_obj.month
        
        if month >= 10:
            return f"{year}0930"  # Q3
        elif month >= 7:
            return f"{year}0630"  # Q2
        elif month >= 4:
            return f"{year}0331"  # Q1
        else:
            return f"{year-1}1231"  # 上年Q4
    
    def _merge_data_results(self, results: List[FetchResult], logger_instance: Any) -> pd.DataFrame:
        """合并不同接口的数据结果"""
        if not results:
            return pd.DataFrame()
        
        # 找到主要数据表（通常是daily数据）
        main_data = None
        other_data = []
        
        for result in results:
            if not result.success or result.data.empty:
                continue
            
            if result.interface == TushareInterface.DAILY.value:
                main_data = result.data.copy()
            else:
                other_data.append((result.interface, result.data))
        
        if main_data is None:
            # 如果没有日线数据，尝试使用其他数据作为主表
            for result in results:
                if result.success and not result.data.empty:
                    main_data = result.data.copy()
                    break
        
        if main_data is None:
            return pd.DataFrame()
        
        # 合并其他数据
        merged_data = main_data
        for interface_name, data in other_data:
            try:
                # 基于ts_code合并数据
                if 'ts_code' in data.columns and 'ts_code' in merged_data.columns:
                    merged_data = merged_data.merge(
                        data, on='ts_code', how='left', suffixes=('', f'_{interface_name}')
                    )
                    logger_instance.log(
                        LogLevel.DEBUG, "data_fetching",
                        f"合并 {interface_name} 数据，数据量: {len(data)}"
                    )
            except Exception as e:
                logger_instance.log(
                    LogLevel.WARNING, "data_fetching",
                    f"合并 {interface_name} 数据失败: {e}"
                )
        
        logger_instance.log(
            LogLevel.INFO, "data_fetching",
            f"数据合并完成，最终数据量: {len(merged_data)} 行，{len(merged_data.columns)} 列"
        )
        
        return merged_data


# 全局实例
enhanced_data_fetcher = EnhancedDataFetcher()