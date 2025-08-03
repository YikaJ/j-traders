"""
因子标准化处理器
在策略层面统一处理因子的标准化，支持多种标准化方法
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union
from enum import Enum


class StandardizationMethod(str, Enum):
    """标准化方法枚举"""
    ZSCORE = "zscore"
    RANK = "rank"
    SIGN = "sign"
    MINMAX = "minmax"
    ROBUST = "robust"


class FactorStandardizer:
    """因子标准化处理器"""
    
    def __init__(self, method: StandardizationMethod = StandardizationMethod.ZSCORE):
        self.method = method
    
    def standardize_single_factor(self, factor_values: pd.Series, 
                                 lookback: int = 252) -> pd.Series:
        """
        标准化单个因子
        
        Args:
            factor_values: 因子值序列
            lookback: 回看期数，用于计算统计量
            
        Returns:
            标准化后的因子值
        """
        if self.method == StandardizationMethod.ZSCORE:
            return self._zscore_standardize(factor_values, lookback)
        elif self.method == StandardizationMethod.RANK:
            return self._rank_standardize(factor_values, lookback)
        elif self.method == StandardizationMethod.SIGN:
            return self._sign_standardize(factor_values)
        elif self.method == StandardizationMethod.MINMAX:
            return self._minmax_standardize(factor_values, lookback)
        elif self.method == StandardizationMethod.ROBUST:
            return self._robust_standardize(factor_values, lookback)
        else:
            raise ValueError(f"不支持的标准化方法: {self.method}")
    
    def standardize_multiple_factors(self, factor_data: Dict[str, pd.Series], 
                                   lookback: int = 252) -> Dict[str, pd.Series]:
        """
        标准化多个因子
        
        Args:
            factor_data: 因子数据字典 {因子名: 因子值序列}
            lookback: 回看期数
            
        Returns:
            标准化后的因子数据字典
        """
        standardized_factors = {}
        
        for factor_name, factor_values in factor_data.items():
            standardized_factors[factor_name] = self.standardize_single_factor(
                factor_values, lookback
            )
        
        return standardized_factors
    
    def _zscore_standardize(self, factor_values: pd.Series, 
                           lookback: int) -> pd.Series:
        """Z-Score标准化"""
        rolling_mean = factor_values.rolling(window=lookback, min_periods=1).mean()
        rolling_std = factor_values.rolling(window=lookback, min_periods=1).std()
        
        # 避免除零
        rolling_std = rolling_std.replace(0, 1)
        
        return (factor_values - rolling_mean) / rolling_std
    
    def _rank_standardize(self, factor_values: pd.Series, 
                         lookback: int) -> pd.Series:
        """分位数排名标准化"""
        def rolling_rank(x):
            if len(x) < 2:
                return 0.5
            return (x.rank(pct=True).iloc[-1] - 0.5) * 2  # 转换为[-1, 1]
        
        return factor_values.rolling(window=lookback, min_periods=1).apply(rolling_rank)
    
    def _sign_standardize(self, factor_values: pd.Series) -> pd.Series:
        """符号函数标准化"""
        return np.sign(factor_values)
    
    def _minmax_standardize(self, factor_values: pd.Series, 
                           lookback: int) -> pd.Series:
        """Min-Max标准化"""
        rolling_min = factor_values.rolling(window=lookback, min_periods=1).min()
        rolling_max = factor_values.rolling(window=lookback, min_periods=1).max()
        
        # 避免除零
        denominator = rolling_max - rolling_min
        denominator = denominator.replace(0, 1)
        
        return (factor_values - rolling_min) / denominator
    
    def _robust_standardize(self, factor_values: pd.Series, 
                           lookback: int) -> pd.Series:
        """稳健标准化（基于中位数和MAD）"""
        def rolling_robust_stats(x):
            if len(x) < 2:
                return pd.Series({'median': x.iloc[0], 'mad': 1})
            
            median = x.median()
            mad = np.median(np.abs(x - median))
            mad = mad if mad > 0 else 1  # 避免除零
            
            return pd.Series({'median': median, 'mad': mad})
        
        stats = factor_values.rolling(window=lookback, min_periods=1).apply(
            rolling_robust_stats, raw=False
        )
        
        return (factor_values - stats['median']) / stats['mad']


class MultiFactorStrategy:
    """多因子策略处理器"""
    
    def __init__(self, standardization_method: StandardizationMethod = StandardizationMethod.ZSCORE):
        self.standardizer = FactorStandardizer(standardization_method)
        self.method = standardization_method
    
    def combine_factors(self, factor_data: Dict[str, pd.Series], 
                       weights: Dict[str, float],
                       lookback: int = 252) -> pd.Series:
        """
        组合多个因子
        
        Args:
            factor_data: 因子数据字典
            weights: 权重字典
            lookback: 标准化回看期数
            
        Returns:
            组合后的因子得分
        """
        # 标准化所有因子
        standardized_factors = self.standardizer.standardize_multiple_factors(
            factor_data, lookback
        )
        
        # 加权组合
        combined_score = pd.Series(0.0, index=list(factor_data.values())[0].index)
        
        for factor_name, factor_values in standardized_factors.items():
            if factor_name in weights:
                combined_score += factor_values * weights[factor_name]
        
        return combined_score
    
    def get_factor_contribution(self, factor_data: Dict[str, pd.Series],
                               weights: Dict[str, float],
                               lookback: int = 252) -> Dict[str, pd.Series]:
        """
        获取各因子的贡献度
        
        Args:
            factor_data: 因子数据字典
            weights: 权重字典
            lookback: 标准化回看期数
            
        Returns:
            各因子贡献度字典
        """
        standardized_factors = self.standardizer.standardize_multiple_factors(
            factor_data, lookback
        )
        
        contributions = {}
        for factor_name, factor_values in standardized_factors.items():
            if factor_name in weights:
                contributions[factor_name] = factor_values * weights[factor_name]
        
        return contributions


# 使用示例
def example_usage():
    """使用示例"""
    
    # 1. 创建标准化处理器
    standardizer = FactorStandardizer(StandardizationMethod.ZSCORE)
    
    # 2. 模拟因子数据
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    ma50_factor = pd.Series(np.random.randn(100), index=dates)
    pe_factor = pd.Series(-np.random.uniform(10, 30, 100), index=dates)
    
    factor_data = {
        'MA50': ma50_factor,
        'PE': pe_factor
    }
    
    # 3. 标准化因子
    standardized_factors = standardizer.standardize_multiple_factors(factor_data)
    
    # 4. 创建多因子策略
    strategy = MultiFactorStrategy(StandardizationMethod.ZSCORE)
    weights = {'MA50': 0.6, 'PE': 0.4}
    
    # 5. 组合因子
    combined_score = strategy.combine_factors(factor_data, weights)
    
    print("标准化后的因子:")
    for name, values in standardized_factors.items():
        print(f"{name}: 均值={values.mean():.3f}, 标准差={values.std():.3f}")
    
    print(f"\n组合得分: 均值={combined_score.mean():.3f}, 标准差={combined_score.std():.3f}")


if __name__ == "__main__":
    example_usage() 