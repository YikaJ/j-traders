"""
Alpha101 Phase 2: Alpha031-050 因子实现
基于 STHSF/alpha101 项目，针对A股市场优化
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List
from .alpha101_extended import Alpha101ExtendedCalculator, Alpha101Tools, TushareDataAdapter


class Alpha031ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#031: (rank(rank(rank(decay_linear((-1 * rank(rank(delta(close, 10)))), 10)))) + rank((-1 * delta(close, 3))))
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="031",
            name="Alpha031",
            display_name="Alpha031-衰减线性动量因子",
            description="基于衰减线性加权的价格动量因子",
            formula="rank(rank(rank(decay_linear((-1 * rank(rank(delta(close, 10)))), 10)))) + rank((-1 * delta(close, 3)))"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 计算10日价格变化
        delta_close_10 = self.tools.delta(df['close'], 10)
        
        # 多层排名处理
        rank_delta = self.tools.rank(self.tools.rank(delta_close_10))
        neg_rank_delta = -1 * rank_delta
        
        # 衰减线性加权
        decay_linear_factor = self.tools.decay_linear(neg_rank_delta, 10)
        
        # 三重排名
        triple_rank = self.tools.rank(self.tools.rank(self.tools.rank(decay_linear_factor)))
        
        # 3日价格变化部分
        delta_close_3 = self.tools.delta(df['close'], 3)
        rank_delta_3 = self.tools.rank(-1 * delta_close_3)
        
        # 组合结果
        result = triple_rank + rank_delta_3
        
        return pd.Series(result, index=df.index)


class Alpha032ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#032: (scale(((sum(close, 7) / 7) - close)) + (20 * scale(correlation(vwap, delay(close, 5), 230))))
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="032",
            name="Alpha032",
            display_name="Alpha032-均价相关性复合因子",
            description="基于均价偏差和VWAP相关性的复合因子",
            formula="scale(((sum(close, 7) / 7) - close)) + (20 * scale(correlation(vwap, delay(close, 5), 230)))"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 7日均价偏差
        close_mean_7 = self.tools.sum_series(df['close'], 7) / 7
        price_deviation = close_mean_7 - df['close']
        scaled_deviation = self.tools.scale(price_deviation)
        
        # VWAP与延迟收盘价的230日相关性
        delay_close_5 = self.tools.delay(df['close'], 5)
        correlation_factor = self.tools.correlation(df['vwap'], delay_close_5, 230)
        scaled_correlation = self.tools.scale(correlation_factor)
        
        # 组合结果
        result = scaled_deviation + (20 * scaled_correlation)
        
        return pd.Series(result, index=df.index)


class Alpha033ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#033: rank((-1 * ((1 - (open / close))^1)))
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="033",
            name="Alpha033",
            display_name="Alpha033-开盘收盘价比率因子",
            description="基于开盘价与收盘价比率的因子",
            formula="rank((-1 * ((1 - (open / close))^1)))"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 计算开盘收盘价比率
        open_close_ratio = df['open'] / (df['close'] + 1e-10)  # 避免除零
        
        # 计算因子值
        factor_value = -1 * (1 - open_close_ratio)
        
        # 排名
        result = self.tools.rank(factor_value)
        
        return pd.Series(result, index=df.index)


class Alpha034ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#034: rank(((1 - rank((stddev(returns, 2) / stddev(returns, 5)))) + (1 - rank(delta(close, 1)))))
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="034",
            name="Alpha034",
            display_name="Alpha034-收益率波动性复合因子",
            description="基于收益率波动性和价格变化的复合因子",
            formula="rank(((1 - rank((stddev(returns, 2) / stddev(returns, 5)))) + (1 - rank(delta(close, 1)))))"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 计算2日和5日收益率标准差
        stddev_returns_2 = self.tools.stddev(df['returns'], 2)
        stddev_returns_5 = self.tools.stddev(df['returns'], 5)
        
        # 标准差比率
        stddev_ratio = stddev_returns_2 / (stddev_returns_5 + 1e-10)
        rank_stddev_ratio = self.tools.rank(stddev_ratio)
        
        # 价格变化
        delta_close_1 = self.tools.delta(df['close'], 1)
        rank_delta_close = self.tools.rank(delta_close_1)
        
        # 组合因子
        combined_factor = (1 - rank_stddev_ratio) + (1 - rank_delta_close)
        
        # 最终排名
        result = self.tools.rank(combined_factor)
        
        return pd.Series(result, index=df.index)


class Alpha035ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#035: ((Ts_Rank(volume, 32) * (1 - Ts_Rank(((close + high) - low), 16))) * (1 - Ts_Rank(returns, 32)))
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="035",
            name="Alpha035",
            display_name="Alpha035-成交量价格收益率时序因子",
            description="基于成交量、价格范围和收益率的时序排名因子",
            formula="((Ts_Rank(volume, 32) * (1 - Ts_Rank(((close + high) - low), 16))) * (1 - Ts_Rank(returns, 32)))"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 成交量32日时序排名
        ts_rank_volume = self.tools.ts_rank(df['volume'], 32)
        
        # 价格范围16日时序排名
        price_range = (df['close'] + df['high']) - df['low']
        ts_rank_price_range = self.tools.ts_rank(price_range, 16)
        
        # 收益率32日时序排名
        ts_rank_returns = self.tools.ts_rank(df['returns'], 32)
        
        # 复合因子
        result = ts_rank_volume * (1 - ts_rank_price_range) * (1 - ts_rank_returns)
        
        return pd.Series(result, index=df.index)


class Alpha036ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#036: (((((2.21 * rank(correlation((close - open), delay(volume, 1), 15))) + (0.7 * rank((open - close)))) + 
                 (0.73 * rank(Ts_Rank(delay((-1 * returns), 6), 5)))) + rank(abs(correlation(vwap, adv20, 6)))) + 
                 (0.6 * rank((((sum(close, 200) / 200) - open) * (close - open)))))
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="036",
            name="Alpha036",
            display_name="Alpha036-多因子加权复合因子",
            description="多个子因子加权组合的复杂因子",
            formula="复杂的多因子加权组合"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 因子1: 收盘开盘差与延迟成交量的相关性
        close_open_diff = df['close'] - df['open']
        delay_volume = self.tools.delay(df['volume'], 1)
        corr_factor1 = self.tools.correlation(close_open_diff, delay_volume, 15)
        rank_factor1 = self.tools.rank(corr_factor1)
        
        # 因子2: 开盘收盘差
        open_close_diff = df['open'] - df['close']
        rank_factor2 = self.tools.rank(open_close_diff)
        
        # 因子3: 延迟收益率的时序排名
        delay_returns = self.tools.delay(-1 * df['returns'], 6)
        ts_rank_returns = self.tools.ts_rank(delay_returns, 5)
        rank_factor3 = self.tools.rank(ts_rank_returns)
        
        # 因子4: VWAP与adv20的相关性绝对值
        vwap_adv20_corr = self.tools.correlation(df['vwap'], df['adv20'], 6)
        rank_factor4 = self.tools.rank(np.abs(vwap_adv20_corr))
        
        # 因子5: 200日均价偏差与价格差的乘积
        close_mean_200 = self.tools.sum_series(df['close'], 200) / 200
        price_factor = (close_mean_200 - df['open']) * (df['close'] - df['open'])
        rank_factor5 = self.tools.rank(price_factor)
        
        # 加权组合
        result = (2.21 * rank_factor1 + 
                 0.7 * rank_factor2 + 
                 0.73 * rank_factor3 + 
                 rank_factor4 + 
                 0.6 * rank_factor5)
        
        return pd.Series(result, index=df.index)


class Alpha037ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#037: (rank(correlation(delay((open - close), 1), close, 200)) + rank((open - close)))
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="037",
            name="Alpha037",
            display_name="Alpha037-开盘收盘差相关性因子",
            description="基于开盘收盘价差与其延迟值相关性的因子",
            formula="(rank(correlation(delay((open - close), 1), close, 200)) + rank((open - close)))"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 开盘收盘差
        open_close_diff = df['open'] - df['close']
        
        # 延迟的开盘收盘差
        delay_open_close = self.tools.delay(open_close_diff, 1)
        
        # 与收盘价的200日相关性
        correlation_factor = self.tools.correlation(delay_open_close, df['close'], 200)
        rank_corr = self.tools.rank(correlation_factor)
        
        # 开盘收盘差的排名
        rank_open_close = self.tools.rank(open_close_diff)
        
        # 组合结果
        result = rank_corr + rank_open_close
        
        return pd.Series(result, index=df.index)


class Alpha038ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#038: ((-1 * rank(Ts_Rank(close, 10))) * rank((close / open)))
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="038",
            name="Alpha038",
            display_name="Alpha038-收盘价时序排名因子",
            description="基于收盘价时序排名和收盘开盘比的因子",
            formula="((-1 * rank(Ts_Rank(close, 10))) * rank((close / open)))"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 收盘价10日时序排名
        ts_rank_close = self.tools.ts_rank(df['close'], 10)
        rank_ts_rank = self.tools.rank(ts_rank_close)
        
        # 收盘开盘比
        close_open_ratio = df['close'] / (df['open'] + 1e-10)
        rank_ratio = self.tools.rank(close_open_ratio)
        
        # 组合结果
        result = (-1 * rank_ts_rank) * rank_ratio
        
        return pd.Series(result, index=df.index)


class Alpha039ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#039: ((-1 * rank((delta(close, 7) * (1 - rank(decay_linear((volume / adv20), 9)))))) * 
                (1 + rank(sum(returns, 250))))
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="039",
            name="Alpha039",
            display_name="Alpha039-价格变化成交量复合因子",
            description="基于价格变化、相对成交量和长期收益的复合因子",
            formula="((-1 * rank((delta(close, 7) * (1 - rank(decay_linear((volume / adv20), 9)))))) * (1 + rank(sum(returns, 250))))"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 7日价格变化
        delta_close_7 = self.tools.delta(df['close'], 7)
        
        # 相对成交量的衰减线性加权
        relative_volume = df['volume'] / (df['adv20'] + 1e-10)
        decay_volume = self.tools.decay_linear(relative_volume, 9)
        rank_decay_volume = self.tools.rank(decay_volume)
        
        # 价格-成交量因子
        price_volume_factor = delta_close_7 * (1 - rank_decay_volume)
        rank_pv_factor = self.tools.rank(price_volume_factor)
        
        # 250日累计收益
        sum_returns_250 = self.tools.sum_series(df['returns'], 250)
        rank_sum_returns = self.tools.rank(sum_returns_250)
        
        # 组合结果
        result = (-1 * rank_pv_factor) * (1 + rank_sum_returns)
        
        return pd.Series(result, index=df.index)


class Alpha040ExtendedCalculator(Alpha101ExtendedCalculator):
    """
    Alpha#040: ((-1 * rank(stddev(high, 10))) * correlation(high, volume, 10))
    """
    
    def __init__(self):
        super().__init__(
            alpha_id="040",
            name="Alpha040",
            display_name="Alpha040-最高价波动性相关因子",
            description="基于最高价波动性和价量相关性的因子",
            formula="((-1 * rank(stddev(high, 10))) * correlation(high, volume, 10))"
        )
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        df = self.prepare_data(data)
        
        # 最高价10日标准差
        stddev_high = self.tools.stddev(df['high'], 10)
        rank_stddev = self.tools.rank(stddev_high)
        
        # 最高价与成交量的10日相关性
        corr_high_volume = self.tools.correlation(df['high'], df['volume'], 10)
        
        # 组合结果
        result = (-1 * rank_stddev) * corr_high_volume
        
        return pd.Series(result, index=df.index)


class Alpha101Phase2Service:
    """Alpha101 Phase2 因子服务 (Alpha031-050)"""
    
    def __init__(self):
        self.calculators = self._initialize_calculators()
        
    def _initialize_calculators(self) -> Dict[str, Alpha101ExtendedCalculator]:
        """初始化所有Phase2因子计算器"""
        calculators = {}
        
        # Alpha031-040
        calculator_classes = [
            Alpha031ExtendedCalculator,
            Alpha032ExtendedCalculator,
            Alpha033ExtendedCalculator,
            Alpha034ExtendedCalculator,
            Alpha035ExtendedCalculator,
            Alpha036ExtendedCalculator,
            Alpha037ExtendedCalculator,
            Alpha038ExtendedCalculator,
            Alpha039ExtendedCalculator,
            Alpha040ExtendedCalculator
        ]
        
        for calc_class in calculator_classes:
            calculator = calc_class()
            calculators[calculator.factor_id] = calculator
            
        return calculators
    
    def get_all_factors(self) -> Dict[str, Dict[str, Any]]:
        """获取所有Phase2因子的元数据"""
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
    
    def calculate_factor(self, factor_id: str, data: pd.DataFrame, 
                        parameters: Dict[str, Any] = None) -> pd.Series:
        """计算指定因子"""
        if factor_id not in self.calculators:
            raise ValueError(f"未知的因子ID: {factor_id}")
            
        calculator = self.calculators[factor_id]
        return calculator.calculate(data, parameters)
    
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
            raise ValueError(f"计算Alpha101 Phase2因子 {factor_id} 时出错: {e}")


# 创建全局服务实例
alpha101_phase2_service = Alpha101Phase2Service()