"""
Alpha101 Phase 4: Alpha061-101 因子实现
基于 STHSF/alpha101 项目，针对A股市场优化
筛选适合A股市场的因子，抛弃需要行业中性化等复杂功能的因子
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List
from .alpha101_extended import Alpha101ExtendedCalculator, Alpha101Tools, TushareDataAdapter


class Alpha061ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#061: (rank((vwap - ts_min(vwap, 16.1219))) < rank(correlation(vwap, adv180, 17.9282)))
    简化为: rank(vwap - ts_min(vwap, 16)) < rank(correlation(vwap, adv180, 18))
    适合A股: 是，VWAP相关因子
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="061",
            name="Alpha061",
            display_name="Alpha061-VWAP位置相关性",
            description="VWAP相对位置与长期成交额相关性比较",
            formula="rank(vwap - ts_min(vwap, 16)) < rank(correlation(vwap, adv180, 18))"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 计算VWAP相对最低位置
        ts_min_vwap = self.tools.ts_min(df['vwap'], 16)
        vwap_position = df['vwap'] - ts_min_vwap
        rank_vwap_position = self.tools.rank(vwap_position)
        
        # 计算VWAP与180日平均成交额的相关性
        correlation_factor = self.tools.correlation(df['vwap'], df['adv180'], 18)
        rank_correlation = self.tools.rank(correlation_factor)
        
        # 比较两个排名
        result = (rank_vwap_position < rank_correlation).astype(int)
        
        return pd.Series(result, index=df.index)


class Alpha062ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#062: 复杂的开盘价和中价比较因子
    适合A股: 是，但需要简化
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="062",
            name="Alpha062",
            display_name="Alpha062-开盘价位置比较",
            description="基于开盘价和中价位置的比较因子",
            formula="简化的开盘价和中价位置比较"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 简化实现
        # 计算VWAP与20日平均成交额的相关性
        corr_vwap_adv = self.tools.correlation(df['vwap'], df['adv20'], 10)
        rank_corr = self.tools.rank(corr_vwap_adv)
        
        # 计算开盘价和中价的位置比较
        rank_open = self.tools.rank(df['open'])
        mid_price = (df['high'] + df['low']) / 2
        rank_mid = self.tools.rank(mid_price)
        rank_high = self.tools.rank(df['high'])
        
        # 位置比较条件
        condition = (rank_open + rank_open) < (rank_mid + rank_high)
        
        # 最终结果
        result = (rank_corr < condition.astype(int)).astype(int) * -1
        
        return pd.Series(result, index=df.index)


# 跳过Alpha063 - 行业中性化

class Alpha064ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#064: 开盘价低价组合与中价VWAP组合的相关性比较
    适合A股: 是，价格相关性因子
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="064",
            name="Alpha064",
            display_name="Alpha064-价格组合相关性",
            description="不同价格组合的相关性比较因子",
            formula="开盘价低价组合与中价VWAP组合的相关性比较"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 计算开盘价和低价的加权组合
        open_low_combo = df['open'] * 0.18 + df['low'] * 0.82
        sum_open_low = self.tools.sum_series(open_low_combo, 13)
        
        # 计算与120日平均成交额的相关性
        corr1 = self.tools.correlation(sum_open_low, df['adv120'], 16)
        rank_corr1 = self.tools.rank(corr1)
        
        # 计算中价和VWAP的加权组合变化
        mid_price = (df['high'] + df['low']) / 2
        mid_vwap_combo = mid_price * 0.18 + df['vwap'] * 0.82
        delta_combo = self.tools.delta(mid_vwap_combo, 4)
        rank_delta = self.tools.rank(delta_combo)
        
        # 比较结果
        result = (rank_corr1 < rank_delta).astype(int) * -1
        
        return pd.Series(result, index=df.index)


class Alpha065ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#065: 开盘价VWAP组合与开盘价位置的比较
    适合A股: 是
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="065",
            name="Alpha065",
            display_name="Alpha065-开盘价VWAP组合",
            description="开盘价VWAP组合与最低开盘价位置的比较",
            formula="开盘价VWAP组合相关性与开盘价位置比较"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 计算开盘价和VWAP的微小加权组合
        open_vwap_combo = df['open'] * 0.008 + df['vwap'] * 0.992
        
        # 计算与60日平均成交额的相关性
        corr_combo = self.tools.correlation(open_vwap_combo, df['adv60'], 6)
        rank_corr = self.tools.rank(corr_combo)
        
        # 计算开盘价相对最低位置
        ts_min_open = self.tools.ts_min(df['open'], 14)
        open_position = df['open'] - ts_min_open
        rank_position = self.tools.rank(open_position)
        
        # 比较结果
        result = (rank_corr < rank_position).astype(int) * -1
        
        return pd.Series(result, index=df.index)


class Alpha066ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#066: VWAP变化与低价组合因子
    适合A股: 是
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="066",
            name="Alpha066",
            display_name="Alpha066-VWAP变化组合",
            description="VWAP变化与低价开盘价组合的复合因子",
            formula="VWAP变化与低价开盘价组合的衰减加权"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 计算VWAP变化
        delta_vwap = self.tools.delta(df['vwap'], 4)
        decay_vwap = self.tools.decay_linear(delta_vwap, 7)
        rank_decay_vwap = self.tools.rank(decay_vwap)
        
        # 计算低价组合相对位置
        low_combo = df['low'] * 0.97 + df['low'] * 0.03  # 几乎就是low
        mid_price = (df['high'] + df['low']) / 2
        relative_position = (low_combo - df['vwap']) / (df['open'] - mid_price + 1e-10)
        
        # 计算衰减加权和时序排名
        decay_position = self.tools.decay_linear(relative_position, 11)
        ts_rank_position = self.tools.ts_rank(decay_position, 7)
        
        # 组合结果
        result = (rank_decay_vwap + ts_rank_position) * -1
        
        return pd.Series(result, index=df.index)


# 跳过Alpha067-Alpha070 - 行业中性化

class Alpha071ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#071: 收盘价与成交额相关性的时序排名
    适合A股: 是
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="071",
            name="Alpha071",
            display_name="Alpha071-收盘价成交额相关性",
            description="收盘价与成交额相关性的最大时序排名",
            formula="max(ts_rank(decay_linear(correlation(ts_rank(close, 3), ts_rank(adv180, 12), 18), 4), 16), ts_rank(decay_linear(rank((low + open) - 2*vwap)^2, 16), 4))"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 第一部分：收盘价与成交额的相关性
        ts_rank_close = self.tools.ts_rank(df['close'], 3)
        ts_rank_adv180 = self.tools.ts_rank(df['adv180'], 12)
        corr_close_adv = self.tools.correlation(ts_rank_close, ts_rank_adv180, 18)
        decay_corr = self.tools.decay_linear(corr_close_adv, 4)
        ts_rank_decay_corr = self.tools.ts_rank(decay_corr, 16)
        
        # 第二部分：价格组合排名
        price_combo = df['low'] + df['open'] - 2 * df['vwap']
        rank_combo = self.tools.rank(price_combo)
        squared_rank = np.power(rank_combo, 2)
        decay_squared = self.tools.decay_linear(squared_rank, 16)
        ts_rank_decay_squared = self.tools.ts_rank(decay_squared, 4)
        
        # 取最大值
        result = np.maximum(ts_rank_decay_corr, ts_rank_decay_squared)
        
        return pd.Series(result, index=df.index)


class Alpha072ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#072: 中价与成交额相关性比值
    适合A股: 是
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="072",
            name="Alpha072",
            display_name="Alpha072-中价成交额相关性比",
            description="不同中价成交额相关性的比值因子",
            formula="rank(decay_linear(correlation(mid_price, adv40, 9), 10)) / rank(decay_linear(correlation(ts_rank(vwap, 4), ts_rank(volume, 19), 7), 3))"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 分子：中价与40日平均成交额的相关性
        mid_price = (df['high'] + df['low']) / 2
        corr_mid_adv = self.tools.correlation(mid_price, df['adv40'], 9)
        decay_corr_mid = self.tools.decay_linear(corr_mid_adv, 10)
        rank_numerator = self.tools.rank(decay_corr_mid)
        
        # 分母：VWAP和成交量时序排名的相关性
        ts_rank_vwap = self.tools.ts_rank(df['vwap'], 4)
        ts_rank_volume = self.tools.ts_rank(df['volume'], 19)
        corr_vwap_vol = self.tools.correlation(ts_rank_vwap, ts_rank_volume, 7)
        decay_corr_vwap = self.tools.decay_linear(corr_vwap_vol, 3)
        rank_denominator = self.tools.rank(decay_corr_vwap)
        
        # 计算比值
        result = rank_numerator / (rank_denominator + 1e-10)
        
        return pd.Series(result, index=df.index)


class Alpha073ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#073: VWAP变化与开盘价低价组合的最大值
    适合A股: 是
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="073",
            name="Alpha073",
            display_name="Alpha073-VWAP变化组合最大值",
            description="VWAP变化与开盘价低价组合的最大值因子",
            formula="max(rank(decay_linear(delta(vwap, 5), 3)), ts_rank(decay_linear(open_low_combo_change, 3), 16)) * -1"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 第一部分：VWAP变化
        delta_vwap = self.tools.delta(df['vwap'], 5)
        decay_delta_vwap = self.tools.decay_linear(delta_vwap, 3)
        rank_vwap_change = self.tools.rank(decay_delta_vwap)
        
        # 第二部分：开盘价低价组合变化
        open_low_combo = df['open'] * 0.15 + df['low'] * 0.85
        delta_combo = self.tools.delta(open_low_combo, 2)
        relative_change = delta_combo / (open_low_combo + 1e-10)
        decay_relative = self.tools.decay_linear(relative_change * -1, 3)
        ts_rank_combo = self.tools.ts_rank(decay_relative, 16)
        
        # 取最大值并乘以-1
        result = np.maximum(rank_vwap_change, ts_rank_combo) * -1
        
        return pd.Series(result, index=df.index)


class Alpha074ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#074: 收盘价与成交额相关性比较
    适合A股: 是
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="074",
            name="Alpha074",
            display_name="Alpha074-收盘价成交额相关性比较",
            description="不同收盘价成交额相关性的比较因子",
            formula="rank(correlation(close, sum(adv30, 37), 15)) < rank(correlation(rank(high*0.03 + vwap*0.97), rank(volume), 11)) * -1"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 第一部分：收盘价与成交额和的相关性
        sum_adv30 = self.tools.sum_series(df['adv30'], 37)
        corr_close_adv = self.tools.correlation(df['close'], sum_adv30, 15)
        rank_corr_close = self.tools.rank(corr_close_adv)
        
        # 第二部分：高价VWAP组合与成交量的相关性
        high_vwap_combo = df['high'] * 0.03 + df['vwap'] * 0.97
        rank_combo = self.tools.rank(high_vwap_combo)
        rank_volume = self.tools.rank(df['volume'])
        corr_combo_vol = self.tools.correlation(rank_combo, rank_volume, 11)
        rank_corr_combo = self.tools.rank(corr_combo_vol)
        
        # 比较结果
        result = (rank_corr_close < rank_corr_combo).astype(int) * -1
        
        return pd.Series(result, index=df.index)


class Alpha075ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#075: VWAP成交量相关性与低价成交额相关性比较
    适合A股: 是
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="075",
            name="Alpha075",
            display_name="Alpha075-量价相关性比较",
            description="VWAP成交量与低价成交额相关性的比较",
            formula="rank(correlation(vwap, volume, 4)) < rank(correlation(rank(low), rank(adv50), 12))"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 第一部分：VWAP与成交量的相关性
        corr_vwap_vol = self.tools.correlation(df['vwap'], df['volume'], 4)
        rank_corr_vwap = self.tools.rank(corr_vwap_vol)
        
        # 第二部分：低价排名与成交额排名的相关性
        rank_low = self.tools.rank(df['low'])
        rank_adv50 = self.tools.rank(df['adv50'])
        corr_low_adv = self.tools.correlation(rank_low, rank_adv50, 12)
        rank_corr_low = self.tools.rank(corr_low_adv)
        
        # 比较结果
        result = (rank_corr_vwap < rank_corr_low).astype(int)
        
        return pd.Series(result, index=df.index)


# 跳过Alpha076 - 行业中性化

class Alpha077ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#077: 中价高价组合与中价成交额相关性的最小值
    适合A股: 是
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="077",
            name="Alpha077",
            display_name="Alpha077-中价高价组合最小值",
            description="中价高价组合与中价成交额相关性的最小值",
            formula="min(rank(decay_linear(mid_high_combo, 20)), rank(decay_linear(correlation(mid_price, adv40, 3), 6)))"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 第一部分：中价和高价组合
        mid_price = (df['high'] + df['low']) / 2
        mid_high_combo = mid_price + df['high'] - (df['vwap'] + df['high'])
        decay_combo = self.tools.decay_linear(mid_high_combo, 20)
        rank_combo = self.tools.rank(decay_combo)
        
        # 第二部分：中价与成交额相关性
        corr_mid_adv = self.tools.correlation(mid_price, df['adv40'], 3)
        decay_corr = self.tools.decay_linear(corr_mid_adv, 6)
        rank_corr = self.tools.rank(decay_corr)
        
        # 取最小值
        result = np.minimum(rank_combo, rank_corr)
        
        return pd.Series(result, index=df.index)


class Alpha078ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#078: 低价VWAP组合与VWAP成交量相关性的幂次
    适合A股: 是
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="078",
            name="Alpha078",
            display_name="Alpha078-低价VWAP幂次相关性",
            description="低价VWAP组合相关性的幂次因子",
            formula="rank(correlation(sum(low*0.35 + vwap*0.65, 20), sum(adv40, 20), 7))^rank(correlation(rank(vwap), rank(volume), 6))"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 底数：低价VWAP组合与成交额的相关性
        low_vwap_combo = df['low'] * 0.35 + df['vwap'] * 0.65
        sum_combo = self.tools.sum_series(low_vwap_combo, 20)
        sum_adv40 = self.tools.sum_series(df['adv40'], 20)
        corr_combo_adv = self.tools.correlation(sum_combo, sum_adv40, 7)
        rank_base = self.tools.rank(corr_combo_adv)
        
        # 指数：VWAP与成交量排名的相关性
        rank_vwap = self.tools.rank(df['vwap'])
        rank_volume = self.tools.rank(df['volume'])
        corr_vwap_vol = self.tools.correlation(rank_vwap, rank_volume, 6)
        rank_exponent = self.tools.rank(corr_vwap_vol)
        
        # 计算幂次（限制指数范围避免数值问题）
        safe_exponent = np.clip(rank_exponent, -2, 2)
        result = np.power(np.abs(rank_base) + 1e-10, safe_exponent) * np.sign(rank_base)
        
        return pd.Series(result, index=df.index)


# 跳过Alpha079-Alpha082 - 行业中性化

class Alpha083ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#083: 高低价比与成交量的复合因子
    适合A股: 是
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="083",
            name="Alpha083",
            display_name="Alpha083-高低价比成交量",
            description="延迟高低价比与成交量的复合因子",
            formula="(rank(delay((high-low)/avg(close,5), 2)) * rank(rank(volume))) / ((high-low)/avg(close,5) / (vwap-close))"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 计算高低价差与5日均价的比值
        avg_close_5 = self.tools.sum_series(df['close'], 5) / 5
        high_low_ratio = (df['high'] - df['low']) / (avg_close_5 + 1e-10)
        
        # 延迟2期
        delay_ratio = self.tools.delay(high_low_ratio, 2)
        rank_delay_ratio = self.tools.rank(delay_ratio)
        
        # 成交量双重排名
        rank_volume = self.tools.rank(df['volume'])
        rank_rank_volume = self.tools.rank(rank_volume)
        
        # 分子
        numerator = rank_delay_ratio * rank_rank_volume
        
        # 分母
        vwap_close_diff = df['vwap'] - df['close']
        denominator = high_low_ratio / (vwap_close_diff + 1e-10)
        
        # 最终结果
        result = numerator / (denominator + 1e-10)
        
        return pd.Series(result, index=df.index)


class Alpha084ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#084: VWAP位置的SignedPower函数
    适合A股: 是
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="084",
            name="Alpha084",
            display_name="Alpha084-VWAP位置幂次",
            description="VWAP相对位置的签名幂次因子",
            formula="SignedPower(ts_rank(vwap - ts_max(vwap, 15), 21), delta(close, 5))"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 计算VWAP相对最高位置
        ts_max_vwap = self.tools.ts_max(df['vwap'], 15)
        vwap_position = df['vwap'] - ts_max_vwap
        ts_rank_position = self.tools.ts_rank(vwap_position, 21)
        
        # 计算收盘价变化
        delta_close = self.tools.delta(df['close'], 5)
        
        # SignedPower函数：保持符号的幂次运算
        result = self.tools.signedpower(ts_rank_position, delta_close)
        
        return pd.Series(result, index=df.index)


class Alpha085ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#085: 高价收盘价组合与中价成交量时序排名相关性的幂次
    适合A股: 是
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="085",
            name="Alpha085",
            display_name="Alpha085-高价组合时序相关性",
            description="高价收盘价组合与中价成交量时序相关性的幂次",
            formula="rank(correlation(high*0.88 + close*0.12, adv30, 10))^rank(correlation(ts_rank(mid_price, 4), ts_rank(volume, 10), 7))"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 底数：高价收盘价组合与成交额的相关性
        high_close_combo = df['high'] * 0.88 + df['close'] * 0.12
        corr_combo_adv = self.tools.correlation(high_close_combo, df['adv30'], 10)
        rank_base = self.tools.rank(corr_combo_adv)
        
        # 指数：中价与成交量时序排名的相关性
        mid_price = (df['high'] + df['low']) / 2
        ts_rank_mid = self.tools.ts_rank(mid_price, 4)
        ts_rank_volume = self.tools.ts_rank(df['volume'], 10)
        corr_mid_vol = self.tools.correlation(ts_rank_mid, ts_rank_volume, 7)
        rank_exponent = self.tools.rank(corr_mid_vol)
        
        # 计算幂次（安全处理）
        safe_exponent = np.clip(rank_exponent, -2, 2)
        result = np.power(np.abs(rank_base) + 1e-10, safe_exponent) * np.sign(rank_base)
        
        return pd.Series(result, index=df.index)


class Alpha086ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#086: 收盘价与成交额时序相关性比较
    适合A股: 是
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="086",
            name="Alpha086",
            display_name="Alpha086-收盘价成交额时序相关性",
            description="收盘价成交额时序相关性与开盘价位置的比较",
            formula="(ts_rank(correlation(close, sum(adv20, 15), 6), 20) < rank((open + close) - (vwap + open))) * -1"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 第一部分：收盘价与成交额和的时序相关性
        sum_adv20 = self.tools.sum_series(df['adv20'], 15)
        corr_close_adv = self.tools.correlation(df['close'], sum_adv20, 6)
        ts_rank_corr = self.tools.ts_rank(corr_close_adv, 20)
        
        # 第二部分：开盘价收盘价组合位置
        open_close_combo = (df['open'] + df['close']) - (df['vwap'] + df['open'])
        rank_combo = self.tools.rank(open_close_combo)
        
        # 比较结果
        result = (ts_rank_corr < rank_combo).astype(int) * -1
        
        return pd.Series(result, index=df.index)


# 跳过Alpha087 - 行业中性化

class Alpha088ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#088: 开盘价低价与高价收盘价排名组合的最小值
    适合A股: 是
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="088",
            name="Alpha088",
            display_name="Alpha088-价格排名组合最小值",
            description="开盘价低价与高价收盘价排名组合的最小值",
            formula="min(rank(decay_linear((rank(open) + rank(low)) - (rank(high) + rank(close)), 8)), ts_rank(decay_linear(correlation(...), 7), 3))"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 第一部分：价格排名组合差值
        rank_open = self.tools.rank(df['open'])
        rank_low = self.tools.rank(df['low'])
        rank_high = self.tools.rank(df['high'])
        rank_close = self.tools.rank(df['close'])
        
        rank_diff = (rank_open + rank_low) - (rank_high + rank_close)
        decay_rank_diff = self.tools.decay_linear(rank_diff, 8)
        rank_first_part = self.tools.rank(decay_rank_diff)
        
        # 第二部分：收盘价与成交额时序排名相关性
        ts_rank_close = self.tools.ts_rank(df['close'], 8)
        ts_rank_adv60 = self.tools.ts_rank(df['adv60'], 21)
        corr_close_adv = self.tools.correlation(ts_rank_close, ts_rank_adv60, 8)
        decay_corr = self.tools.decay_linear(corr_close_adv, 7)
        ts_rank_second_part = self.tools.ts_rank(decay_corr, 3)
        
        # 取最小值
        result = np.minimum(rank_first_part, ts_rank_second_part)
        
        return pd.Series(result, index=df.index)


# 跳过Alpha089-Alpha091 - 行业中性化

class Alpha092ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#092: 中价收盘价组合条件与低价成交额相关性的最小值
    适合A股: 是
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="092",
            name="Alpha092",
            display_name="Alpha092-中价条件相关性最小值",
            description="中价收盘价组合条件与低价成交额相关性的最小值",
            formula="min(ts_rank(decay_linear(condition, 15), 19), ts_rank(decay_linear(correlation(rank(low), rank(adv30), 8), 7), 7))"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 第一部分：条件判断
        mid_price = (df['high'] + df['low']) / 2
        condition = ((mid_price + df['close']) < (df['low'] + df['open'])).astype(float)
        decay_condition = self.tools.decay_linear(condition, 15)
        ts_rank_condition = self.tools.ts_rank(decay_condition, 19)
        
        # 第二部分：低价与成交额排名相关性
        rank_low = self.tools.rank(df['low'])
        rank_adv30 = self.tools.rank(df['adv30'])
        corr_low_adv = self.tools.correlation(rank_low, rank_adv30, 8)
        decay_corr = self.tools.decay_linear(corr_low_adv, 7)
        ts_rank_corr = self.tools.ts_rank(decay_corr, 7)
        
        # 取最小值
        result = np.minimum(ts_rank_condition, ts_rank_corr)
        
        return pd.Series(result, index=df.index)


# 跳过Alpha093 - 行业中性化

class Alpha094ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#094: VWAP位置与VWAP成交额时序相关性的幂次
    适合A股: 是
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="094",
            name="Alpha094",
            display_name="Alpha094-VWAP位置时序相关性",
            description="VWAP位置与VWAP成交额时序相关性的幂次因子",
            formula="(rank(vwap - ts_min(vwap, 12))^ts_rank(correlation(ts_rank(vwap, 20), ts_rank(adv60, 4), 18), 3)) * -1"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 底数：VWAP相对最低位置
        ts_min_vwap = self.tools.ts_min(df['vwap'], 12)
        vwap_position = df['vwap'] - ts_min_vwap
        rank_base = self.tools.rank(vwap_position)
        
        # 指数：VWAP与成交额时序排名相关性
        ts_rank_vwap = self.tools.ts_rank(df['vwap'], 20)
        ts_rank_adv60 = self.tools.ts_rank(df['adv60'], 4)
        corr_vwap_adv = self.tools.correlation(ts_rank_vwap, ts_rank_adv60, 18)
        ts_rank_exponent = self.tools.ts_rank(corr_vwap_adv, 3)
        
        # 计算幂次（安全处理）
        safe_exponent = np.clip(ts_rank_exponent, -2, 2)
        result = np.power(np.abs(rank_base) + 1e-10, safe_exponent) * np.sign(rank_base) * -1
        
        return pd.Series(result, index=df.index)


class Alpha095ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#095: 开盘价位置与中价成交额相关性时序排名比较
    适合A股: 是
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="095",
            name="Alpha095",
            display_name="Alpha095-开盘价位置相关性比较",
            description="开盘价位置与中价成交额相关性时序排名的比较",
            formula="rank(open - ts_min(open, 12)) < ts_rank((rank(correlation(sum(mid_price, 19), sum(adv40, 19), 13))^5), 12)"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 第一部分：开盘价相对最低位置
        ts_min_open = self.tools.ts_min(df['open'], 12)
        open_position = df['open'] - ts_min_open
        rank_open_position = self.tools.rank(open_position)
        
        # 第二部分：中价与成交额相关性的5次方时序排名
        mid_price = (df['high'] + df['low']) / 2
        sum_mid_price = self.tools.sum_series(mid_price, 19)
        sum_adv40 = self.tools.sum_series(df['adv40'], 19)
        corr_mid_adv = self.tools.correlation(sum_mid_price, sum_adv40, 13)
        rank_corr = self.tools.rank(corr_mid_adv)
        corr_power5 = np.power(np.abs(rank_corr) + 1e-10, 5) * np.sign(rank_corr)
        ts_rank_power = self.tools.ts_rank(corr_power5, 12)
        
        # 比较结果
        result = (rank_open_position < ts_rank_power).astype(int)
        
        return pd.Series(result, index=df.index)


class Alpha096ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#096: VWAP成交量相关性与收盘价成交额相关性ArgMax的最大值
    适合A股: 是
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="096",
            name="Alpha096",
            display_name="Alpha096-相关性ArgMax最大值",
            description="VWAP成交量与收盘价成交额相关性ArgMax的最大值",
            formula="max(ts_rank(decay_linear(correlation(rank(vwap), rank(volume), 4), 4), 8), ts_rank(decay_linear(ts_argmax(...), 14), 13)) * -1"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 第一部分：VWAP与成交量排名相关性
        rank_vwap = self.tools.rank(df['vwap'])
        rank_volume = self.tools.rank(df['volume'])
        corr_vwap_vol = self.tools.correlation(rank_vwap, rank_volume, 4)
        decay_corr = self.tools.decay_linear(corr_vwap_vol, 4)
        ts_rank_first = self.tools.ts_rank(decay_corr, 8)
        
        # 第二部分：收盘价与成交额相关性的ArgMax
        ts_rank_close = self.tools.ts_rank(df['close'], 7)
        ts_rank_adv60 = self.tools.ts_rank(df['adv60'], 4)
        corr_close_adv = self.tools.correlation(ts_rank_close, ts_rank_adv60, 3)
        ts_argmax_corr = self.tools.ts_argmax(corr_close_adv, 13)
        decay_argmax = self.tools.decay_linear(ts_argmax_corr, 14)
        ts_rank_second = self.tools.ts_rank(decay_argmax, 13)
        
        # 取最大值并乘以-1
        result = np.maximum(ts_rank_first, ts_rank_second) * -1
        
        return pd.Series(result, index=df.index)


# 跳过Alpha097 - 行业中性化

class Alpha098ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#098: VWAP成交额相关性与开盘价成交额相关性ArgMin的差值
    适合A股: 是
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="098",
            name="Alpha098",
            display_name="Alpha098-相关性ArgMin差值",
            description="VWAP成交额与开盘价成交额相关性ArgMin的差值",
            formula="rank(decay_linear(correlation(vwap, sum(adv5, 26), 5), 7)) - rank(decay_linear(ts_rank(ts_argmin(...), 7), 8))"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 第一部分：VWAP与成交额和的相关性
        sum_adv5 = self.tools.sum_series(df['adv5'], 26)
        corr_vwap_adv = self.tools.correlation(df['vwap'], sum_adv5, 5)
        decay_corr = self.tools.decay_linear(corr_vwap_adv, 7)
        rank_first = self.tools.rank(decay_corr)
        
        # 第二部分：开盘价与成交额排名相关性的ArgMin
        rank_open = self.tools.rank(df['open'])
        rank_adv15 = self.tools.rank(df['adv15'])
        corr_open_adv = self.tools.correlation(rank_open, rank_adv15, 21)
        ts_argmin_corr = self.tools.ts_argmin(corr_open_adv, 9)
        ts_rank_argmin = self.tools.ts_rank(ts_argmin_corr, 7)
        decay_ts_rank = self.tools.decay_linear(ts_rank_argmin, 8)
        rank_second = self.tools.rank(decay_ts_rank)
        
        # 计算差值
        result = rank_first - rank_second
        
        return pd.Series(result, index=df.index)


class Alpha099ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#099: 中价成交额和与低价成交量相关性的比较
    适合A股: 是
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="099",
            name="Alpha099",
            display_name="Alpha099-中价成交额相关性比较",
            description="中价成交额和与低价成交量相关性的比较",
            formula="(rank(correlation(sum(mid_price, 20), sum(adv60, 20), 8)) < rank(correlation(low, volume, 6))) * -1"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 第一部分：中价和与成交额和的相关性
        mid_price = (df['high'] + df['low']) / 2
        sum_mid_price = self.tools.sum_series(mid_price, 20)
        sum_adv60 = self.tools.sum_series(df['adv60'], 20)
        corr_mid_adv = self.tools.correlation(sum_mid_price, sum_adv60, 8)
        rank_first = self.tools.rank(corr_mid_adv)
        
        # 第二部分：低价与成交量的相关性
        corr_low_vol = self.tools.correlation(df['low'], df['volume'], 6)
        rank_second = self.tools.rank(corr_low_vol)
        
        # 比较结果
        result = (rank_first < rank_second).astype(int) * -1
        
        return pd.Series(result, index=df.index)


# 跳过Alpha100 - 行业中性化

class Alpha101ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#101: ((close - open) / ((high - low) + .001))
    适合A股: 是，最简单的日内动量因子
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="101",
            name="Alpha101",
            display_name="Alpha101-日内动量",
            description="日内价格动量因子",
            formula="(close - open) / (high - low + 0.001)"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 计算日内动量
        intraday_momentum = (df['close'] - df['open']) / (df['high'] - df['low'] + 0.001)
        
        return pd.Series(intraday_momentum, index=df.index)


class Alpha101Phase4Service:
    """Alpha101 Phase4 因子服务 (Alpha061-101，筛选适合A股的因子)"""
    
    def __init__(self):
        self.calculators = self._initialize_calculators()
        
    def _initialize_calculators(self) -> Dict[str, Alpha101ExtendedCalculator]:
        """初始化所有Phase4因子计算器"""
        calculators = {}
        
        # 只包含适合A股市场的因子，跳过需要行业中性化的因子
        calculator_classes = [
            Alpha061ExtendedCalculator,
            Alpha062ExtendedCalculator,
            # 跳过Alpha063 - 行业中性化
            Alpha064ExtendedCalculator,
            Alpha065ExtendedCalculator,
            Alpha066ExtendedCalculator,
            # 跳过Alpha067-070 - 行业中性化
            Alpha071ExtendedCalculator,
            Alpha072ExtendedCalculator,
            Alpha073ExtendedCalculator,
            Alpha074ExtendedCalculator,
            Alpha075ExtendedCalculator,
            # 跳过Alpha076 - 行业中性化
            Alpha077ExtendedCalculator,
            Alpha078ExtendedCalculator,
            # 跳过Alpha079-082 - 行业中性化
            Alpha083ExtendedCalculator,
            Alpha084ExtendedCalculator,
            Alpha085ExtendedCalculator,
            Alpha086ExtendedCalculator,
            # 跳过Alpha087 - 行业中性化
            Alpha088ExtendedCalculator,
            # 跳过Alpha089-091 - 行业中性化
            Alpha092ExtendedCalculator,
            # 跳过Alpha093 - 行业中性化
            Alpha094ExtendedCalculator,
            Alpha095ExtendedCalculator,
            Alpha096ExtendedCalculator,
            # 跳过Alpha097 - 行业中性化
            Alpha098ExtendedCalculator,
            Alpha099ExtendedCalculator,
            # 跳过Alpha100 - 行业中性化
            Alpha101ExtendedCalculator,
        ]
        
        for calc_class in calculator_classes:
            calculator = calc_class()
            calculators[calculator.factor_id] = calculator
            
        return calculators
    
    def get_all_factors(self) -> Dict[str, Dict[str, Any]]:
        """获取所有Phase4因子的元数据"""
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
            raise ValueError(f"计算Alpha101 Phase4因子 {factor_id} 时出错: {e}")
    
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
alpha101_phase4_service = Alpha101Phase4Service()