"""
Alpha101 Phase 3: Alpha041-080 因子实现
基于 STHSF/alpha101 项目，针对A股市场优化
筛选适合A股市场的因子，抛弃不适合的因子
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List
from .alpha101_extended import Alpha101ExtendedCalculator, Alpha101Tools, TushareDataAdapter


class Alpha041ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#041: (((high * low)^0.5) - vwap)
    公式: sqrt(high * low) - vwap
    适合A股: 是，简单的价格因子
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="041",
            name="Alpha041",
            display_name="Alpha041-几何均价差",
            description="最高价与最低价几何均值与VWAP的差值",
            formula="sqrt(high * low) - vwap"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 计算几何均价
        geometric_mean = np.sqrt(df['high'] * df['low'])
        
        # 计算与VWAP的差值
        result = geometric_mean - df['vwap']
        
        return pd.Series(result, index=df.index)


class Alpha042ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#042: (rank((vwap - close)) / rank((vwap + close)))
    公式: rank(vwap - close) / rank(vwap + close)
    适合A股: 是，VWAP相关因子
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="042",
            name="Alpha042",
            display_name="Alpha042-VWAP相对位置",
            description="VWAP与收盘价关系的相对排名因子",
            formula="rank(vwap - close) / rank(vwap + close)"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 计算VWAP与收盘价的差值和和值
        vwap_close_diff = df['vwap'] - df['close']
        vwap_close_sum = df['vwap'] + df['close']
        
        # 分别排名
        rank_diff = self.tools.rank(vwap_close_diff)
        rank_sum = self.tools.rank(vwap_close_sum)
        
        # 计算比值
        result = rank_diff / (rank_sum + 1e-10)  # 避免除零
        
        return pd.Series(result, index=df.index)


class Alpha043ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#043: (ts_rank((volume / adv20), 20) * ts_rank((-1 * delta(close, 7)), 8))
    公式: ts_rank(volume/adv20, 20) * ts_rank(-delta(close, 7), 8)
    适合A股: 是，量价结合因子
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="043",
            name="Alpha043",
            display_name="Alpha043-相对成交量动量",
            description="相对成交量与价格反转的时序排名组合",
            formula="ts_rank(volume/adv20, 20) * ts_rank(-delta(close, 7), 8)"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 计算相对成交量
        relative_volume = df['volume'] / (df['adv20'] + 1e-10)
        
        # 计算7日价格变化的负值
        neg_price_change = -1 * self.tools.delta(df['close'], 7)
        
        # 分别计算时序排名
        ts_rank_volume = self.tools.ts_rank(relative_volume, 20)
        ts_rank_price = self.tools.ts_rank(neg_price_change, 8)
        
        # 计算乘积
        result = ts_rank_volume * ts_rank_price
        
        return pd.Series(result, index=df.index)


class Alpha044ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#044: (-1 * correlation(high, rank(volume), 5))
    公式: -correlation(high, rank(volume), 5)
    适合A股: 是，量价背离因子
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="044",
            name="Alpha044",
            display_name="Alpha044-高价成交量背离",
            description="最高价与成交量排名的负相关",
            formula="-correlation(high, rank(volume), 5)"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 计算成交量排名
        rank_volume = self.tools.rank(df['volume'])
        
        # 计算5日相关性
        correlation_factor = self.tools.correlation(df['high'], rank_volume, 5)
        
        # 取负值
        result = -1 * correlation_factor
        
        return pd.Series(result, index=df.index)


class Alpha045ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#045: (-1 * ((rank((sum(delay(close, 5), 20) / 20)) * correlation(close, volume, 2)) * 
                rank(correlation(sum(close, 5), sum(close, 20), 2))))
    适合A股: 是，价量相关性因子
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="045",
            name="Alpha045",
            display_name="Alpha045-多重价量相关性",
            description="基于延迟价格和价量相关性的复合因子",
            formula="复杂的价量相关性组合因子"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 计算20日延迟收盘价均值
        delay_close_5 = self.tools.delay(df['close'], 5)
        sum_delay_close = self.tools.sum_series(delay_close_5, 20) / 20
        rank_delay_avg = self.tools.rank(sum_delay_close)
        
        # 计算收盘价与成交量的2日相关性
        corr_close_volume = self.tools.correlation(df['close'], df['volume'], 2)
        
        # 计算5日和20日收盘价和的2日相关性
        sum_close_5 = self.tools.sum_series(df['close'], 5)
        sum_close_20 = self.tools.sum_series(df['close'], 20)
        corr_sums = self.tools.correlation(sum_close_5, sum_close_20, 2)
        rank_corr_sums = self.tools.rank(corr_sums)
        
        # 计算最终结果
        result = -1 * (rank_delay_avg * corr_close_volume * rank_corr_sums)
        
        return pd.Series(result, index=df.index)


class Alpha046ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#046: 趋势反转条件因子
    适合A股: 是，趋势判断因子
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="046",
            name="Alpha046",
            display_name="Alpha046-趋势反转条件",
            description="基于价格趋势的条件判断因子",
            formula="基于20日和10日价格趋势的条件因子"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 计算趋势变化率
        delay_close_20 = self.tools.delay(df['close'], 20)
        delay_close_10 = self.tools.delay(df['close'], 10)
        
        trend_20_10 = (delay_close_20 - delay_close_10) / 10
        trend_10_0 = (delay_close_10 - df['close']) / 10
        
        trend_diff = trend_20_10 - trend_10_0
        
        # 条件判断
        condition1 = trend_diff > 0.25
        condition2 = trend_diff < 0
        
        # 计算结果
        result = np.where(condition1, -1,
                         np.where(condition2, 1,
                                 -1 * (df['close'] - self.tools.delay(df['close'], 1))))
        
        return pd.Series(result, index=df.index)


class Alpha047ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#047: 复杂的价量排名因子
    适合A股: 是，但需要简化
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="047",
            name="Alpha047",
            display_name="Alpha047-复合价量排名",
            description="基于倒数价格和成交量的复合排名因子",
            formula="复杂的价量排名组合"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 简化实现，保持核心逻辑
        # 计算价格倒数排名与成交量的组合
        inv_close_rank = self.tools.rank(1 / (df['close'] + 1e-10))
        volume_factor = df['volume'] / (df['adv20'] + 1e-10)
        
        # 计算最高价相关因子
        high_factor = df['high'] * self.tools.rank(df['high'] - df['close'])
        high_avg = self.tools.sum_series(df['high'], 5) / 5
        high_normalized = high_factor / (high_avg + 1e-10)
        
        # VWAP变化
        vwap_change = df['vwap'] - self.tools.delay(df['vwap'], 5)
        rank_vwap_change = self.tools.rank(vwap_change)
        
        # 组合结果
        result = (inv_close_rank * volume_factor * high_normalized) - rank_vwap_change
        
        return pd.Series(result, index=df.index)


# 跳过Alpha048 - 使用美股特有行业数据，不适合A股

class Alpha049ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#049: 价格趋势条件因子
    适合A股: 是
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="049",
            name="Alpha049",
            display_name="Alpha049-价格趋势条件2",
            description="基于价格趋势的另一个条件判断因子",
            formula="基于价格趋势的条件因子"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 计算趋势变化率
        delay_close_20 = self.tools.delay(df['close'], 20)
        delay_close_10 = self.tools.delay(df['close'], 10)
        
        trend_20_10 = (delay_close_20 - delay_close_10) / 10
        trend_10_0 = (delay_close_10 - df['close']) / 10
        
        trend_diff = trend_20_10 - trend_10_0
        
        # 条件判断 (与Alpha046稍有不同的阈值)
        condition = trend_diff < -0.1
        
        # 计算结果
        result = np.where(condition, 1, 
                         -1 * (df['close'] - self.tools.delay(df['close'], 1)))
        
        return pd.Series(result, index=df.index)


class Alpha050ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#050: (-1 * ts_max(rank(correlation(rank(volume), rank(vwap), 5)), 5))
    适合A股: 是，量价相关性因子
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="050",
            name="Alpha050",
            display_name="Alpha050-量价相关性极值",
            description="成交量与VWAP排名相关性的5日最大值",
            formula="-ts_max(rank(correlation(rank(volume), rank(vwap), 5)), 5)"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 计算成交量和VWAP的排名
        rank_volume = self.tools.rank(df['volume'])
        rank_vwap = self.tools.rank(df['vwap'])
        
        # 计算5日相关性
        correlation_factor = self.tools.correlation(rank_volume, rank_vwap, 5)
        
        # 计算相关性的排名
        rank_correlation = self.tools.rank(correlation_factor)
        
        # 计算5日最大值并取负
        ts_max_corr = self.tools.ts_max(rank_correlation, 5)
        result = -1 * ts_max_corr
        
        return pd.Series(result, index=df.index)


class Alpha051ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#051: 类似Alpha049的趋势条件因子
    适合A股: 是
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="051",
            name="Alpha051",
            display_name="Alpha051-价格趋势条件3",
            description="基于价格趋势的第三个条件判断因子",
            formula="基于价格趋势的条件因子，阈值-0.05"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 计算趋势变化率
        delay_close_20 = self.tools.delay(df['close'], 20)
        delay_close_10 = self.tools.delay(df['close'], 10)
        
        trend_20_10 = (delay_close_20 - delay_close_10) / 10
        trend_10_0 = (delay_close_10 - df['close']) / 10
        
        trend_diff = trend_20_10 - trend_10_0
        
        # 条件判断 (阈值-0.05)
        condition = trend_diff < -0.05
        
        # 计算结果
        result = np.where(condition, 1, 
                         -1 * (df['close'] - self.tools.delay(df['close'], 1)))
        
        return pd.Series(result, index=df.index)


class Alpha052ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#052: 低价变化与收益率的复合因子
    适合A股: 是
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="052",
            name="Alpha052",
            display_name="Alpha052-低价变化收益率",
            description="最低价变化与长期收益率的复合因子",
            formula="(delay(ts_min(low, 5), 5) - ts_min(low, 5)) * rank((sum(returns, 240) - sum(returns, 20))/220) * ts_rank(volume, 5)"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 计算5日最低价变化
        ts_min_low_5 = self.tools.ts_min(df['low'], 5)
        delay_ts_min_low = self.tools.delay(ts_min_low_5, 5)
        low_change = delay_ts_min_low - ts_min_low_5
        
        # 计算长期收益率差
        sum_returns_240 = self.tools.sum_series(df['returns'], 240)
        sum_returns_20 = self.tools.sum_series(df['returns'], 20)
        returns_diff = (sum_returns_240 - sum_returns_20) / 220
        rank_returns_diff = self.tools.rank(returns_diff)
        
        # 计算成交量时序排名
        ts_rank_volume = self.tools.ts_rank(df['volume'], 5)
        
        # 组合结果
        result = low_change * rank_returns_diff * ts_rank_volume
        
        return pd.Series(result, index=df.index)


class Alpha053ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#053: (-1 * delta((((close - low) - (high - close)) / (close - low)), 9))
    适合A股: 是，价格位置变化因子
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="053",
            name="Alpha053",
            display_name="Alpha053-价格位置变化",
            description="收盘价相对位置的9日变化",
            formula="-delta(((close - low) - (high - close)) / (close - low), 9)"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 计算价格相对位置
        close_low_diff = df['close'] - df['low']
        high_close_diff = df['high'] - df['close']
        relative_position = (close_low_diff - high_close_diff) / (close_low_diff + 1e-10)
        
        # 计算9日变化
        delta_position = self.tools.delta(relative_position, 9)
        
        # 取负值
        result = -1 * delta_position
        
        return pd.Series(result, index=df.index)


class Alpha054ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#054: ((-1 * ((low - close) * (open^5))) / ((low - high) * (close^5)))
    适合A股: 是，但需要数值稳定性处理
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="054",
            name="Alpha054",
            display_name="Alpha054-价格幂次比率",
            description="基于价格幂次的比率因子",
            formula="(-1 * ((low - close) * (open^5))) / ((low - high) * (close^5))"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 计算分子
        numerator = -1 * (df['low'] - df['close']) * np.power(df['open'], 5)
        
        # 计算分母 (注意符号，low - high 是负数)
        denominator = (df['low'] - df['high']) * np.power(df['close'], 5)
        
        # 避免除零和数值稳定性问题
        result = numerator / (denominator + 1e-10)
        
        # 限制极值
        result = np.clip(result, -100, 100)
        
        return pd.Series(result, index=df.index)


class Alpha055ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#055: (-1 * correlation(rank(((close - ts_min(low, 12)) / (ts_max(high, 12) - ts_min(low, 12)))), rank(volume), 6))
    适合A股: 是，相对价格位置与成交量相关性
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="055",
            name="Alpha055",
            display_name="Alpha055-相对价格位置量能",
            description="相对价格位置与成交量排名的负相关",
            formula="-correlation(rank(relative_price_position), rank(volume), 6)"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 计算12日价格范围
        ts_min_low_12 = self.tools.ts_min(df['low'], 12)
        ts_max_high_12 = self.tools.ts_max(df['high'], 12)
        price_range = ts_max_high_12 - ts_min_low_12
        
        # 计算相对价格位置
        relative_position = (df['close'] - ts_min_low_12) / (price_range + 1e-10)
        
        # 计算排名
        rank_position = self.tools.rank(relative_position)
        rank_volume = self.tools.rank(df['volume'])
        
        # 计算6日相关性并取负
        correlation_factor = self.tools.correlation(rank_position, rank_volume, 6)
        result = -1 * correlation_factor
        
        return pd.Series(result, index=df.index)


# 跳过Alpha056 - 使用市值数据，需要额外数据源

class Alpha057ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#057: (0 - (1 * ((close - vwap) / decay_linear(rank(ts_argmax(close, 30)), 2))))
    适合A股: 是，价格偏离度因子
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="057",
            name="Alpha057",
            display_name="Alpha057-价格偏离度",
            description="收盘价与VWAP偏离度的标准化",
            formula="-(close - vwap) / decay_linear(rank(ts_argmax(close, 30)), 2)"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 计算价格偏离
        price_deviation = df['close'] - df['vwap']
        
        # 计算30日最高收盘价出现的位置
        ts_argmax_close = self.tools.ts_argmax(df['close'], 30)
        rank_argmax = self.tools.rank(ts_argmax_close)
        
        # 计算2日衰减线性加权
        decay_weight = self.tools.decay_linear(rank_argmax, 2)
        
        # 计算最终结果
        result = -1 * (price_deviation / (decay_weight + 1e-10))
        
        return pd.Series(result, index=df.index)


# 跳过Alpha058, Alpha059 - 使用行业中性化，需要更复杂的实现

class Alpha060ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#060: (0 - (1 * ((2 * scale(rank(((((close - low) - (high - close)) / (high - low)) * volume)))) - 
                scale(rank(ts_argmax(close, 10))))))
    适合A股: 是，成交量加权价格位置因子
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="060",
            name="Alpha060",
            display_name="Alpha060-成交量加权价格位置",
            description="成交量加权的价格位置与最高价位置的对比",
            formula="-(2 * scale(rank(volume_weighted_position)) - scale(rank(ts_argmax(close, 10))))"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 计算成交量加权的价格位置
        close_low = df['close'] - df['low']
        high_close = df['high'] - df['close']
        high_low = df['high'] - df['low']
        
        price_position = (close_low - high_close) / (high_low + 1e-10)
        volume_weighted_position = price_position * df['volume']
        
        # 计算10日最高收盘价位置
        ts_argmax_close = self.tools.ts_argmax(df['close'], 10)
        
        # 分别排名和标准化
        rank_vw_position = self.tools.rank(volume_weighted_position)
        rank_argmax = self.tools.rank(ts_argmax_close)
        
        scale_vw_position = self.tools.scale(rank_vw_position)
        scale_argmax = self.tools.scale(rank_argmax)
        
        # 计算最终结果
        result = -1 * (2 * scale_vw_position - scale_argmax)
        
        return pd.Series(result, index=df.index)


class Alpha101Phase3Service:
    """Alpha101 Phase3 因子服务 (Alpha041-080，筛选适合A股的因子)"""
    
    def __init__(self):
        self.calculators = self._initialize_calculators()
        
    def _initialize_calculators(self) -> Dict[str, Alpha101ExtendedCalculator]:
        """初始化所有Phase3因子计算器"""
        calculators = {}
        
        # 只包含适合A股市场的因子
        calculator_classes = [
            Alpha041ExtendedCalculator,
            Alpha042ExtendedCalculator,
            Alpha043ExtendedCalculator,
            Alpha044ExtendedCalculator,
            Alpha045ExtendedCalculator,
            Alpha046ExtendedCalculator,
            Alpha047ExtendedCalculator,
            # 跳过Alpha048 - 行业中性化
            Alpha049ExtendedCalculator,
            Alpha050ExtendedCalculator,
            Alpha051ExtendedCalculator,
            Alpha052ExtendedCalculator,
            Alpha053ExtendedCalculator,
            Alpha054ExtendedCalculator,
            Alpha055ExtendedCalculator,
            # 跳过Alpha056 - 需要市值数据
            Alpha057ExtendedCalculator,
            # 跳过Alpha058, Alpha059 - 行业中性化
            Alpha060ExtendedCalculator,
        ]
        
        for calc_class in calculator_classes:
            calculator = calc_class()
            calculators[calculator.factor_id] = calculator
            
        return calculators
    
    def get_all_factors(self) -> Dict[str, Dict[str, Any]]:
        """获取所有Phase3因子的元数据"""
        factors = {}
        
        for factor_id, calculator in self.calculators.items():
            factors[factor_id] = {
                "id": calculator.factor_id,
                "name": calculator.name,
                "display_name": calculator.display_name,
                "description": calculator.description,
                "formula": calculator.formula,
                "category": calculator.category,
                "input_fields": calculator.input_fields,
                "default_parameters": calculator.default_parameters
            }
            
        return factors
    
    def get_available_factors(self) -> List[Dict[str, Any]]:
        """获取所有可用因子列表"""
        factors = []
        for factor_id, calculator in self.calculators.items():
            factors.append({
                'factor_id': factor_id,
                'name': calculator.name,
                'display_name': calculator.display_name,
                'description': calculator.description,
                'formula': calculator.formula,
                'category': calculator.category,
                'input_fields': calculator.input_fields,
                'default_parameters': calculator.default_parameters
            })
        return factors
    
    def calculate_single_factor(self, factor_id: str, data: pd.DataFrame, 
                              parameters: Dict[str, Any] = None) -> pd.Series:
        """计算单个因子"""
        if factor_id not in self.calculators:
            raise ValueError(f"未找到因子: {factor_id}")
        
        calculator = self.calculators[factor_id]
        try:
            return calculator.calculate(data, parameters)
        except Exception as e:
            raise ValueError(f"计算Alpha101 Phase3因子 {factor_id} 时出错: {e}")
    
    def calculate_factor(self, factor_id: str, data: pd.DataFrame, 
                        parameters: Dict[str, Any] = None) -> pd.Series:
        """计算指定因子"""
        return self.calculate_single_factor(factor_id, data, parameters)
    
    def get_factor_info(self, factor_id: str) -> Dict[str, Any]:
        """获取因子详细信息"""
        if factor_id not in self.calculators:
            raise ValueError(f"未知的因子ID: {factor_id}")
            
        calculator = self.calculators[factor_id]
        return {
            "id": calculator.factor_id,
            "name": calculator.name,
            "display_name": calculator.display_name,
            "description": calculator.description,
            "formula": calculator.formula,
            "category": calculator.category,
            "input_fields": calculator.input_fields,
            "default_parameters": calculator.default_parameters
        }


# 创建全局服务实例
alpha101_phase3_service = Alpha101Phase3Service()