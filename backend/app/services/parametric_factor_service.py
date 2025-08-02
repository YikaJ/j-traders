"""
参数化因子计算服务
将重复的因子（如不同周期的移动平均线）统一为参数化版本
减少因子库的冗余，提高灵活性
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union
from abc import ABC, abstractmethod
from datetime import datetime
import logging

from .builtin_factor_service import BuiltinFactorCalculator, FactorCategory

logger = logging.getLogger(__name__)


class ParametricFactorCalculator(BuiltinFactorCalculator):
    """参数化因子计算器基类"""
    
    def __init__(self, factor_id: str, name: str, display_name: str, 
                 category: FactorCategory, description: str = ""):
        super().__init__(
            factor_id=factor_id,
            name=name,
            display_name=display_name,
            category=category,
            description=description
        )
        self.is_parametric = True


class MovingAverageCalculator(ParametricFactorCalculator):
    """通用移动平均线计算器"""
    
    def __init__(self):
        super().__init__(
            factor_id="moving_average",
            name="MovingAverage",
            display_name="移动平均线",
            category=FactorCategory.TREND,
            description="通用移动平均线因子，支持简单移动平均(SMA)和指数移动平均(EMA)两种类型"
        )
        self.default_parameters = {
            "period": {"type": "integer", "minimum": 1, "maximum": 252, "default": 20},
            "ma_type": {
                "type": "string", 
                "enum": ["sma", "ema"], 
                "default": "sma",
                "description": "移动平均类型: sma=简单移动平均, ema=指数移动平均"
            },
            "price_field": {
                "type": "string",
                "enum": ["close", "open", "high", "low"],
                "default": "close",
                "description": "价格字段选择"
            }
        }
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        """计算移动平均线"""
        self.validate_data(data)
        params = parameters or {}
        
        period = params.get("period", 20)
        ma_type = params.get("ma_type", "sma").lower()
        price_field = params.get("price_field", "close")
        
        if price_field not in data.columns:
            raise ValueError(f"价格字段 '{price_field}' 不存在")
        
        price_series = data[price_field]
        
        if ma_type == "sma":
            return price_series.rolling(window=period, min_periods=1).mean()
        elif ma_type == "ema":
            return price_series.ewm(span=period, adjust=False).mean()
        else:
            raise ValueError(f"不支持的移动平均类型: {ma_type}")


class BollingerBandsCalculator(ParametricFactorCalculator):
    """参数化布林带计算器"""
    
    def __init__(self):
        super().__init__(
            factor_id="bollinger_bands",
            name="BollingerBands",
            display_name="布林带",
            category=FactorCategory.TREND,
            description="布林带技术指标，包含上轨、中轨、下轨和布林带宽度"
        )
        self.default_parameters = {
            "period": {"type": "integer", "minimum": 5, "maximum": 100, "default": 20},
            "std_multiplier": {"type": "number", "minimum": 0.5, "maximum": 5.0, "default": 2.0},
            "price_field": {
                "type": "string",
                "enum": ["close", "open", "high", "low"],
                "default": "close"
            },
            "output_type": {
                "type": "string",
                "enum": ["upper", "middle", "lower", "width", "position"],
                "default": "position",
                "description": "输出类型: upper=上轨, middle=中轨, lower=下轨, width=带宽, position=价格位置百分比"
            }
        }
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        """计算布林带"""
        self.validate_data(data)
        params = parameters or {}
        
        period = params.get("period", 20)
        std_multiplier = params.get("std_multiplier", 2.0)
        price_field = params.get("price_field", "close")
        output_type = params.get("output_type", "position")
        
        price_series = data[price_field]
        
        # 计算中轨（移动平均）
        middle = price_series.rolling(window=period).mean()
        
        # 计算标准差
        std = price_series.rolling(window=period).std()
        
        # 计算上轨和下轨
        upper = middle + (std * std_multiplier)
        lower = middle - (std * std_multiplier)
        
        if output_type == "upper":
            return upper
        elif output_type == "middle":
            return middle
        elif output_type == "lower":
            return lower
        elif output_type == "width":
            return (upper - lower) / middle * 100
        elif output_type == "position":
            # 计算价格在布林带中的位置百分比
            return (price_series - lower) / (upper - lower) * 100
        else:
            raise ValueError(f"不支持的输出类型: {output_type}")


class RSICalculator(ParametricFactorCalculator):
    """相对强弱指数(RSI)计算器"""
    
    def __init__(self):
        super().__init__(
            factor_id="rsi",
            name="RSI",
            display_name="相对强弱指数",
            category=FactorCategory.MOMENTUM,
            description="相对强弱指数，衡量价格变动的速度和变化幅度"
        )
        self.default_parameters = {
            "period": {"type": "integer", "minimum": 2, "maximum": 100, "default": 14},
            "price_field": {
                "type": "string",
                "enum": ["close", "open", "high", "low"],
                "default": "close"
            },
            "smoothing_type": {
                "type": "string",
                "enum": ["sma", "ema"],
                "default": "ema",
                "description": "平滑方法: sma=简单移动平均, ema=指数移动平均"
            }
        }
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        """计算RSI"""
        self.validate_data(data)
        params = parameters or {}
        
        period = params.get("period", 14)
        price_field = params.get("price_field", "close")
        smoothing_type = params.get("smoothing_type", "ema")
        
        price_series = data[price_field]
        
        # 计算价格变化
        delta = price_series.diff()
        
        # 分离涨跌
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # 计算平均涨跌幅
        if smoothing_type == "sma":
            avg_gain = gain.rolling(window=period).mean()
            avg_loss = loss.rolling(window=period).mean()
        else:  # ema
            avg_gain = gain.ewm(span=period, adjust=False).mean()
            avg_loss = loss.ewm(span=period, adjust=False).mean()
        
        # 计算RS和RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi


class MACDCalculator(ParametricFactorCalculator):
    """MACD指标计算器"""
    
    def __init__(self):
        super().__init__(
            factor_id="macd",
            name="MACD",
            display_name="MACD指标",
            category=FactorCategory.MOMENTUM,
            description="移动平均聚散指标，包含MACD线、信号线和柱状图"
        )
        self.default_parameters = {
            "fast_period": {"type": "integer", "minimum": 5, "maximum": 50, "default": 12},
            "slow_period": {"type": "integer", "minimum": 10, "maximum": 100, "default": 26},
            "signal_period": {"type": "integer", "minimum": 3, "maximum": 20, "default": 9},
            "price_field": {
                "type": "string",
                "enum": ["close", "open", "high", "low"],
                "default": "close"
            },
            "output_type": {
                "type": "string",
                "enum": ["macd", "signal", "histogram"],
                "default": "macd",
                "description": "输出类型: macd=MACD线, signal=信号线, histogram=柱状图"
            }
        }
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        """计算MACD"""
        self.validate_data(data)
        params = parameters or {}
        
        fast_period = params.get("fast_period", 12)
        slow_period = params.get("slow_period", 26)
        signal_period = params.get("signal_period", 9)
        price_field = params.get("price_field", "close")
        output_type = params.get("output_type", "macd")
        
        price_series = data[price_field]
        
        # 计算快慢EMA
        ema_fast = price_series.ewm(span=fast_period).mean()
        ema_slow = price_series.ewm(span=slow_period).mean()
        
        # 计算MACD线
        macd_line = ema_fast - ema_slow
        
        # 计算信号线
        signal_line = macd_line.ewm(span=signal_period).mean()
        
        # 计算柱状图
        histogram = macd_line - signal_line
        
        if output_type == "macd":
            return macd_line
        elif output_type == "signal":
            return signal_line
        elif output_type == "histogram":
            return histogram
        else:
            raise ValueError(f"不支持的输出类型: {output_type}")


class VolumeAnalysisCalculator(ParametricFactorCalculator):
    """成交量分析因子"""
    
    def __init__(self):
        super().__init__(
            factor_id="volume_analysis",
            name="VolumeAnalysis", 
            display_name="成交量分析",
            category=FactorCategory.VOLUME,
            description="成交量相关分析指标，包含成交量比率、价量配合等"
        )
        self.default_parameters = {
            "period": {"type": "integer", "minimum": 5, "maximum": 100, "default": 20},
            "analysis_type": {
                "type": "string",
                "enum": ["volume_ratio", "price_volume", "obv", "volume_sma"],
                "default": "volume_ratio",
                "description": "分析类型: volume_ratio=量比, price_volume=价量配合, obv=能量潮, volume_sma=成交量均线"
            }
        }
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        """计算成交量分析指标"""
        self.validate_data(data)
        params = parameters or {}
        
        period = params.get("period", 20)
        analysis_type = params.get("analysis_type", "volume_ratio")
        
        if analysis_type == "volume_ratio":
            # 量比：当日成交量/平均成交量
            avg_volume = data['volume'].rolling(window=period).mean()
            return data['volume'] / avg_volume
            
        elif analysis_type == "price_volume":
            # 价量配合度：价格涨跌与成交量的相关性
            price_change = data['close'].pct_change()
            volume_change = data['volume'].pct_change()
            return price_change.rolling(window=period).corr(volume_change)
            
        elif analysis_type == "obv":
            # 能量潮(OBV)
            price_change = data['close'].diff()
            volume_direction = np.where(price_change > 0, data['volume'], 
                                      np.where(price_change < 0, -data['volume'], 0))
            return pd.Series(volume_direction, index=data.index).cumsum()
            
        elif analysis_type == "volume_sma":
            # 成交量移动平均
            return data['volume'].rolling(window=period).mean()
            
        else:
            raise ValueError(f"不支持的分析类型: {analysis_type}")


class ParametricFactorService:
    """参数化因子服务"""
    
    def __init__(self):
        # 注册所有参数化因子
        self.calculators = {
            "moving_average": MovingAverageCalculator(),
            "bollinger_bands": BollingerBandsCalculator(),
            "rsi": RSICalculator(),
            "macd": MACDCalculator(),
            "volume_analysis": VolumeAnalysisCalculator(),
        }
    
    def get_available_factors(self) -> List[Dict[str, Any]]:
        """获取所有可用的参数化因子"""
        factors = []
        for factor_id, calculator in self.calculators.items():
            factors.append({
                'factor_id': factor_id,
                'name': calculator.name,
                'display_name': calculator.display_name,
                'description': calculator.description,
                'input_fields': calculator.input_fields,
                'default_parameters': calculator.default_parameters,
                'category': calculator.category.value,
                'is_parametric': True
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
            'input_fields': calculator.input_fields,
            'default_parameters': calculator.default_parameters,
            'category': calculator.category.value,
            'is_parametric': True
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
            logger.error(f"计算参数化因子 {factor_id} 时出错: {e}")
            raise


# 创建全局参数化因子服务实例
parametric_factor_service = ParametricFactorService()