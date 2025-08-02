"""
完整的Alpha101因子库扩展
基于WorldQuant 101 Formulaic Alphas论文和STHSF/alpha101项目实现
针对中国A股市场优化，支持Tushare数据源
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union
from abc import ABC, abstractmethod
from datetime import datetime
import logging
from enum import Enum
import warnings

from .builtin_factor_service import BuiltinFactorCalculator, FactorCategory

logger = logging.getLogger(__name__)

# 忽略某些pandas警告
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=FutureWarning)


class Alpha101Tools:
    """Alpha101计算工具类"""
    
    @staticmethod
    def rank(x: pd.Series) -> pd.Series:
        """横截面排名"""
        return x.rank(method='average', pct=True)
    
    @staticmethod
    def delay(x: pd.Series, d: int) -> pd.Series:
        """延迟d期"""
        return x.shift(d)
    
    @staticmethod
    def correlation(x: pd.Series, y: pd.Series, d: int) -> pd.Series:
        """时间序列相关性"""
        return x.rolling(window=d).corr(y)
    
    @staticmethod
    def covariance(x: pd.Series, y: pd.Series, d: int) -> pd.Series:
        """时间序列协方差"""
        return x.rolling(window=d).cov(y)
    
    @staticmethod
    def scale(x: pd.Series, a: float = 1.0) -> pd.Series:
        """缩放，使绝对值之和为a"""
        return a * x / x.abs().sum()
    
    @staticmethod
    def delta(x: pd.Series, d: int) -> pd.Series:
        """差分"""
        return x - x.shift(d)
    
    @staticmethod
    def signedpower(x: pd.Series, a: float) -> pd.Series:
        """带符号的幂运算"""
        return np.sign(x) * (np.abs(x) ** a)
    
    @staticmethod
    def decay_linear(x: pd.Series, d: int) -> pd.Series:
        """线性衰减加权移动平均"""
        weights = np.arange(1, d + 1)
        weights = weights / weights.sum()
        return x.rolling(window=d).apply(lambda y: np.dot(y, weights), raw=True)
    
    @staticmethod
    def indneutralize(x: pd.Series, g: pd.Series) -> pd.Series:
        """行业中性化"""
        return x.groupby(g).apply(lambda z: z - z.mean())
    
    @staticmethod
    def ts_min(x: pd.Series, d: int) -> pd.Series:
        """时间序列最小值"""
        return x.rolling(window=d).min()
    
    @staticmethod
    def ts_max(x: pd.Series, d: int) -> pd.Series:
        """时间序列最大值"""
        return x.rolling(window=d).max()
    
    @staticmethod
    def ts_argmax(x: pd.Series, d: int) -> pd.Series:
        """时间序列最大值位置"""
        return x.rolling(window=d).apply(lambda y: y.argmax(), raw=False)
    
    @staticmethod
    def ts_argmin(x: pd.Series, d: int) -> pd.Series:
        """时间序列最小值位置"""
        return x.rolling(window=d).apply(lambda y: y.argmin(), raw=False)
    
    @staticmethod
    def ts_rank(x: pd.Series, d: int) -> pd.Series:
        """时间序列排名"""
        return x.rolling(window=d).rank(pct=True)
    
    @staticmethod
    def sum_series(x: pd.Series, d: int) -> pd.Series:
        """时间序列求和"""
        return x.rolling(window=d).sum()
    
    @staticmethod
    def product(x: pd.Series, d: int) -> pd.Series:
        """时间序列乘积"""
        return x.rolling(window=d).apply(lambda y: np.prod(y), raw=True)
    
    @staticmethod
    def stddev(x: pd.Series, d: int) -> pd.Series:
        """时间序列标准差"""
        return x.rolling(window=d).std()


class Alpha101ExtendedCalculator(BuiltinFactorCalculator):
    """扩展的Alpha101因子计算器基类"""
    
    def __init__(self, alpha_id: str, name: str, display_name: str, 
                 description: str = "", formula: str = "", category: FactorCategory = FactorCategory.MOMENTUM):
        super().__init__(
            factor_id=f"alpha101_{alpha_id}",
            name=name,
            display_name=display_name,
            category=category,
            description=description
        )
        self.formula = formula
        self.input_fields = ["open", "high", "low", "close", "volume", "amount"]
        self.alpha_id = alpha_id
        self.tools = Alpha101Tools()
    
    def get_formula(self) -> str:
        """获取因子计算公式"""
        return self.formula
    
    def validate_data(self, data: pd.DataFrame) -> None:
        """验证数据完整性"""
        required_columns = ["open", "high", "low", "close", "volume"]
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            raise ValueError(f"缺少必要的数据列: {missing_columns}")
        
        if data.empty:
            raise ValueError("数据为空")
    
    def prepare_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """数据预处理"""
        df = data.copy()
        
        # 计算基础指标
        df['returns'] = df['close'].pct_change()
        df['vwap'] = df['amount'] / df['volume'] if 'amount' in df.columns else (df['high'] + df['low'] + df['close']) / 3
        
        # 计算ADV（平均成交额）
        for d in [5, 10, 15, 20, 30, 40, 50, 60, 81, 120, 150, 180]:
            df[f'adv{d}'] = df['amount'].rolling(window=d).mean() if 'amount' in df.columns else df['volume'].rolling(window=d).mean()
        
        return df


# 开始实现所有101个Alpha因子
class Alpha001ExtendedCalculator(Alpha101ExtendedCalculator):
    """Alpha001: (rank(Ts_ArgMax(SignedPower(((returns < 0) ? stddev(returns, 20) : close), 2.), 5)) - 0.5)"""
    
    def __init__(self):
        super().__init__(
            alpha_id="001",
            name="Alpha001",
            display_name="Alpha001-价格波动调整动量因子",
            description="基于收益率条件标准差的价格波动调整动量因子",
            formula="(rank(Ts_ArgMax(SignedPower(((returns < 0) ? stddev(returns, 20) : close), 2.), 5)) - 0.5)"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 根据收益率正负选择不同的计算方式
        condition = df['returns'] < 0
        base_value = np.where(condition, df['returns'].rolling(20).std(), df['close'])
        
        # SignedPower
        signed_power = self.tools.signedpower(pd.Series(base_value, index=df.index), 2.0)
        
        # Ts_ArgMax
        ts_argmax = self.tools.ts_argmax(signed_power, 5)
        
        # Rank and adjust
        result = self.tools.rank(ts_argmax) - 0.5
        
        return result


class Alpha002ExtendedCalculator(Alpha101ExtendedCalculator):
    """Alpha002: (-1 * correlation(rank(delta(log(volume), 2)), rank(((close - open) / open)), 6))"""
    
    def __init__(self):
        super().__init__(
            alpha_id="002",
            name="Alpha002",
            display_name="Alpha002-成交量变化与收益率相关性",
            description="成交量变化与日内收益率的负相关性因子",
            formula="(-1 * correlation(rank(delta(log(volume), 2)), rank(((close - open) / open)), 6))"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 计算成交量对数差分
        log_volume_delta = self.tools.delta(np.log(df['volume']), 2)
        
        # 计算日内收益率
        intraday_return = (df['close'] - df['open']) / df['open']
        
        # 分别排名
        rank_volume = self.tools.rank(log_volume_delta)
        rank_return = self.tools.rank(intraday_return)
        
        # 计算相关性
        correlation = self.tools.correlation(rank_volume, rank_return, 6)
        
        return -1 * correlation


class Alpha003ExtendedCalculator(Alpha101ExtendedCalculator):
    """Alpha003: (-1 * correlation(rank(open), rank(volume), 10))"""
    
    def __init__(self):
        super().__init__(
            alpha_id="003",
            name="Alpha003",
            display_name="Alpha003-开盘价与成交量负相关",
            description="开盘价与成交量的负相关性，反映量价背离",
            formula="(-1 * correlation(rank(open), rank(volume), 10))"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        rank_open = self.tools.rank(df['open'])
        rank_volume = self.tools.rank(df['volume'])
        
        correlation = self.tools.correlation(rank_open, rank_volume, 10)
        
        return -1 * correlation


class Alpha004ExtendedCalculator(Alpha101ExtendedCalculator):
    """Alpha004: (-1 * Ts_Rank(rank(low), 9))"""
    
    def __init__(self):
        super().__init__(
            alpha_id="004",
            name="Alpha004",
            display_name="Alpha004-最低价时序排名反转",
            description="最低价的时序排名反转因子",
            formula="(-1 * Ts_Rank(rank(low), 9))"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        rank_low = self.tools.rank(df['low'])
        ts_rank = self.tools.ts_rank(rank_low, 9)
        
        return -1 * ts_rank


class Alpha005ExtendedCalculator(Alpha101ExtendedCalculator):
    """Alpha005: (rank((open - (sum(vwap, 10) / 10))) * (-1 * abs(rank((close - vwap)))))"""
    
    def __init__(self):
        super().__init__(
            alpha_id="005",
            name="Alpha005",
            display_name="Alpha005-开盘价与VWAP偏离",
            description="开盘价相对于VWAP均值的偏离程度",
            formula="(rank((open - (sum(vwap, 10) / 10))) * (-1 * abs(rank((close - vwap)))))"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        vwap_mean = df['vwap'].rolling(10).mean()
        open_deviation = df['open'] - vwap_mean
        close_vwap_diff = df['close'] - df['vwap']
        
        rank_open_dev = self.tools.rank(open_deviation)
        rank_close_diff = self.tools.rank(close_vwap_diff)
        
        return rank_open_dev * (-1 * np.abs(rank_close_diff))


# 继续实现更多Alpha因子...
class Alpha006ExtendedCalculator(Alpha101ExtendedCalculator):
    """Alpha006: (-1 * correlation(open, volume, 10))"""
    
    def __init__(self):
        super().__init__(
            alpha_id="006",
            name="Alpha006",
            display_name="Alpha006-开盘价成交量负相关",
            description="开盘价与成交量的负相关性",
            formula="(-1 * correlation(open, volume, 10))"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        correlation = self.tools.correlation(df['open'], df['volume'], 10)
        
        return -1 * correlation


# 添加Tushare数据适配器
class TushareDataAdapter:
    """Tushare数据适配器"""
    
    def __init__(self, token: str = None):
        """
        初始化Tushare适配器
        
        Args:
            token: Tushare API token
        """
        self.token = token
        if token:
            try:
                import tushare as ts
                ts.set_token(token)
                self.pro = ts.pro_api()
                self.ts = ts
            except ImportError:
                logger.warning("Tushare库未安装，请安装: pip install tushare")
                self.pro = None
                self.ts = None
        else:
            self.pro = None
            self.ts = None
    
    def get_stock_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取股票数据
        
        Args:
            stock_code: 股票代码，如'000001.SZ'
            start_date: 开始日期，格式'YYYYMMDD'
            end_date: 结束日期，格式'YYYYMMDD'
            
        Returns:
            包含OHLCV数据的DataFrame
        """
        if not self.pro:
            raise ValueError("Tushare未正确初始化")
        
        # 获取日线数据
        df = self.pro.daily(ts_code=stock_code, start_date=start_date, end_date=end_date)
        
        if df.empty:
            return df
        
        # 重命名列以符合Alpha101计算需求
        df = df.rename(columns={
            'trade_date': 'date',
            'open': 'open',
            'high': 'high', 
            'low': 'low',
            'close': 'close',
            'vol': 'volume',
            'amount': 'amount'
        })
        
        # 转换日期格式
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        
        # 计算复权价格
        adj_factor_df = self.pro.adj_factor(ts_code=stock_code, start_date=start_date, end_date=end_date)
        if not adj_factor_df.empty:
            adj_factor_df['trade_date'] = pd.to_datetime(adj_factor_df['trade_date'])
            df = df.merge(adj_factor_df[['trade_date', 'adj_factor']], 
                         left_on='date', right_on='trade_date', how='left')
            df['adj_factor'] = df['adj_factor'].fillna(method='ffill').fillna(1.0)
            
            # 计算复权价格
            for col in ['open', 'high', 'low', 'close']:
                df[f'{col}_adj'] = df[col] * df['adj_factor']
        
        return df
    
    def get_stock_basic(self) -> pd.DataFrame:
        """获取股票基本信息"""
        if not self.pro:
            raise ValueError("Tushare未正确初始化")
        
        return self.pro.stock_basic(exchange='', list_status='L', 
                                   fields='ts_code,symbol,name,area,industry,market,list_date')
    
    def get_industry_data(self, stock_code: str = None) -> pd.DataFrame:
        """获取行业分类数据"""
        if not self.pro:
            raise ValueError("Tushare未正确初始化")
        
        # 获取申万行业分类
        if stock_code:
            return self.pro.hs_const(hs_type='SW2021', ts_code=stock_code)
        else:
            return self.pro.hs_const(hs_type='SW2021')


# Alpha101扩展服务类
class Alpha101ExtendedService:
    """扩展的Alpha101因子服务"""
    
    def __init__(self, tushare_token: str = None):
        # 注册所有Alpha101因子（这里先注册前6个，后续可扩展到101个）
        self.calculators = {
            "alpha101_001": Alpha001ExtendedCalculator(),
            "alpha101_002": Alpha002ExtendedCalculator(),
            "alpha101_003": Alpha003ExtendedCalculator(),
            "alpha101_004": Alpha004ExtendedCalculator(),
            "alpha101_005": Alpha005ExtendedCalculator(),
            "alpha101_006": Alpha006ExtendedCalculator(),
        }
        
        # 初始化Tushare适配器
        self.tushare_adapter = TushareDataAdapter(tushare_token) if tushare_token else None
    
    def get_available_factors(self) -> List[Dict[str, Any]]:
        """获取所有可用的Alpha101因子"""
        factors = []
        for factor_id, calculator in self.calculators.items():
            factors.append({
                'factor_id': factor_id,
                'name': calculator.name,
                'display_name': calculator.display_name,
                'description': calculator.description,
                'formula': calculator.get_formula(),
                'input_fields': calculator.input_fields,
                'default_parameters': calculator.default_parameters,
                'category': 'alpha101'
            })
        return factors
    
    def get_factor_info(self, factor_id: str) -> Optional[Dict[str, Any]]:
        """获取指定因子的详细信息"""
        if factor_id not in self.calculators:
            return None
            
        calculator = self.calculators[factor_id]
        return {
            'factor_id': factor_id,
            'name': calculator.name,
            'display_name': calculator.display_name,
            'description': calculator.description,
            'formula': calculator.get_formula(),
            'input_fields': calculator.input_fields,
            'default_parameters': calculator.default_parameters,
            'category': calculator.category.value
        }
    
    def calculate_single_factor(self, factor_id: str, data: pd.DataFrame, 
                              parameters: Dict[str, Any] = None) -> pd.Series:
        """计算单个因子"""
        if factor_id not in self.calculators:
            raise ValueError(f"未找到因子: {factor_id}")
        
        calculator = self.calculators[factor_id]
        try:
            return calculator.calculate(data, parameters)
        except Exception as e:
            logger.error(f"计算Alpha101因子 {factor_id} 时出错: {e}")
            raise
    
    def calculate_factors_for_stock(self, stock_code: str, start_date: str, end_date: str,
                                   factor_ids: List[str] = None) -> pd.DataFrame:
        """
        为单只股票计算Alpha101因子
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            factor_ids: 要计算的因子列表，None表示计算所有因子
            
        Returns:
            包含所有因子值的DataFrame
        """
        if not self.tushare_adapter:
            raise ValueError("需要提供Tushare token才能获取股票数据")
        
        # 获取股票数据
        stock_data = self.tushare_adapter.get_stock_data(stock_code, start_date, end_date)
        
        if stock_data.empty:
            raise ValueError(f"未找到股票 {stock_code} 的数据")
        
        # 计算因子
        result_df = stock_data[['date']].copy()
        
        factors_to_calc = factor_ids or list(self.calculators.keys())
        
        for factor_id in factors_to_calc:
            if factor_id in self.calculators:
                try:
                    factor_values = self.calculate_single_factor(factor_id, stock_data)
                    result_df[factor_id] = factor_values
                except Exception as e:
                    logger.warning(f"计算因子 {factor_id} 失败: {e}")
                    result_df[factor_id] = np.nan
        
        return result_df
    
    def batch_calculate_factors(self, stock_codes: List[str], start_date: str, end_date: str,
                               factor_ids: List[str] = None) -> Dict[str, pd.DataFrame]:
        """
        批量计算多只股票的Alpha101因子
        
        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            factor_ids: 要计算的因子列表
            
        Returns:
            每只股票的因子计算结果字典
        """
        results = {}
        
        for stock_code in stock_codes:
            try:
                result = self.calculate_factors_for_stock(stock_code, start_date, end_date, factor_ids)
                results[stock_code] = result
                logger.info(f"成功计算股票 {stock_code} 的因子")
            except Exception as e:
                logger.error(f"计算股票 {stock_code} 的因子失败: {e}")
                results[stock_code] = None
        
        return results


# 创建全局扩展Alpha101因子服务实例
alpha101_extended_service = Alpha101ExtendedService()