"""
Alpha101因子计算服务
基于WorldQuant 101 Formulaic Alphas论文实现
提供成熟的量化交易因子
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union
from abc import ABC, abstractmethod
from datetime import datetime
import logging
from enum import Enum

from .builtin_factor_service import BuiltinFactorCalculator, FactorCategory

logger = logging.getLogger(__name__)


class Alpha101Calculator(BuiltinFactorCalculator):
    """Alpha101因子计算器基类"""
    
    def __init__(self, alpha_id: str, name: str, display_name: str, 
                 description: str = "", formula: str = ""):
        super().__init__(
            factor_id=f"alpha101_{alpha_id}",
            name=name,
            display_name=display_name,
            category=FactorCategory.MOMENTUM,  # Alpha101主要是价量动量因子
            description=description
        )
        self.formula = formula
        self.input_fields = ["open", "high", "low", "close", "volume"]
        self.alpha_id = alpha_id
    
    def get_formula(self) -> str:
        """获取因子计算公式"""
        return self.formula


class Alpha001Calculator(Alpha101Calculator):
    """Alpha001: (rank(Ts_ArgMax(SignedPower(((returns < 0) ? stddev(returns, 20) : close), 2.), 5)) - 0.5)"""
    
    def __init__(self):
        super().__init__(
            alpha_id="001",
            name="Alpha001",
            display_name="Alpha001-价格波动调整因子",
            description="根据价格波动性调整的动量因子，考虑收益率的条件标准差",
            formula="(rank(Ts_ArgMax(SignedPower(((returns < 0) ? stddev(returns, 20) : close), 2.), 5)) - 0.5)"
        )
        self.default_parameters = {
            "lookback_period": {"type": "integer", "minimum": 1, "maximum": 60, "default": 20},
            "argmax_period": {"type": "integer", "minimum": 1, "maximum": 20, "default": 5}
        }
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        """计算Alpha001因子"""
        self.validate_data(data)
        params = parameters or {}
        lookback = params.get("lookback_period", 20)
        argmax_period = params.get("argmax_period", 5)
        
        # 计算收益率
        returns = data['close'].pct_change()
        
        # 计算条件值: 当returns < 0时用stddev，否则用close
        condition = returns < 0
        stddev_returns = returns.rolling(window=lookback).std()
        conditional_values = np.where(condition, stddev_returns, data['close'])
        
        # SignedPower(x, 2) = x^2 保持符号
        signed_power = np.sign(conditional_values) * (np.abs(conditional_values) ** 2)
        
        # 计算rolling window内的argmax
        result = []
        for i in range(len(signed_power)):
            if i >= argmax_period - 1:
                window_data = signed_power[i-argmax_period+1:i+1]
                if not pd.isna(window_data).all():
                    argmax_idx = np.nanargmax(window_data)
                    result.append(argmax_idx)
                else:
                    result.append(np.nan)
            else:
                result.append(np.nan)
        
        # 转换为rank并减去0.5
        result_series = pd.Series(result, index=data.index)
        rank_result = result_series.rank(pct=True) - 0.5
        
        return rank_result


class Alpha002Calculator(Alpha101Calculator):
    """Alpha002: (-1 * correlation(rank(delta(log(volume), 2)), rank(((close - open) / open)), 6))"""
    
    def __init__(self):
        super().__init__(
            alpha_id="002", 
            name="Alpha002",
            display_name="Alpha002-成交量价格背离因子",
            description="成交量变化与价格变化的负相关性，捕捉量价背离信号",
            formula="(-1 * correlation(rank(delta(log(volume), 2)), rank(((close - open) / open)), 6))"
        )
        self.default_parameters = {
            "correlation_period": {"type": "integer", "minimum": 3, "maximum": 30, "default": 6},
            "delta_period": {"type": "integer", "minimum": 1, "maximum": 10, "default": 2}
        }
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        """计算Alpha002因子"""
        self.validate_data(data)
        params = parameters or {}
        corr_period = params.get("correlation_period", 6)
        delta_period = params.get("delta_period", 2)
        
        # 计算log(volume)的差分
        log_volume = np.log(data['volume'].replace(0, np.nan))
        delta_log_volume = log_volume.diff(delta_period)
        rank_delta_log_volume = delta_log_volume.rank(pct=True)
        
        # 计算价格相对变化
        price_change = (data['close'] - data['open']) / data['open']
        rank_price_change = price_change.rank(pct=True)
        
        # 计算rolling correlation
        correlation = rank_delta_log_volume.rolling(window=corr_period).corr(rank_price_change)
        
        return -1 * correlation


class Alpha003Calculator(Alpha101Calculator):
    """Alpha003: (-1 * correlation(rank(open), rank(volume), 10))"""
    
    def __init__(self):
        super().__init__(
            alpha_id="003",
            name="Alpha003", 
            display_name="Alpha003-开盘价成交量反向因子",
            description="开盘价与成交量的负相关性，反向动量信号",
            formula="(-1 * correlation(rank(open), rank(volume), 10))"
        )
        self.default_parameters = {
            "correlation_period": {"type": "integer", "minimum": 5, "maximum": 30, "default": 10}
        }
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        """计算Alpha003因子"""
        self.validate_data(data)
        params = parameters or {}
        corr_period = params.get("correlation_period", 10)
        
        # 计算rank
        rank_open = data['open'].rank(pct=True)
        rank_volume = data['volume'].rank(pct=True)
        
        # 计算rolling correlation
        correlation = rank_open.rolling(window=corr_period).corr(rank_volume)
        
        return -1 * correlation


class Alpha004Calculator(Alpha101Calculator):
    """Alpha004: (-1 * Ts_Rank(rank(low), 9))"""
    
    def __init__(self):
        super().__init__(
            alpha_id="004",
            name="Alpha004",
            display_name="Alpha004-最低价时序排名因子", 
            description="最低价的时序排名，反向低价动量",
            formula="(-1 * Ts_Rank(rank(low), 9))"
        )
        self.default_parameters = {
            "ts_rank_period": {"type": "integer", "minimum": 5, "maximum": 20, "default": 9}
        }
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        """计算Alpha004因子"""
        self.validate_data(data)
        params = parameters or {}
        ts_rank_period = params.get("ts_rank_period", 9)
        
        # 计算cross-sectional rank
        rank_low = data['low'].rank(pct=True)
        
        # 计算time-series rank
        ts_rank = rank_low.rolling(window=ts_rank_period).rank(pct=True)
        
        return -1 * ts_rank


class Alpha006Calculator(Alpha101Calculator):
    """Alpha006: (-1 * correlation(open, volume, 10))"""
    
    def __init__(self):
        super().__init__(
            alpha_id="006",
            name="Alpha006",
            display_name="Alpha006-开盘量价反相关因子",
            description="开盘价与成交量的负相关，量价背离信号",
            formula="(-1 * correlation(open, volume, 10))"
        )
        self.default_parameters = {
            "correlation_period": {"type": "integer", "minimum": 5, "maximum": 30, "default": 10}
        }
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        """计算Alpha006因子"""
        self.validate_data(data)
        params = parameters or {}
        corr_period = params.get("correlation_period", 10)
        
        # 计算rolling correlation
        correlation = data['open'].rolling(window=corr_period).corr(data['volume'])
        
        return -1 * correlation


class Alpha101FactorService:
    """Alpha101因子服务"""
    
    def __init__(self):
        # 注册所有Alpha101因子
        self.calculators = {
            "alpha101_001": Alpha001Calculator(),
            "alpha101_002": Alpha002Calculator(), 
            "alpha101_003": Alpha003Calculator(),
            "alpha101_004": Alpha004Calculator(),
            "alpha101_006": Alpha006Calculator(),
        }
    
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


# 创建全局Alpha101因子服务实例
alpha101_factor_service = Alpha101FactorService()