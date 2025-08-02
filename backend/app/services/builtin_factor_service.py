"""
内置因子计算服务
提供20+常见技术指标的计算功能
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union
from abc import ABC, abstractmethod
from datetime import datetime
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class FactorCategory(str, Enum):
    """因子分类枚举"""
    TREND = "trend"           # 趋势类
    MOMENTUM = "momentum"     # 动量类  
    VOLUME = "volume"         # 价量类
    VOLATILITY = "volatility" # 波动率类
    VALUATION = "valuation"   # 估值类
    ALPHA101_EXTENDED = "alpha101_extended"  # Alpha101扩展因子
    ALPHA101_MORE_FACTORS = "alpha101_more_factors"  # Alpha101更多因子
    ALPHA101_PHASE2 = "alpha101_phase2"  # Alpha101第二阶段因子


class BuiltinFactorCalculator(ABC):
    """内置因子计算器抽象基类"""
    
    def __init__(self, factor_id: str, name: str, display_name: str, 
                 category: FactorCategory, description: str = ""):
        self.factor_id = factor_id
        self.name = name
        self.display_name = display_name
        self.category = category
        self.description = description
        self.input_fields = ["close"]  # 默认需要收盘价
        self.default_parameters = {}
    
    @abstractmethod
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        """
        计算因子值
        
        Args:
            data: 股票历史数据，包含 close, high, low, volume等字段
            parameters: 计算参数
            
        Returns:
            pd.Series: 因子值序列
        """
        pass
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """验证输入数据是否满足计算要求"""
        required_fields = self.get_required_fields()
        missing_fields = [field for field in required_fields if field not in data.columns]
        
        if missing_fields:
            raise ValueError(f"缺少必要字段: {missing_fields}")
            
        if len(data) == 0:
            raise ValueError("数据为空")
            
        return True
    
    def get_required_fields(self) -> List[str]:
        """获取计算所需的数据字段"""
        return self.input_fields
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        """获取参数验证schema"""
        return {
            "type": "object",
            "properties": self.default_parameters,
            "additionalProperties": False
        }


# =============================================================================
# 趋势类因子计算器
# =============================================================================

class SimpleMovingAverageCalculator(BuiltinFactorCalculator):
    """简单移动平均线计算器"""
    
    def __init__(self, period: int = 20):
        super().__init__(
            factor_id=f"sma_{period}",
            name=f"SMA{period}",
            display_name=f"{period}日简单移动平均",
            category=FactorCategory.TREND,
            description=f"计算{period}日简单移动平均线，用于判断价格趋势"
        )
        self.default_parameters = {
            "period": {"type": "integer", "minimum": 1, "maximum": 252, "default": period}
        }
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        """计算简单移动平均线"""
        self.validate_data(data)
        
        period = parameters.get("period", 20) if parameters else 20
        
        if len(data) < period:
            logger.warning(f"数据长度({len(data)})小于周期({period})，无法计算完整SMA")
        
        return data['close'].rolling(window=period, min_periods=1).mean()


class ExponentialMovingAverageCalculator(BuiltinFactorCalculator):
    """指数移动平均线计算器"""
    
    def __init__(self, period: int = 20):
        super().__init__(
            factor_id=f"ema_{period}",
            name=f"EMA{period}",
            display_name=f"{period}日指数移动平均",
            category=FactorCategory.TREND,
            description=f"计算{period}日指数移动平均线，对近期价格赋予更高权重"
        )
        self.default_parameters = {
            "period": {"type": "integer", "minimum": 1, "maximum": 252, "default": period}
        }
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        """计算指数移动平均线"""
        self.validate_data(data)
        
        period = parameters.get("period", 20) if parameters else 20
        return data['close'].ewm(span=period, adjust=False).mean()


class BollingerBandsCalculator(BuiltinFactorCalculator):
    """布林带计算器"""
    
    def __init__(self, period: int = 20, std_multiplier: float = 2.0):
        super().__init__(
            factor_id="bollinger_bands",
            name="BOLL",
            display_name="布林带",
            category=FactorCategory.TREND,
            description="计算布林带上轨、中轨、下轨，用于判断价格相对位置"
        )
        self.default_parameters = {
            "period": {"type": "integer", "minimum": 1, "maximum": 100, "default": period},
            "std_multiplier": {"type": "number", "minimum": 0.1, "maximum": 5.0, "default": std_multiplier}
        }
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.DataFrame:
        """计算布林带，返回包含upper, middle, lower的DataFrame"""
        self.validate_data(data)
        
        period = parameters.get("period", 20) if parameters else 20
        std_multiplier = parameters.get("std_multiplier", 2.0) if parameters else 2.0
        
        # 计算中轨（移动平均）
        middle = data['close'].rolling(window=period).mean()
        
        # 计算标准差
        std = data['close'].rolling(window=period).std()
        
        # 计算上轨和下轨
        upper = middle + (std * std_multiplier)
        lower = middle - (std * std_multiplier)
        
        # 计算价格在布林带中的位置 (0-1之间)
        position = (data['close'] - lower) / (upper - lower)
        
        return pd.DataFrame({
            'upper': upper,
            'middle': middle,
            'lower': lower,
            'position': position.fillna(0.5)  # 缺失值填充为中位
        })


class MovingAverageCrossoverCalculator(BuiltinFactorCalculator):
    """移动平均交叉计算器"""
    
    def __init__(self, fast_period: int = 5, slow_period: int = 20):
        super().__init__(
            factor_id="ma_crossover",
            name="MA_CROSS",
            display_name="移动平均交叉",
            category=FactorCategory.TREND,
            description="计算快线和慢线的交叉信号，1表示金叉，-1表示死叉，0表示无信号"
        )
        self.default_parameters = {
            "fast_period": {"type": "integer", "minimum": 1, "maximum": 50, "default": fast_period},
            "slow_period": {"type": "integer", "minimum": 2, "maximum": 200, "default": slow_period}
        }
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        """计算移动平均交叉信号"""
        self.validate_data(data)
        
        fast_period = parameters.get("fast_period", 5) if parameters else 5
        slow_period = parameters.get("slow_period", 20) if parameters else 20
        
        if fast_period >= slow_period:
            raise ValueError("快线周期必须小于慢线周期")
        
        # 计算快线和慢线
        fast_ma = data['close'].rolling(window=fast_period).mean()
        slow_ma = data['close'].rolling(window=slow_period).mean()
        
        # 计算交叉信号
        # 当前快线 > 慢线 and 前一日快线 <= 慢线 => 金叉 (1)
        # 当前快线 < 慢线 and 前一日快线 >= 慢线 => 死叉 (-1)
        
        current_above = fast_ma > slow_ma
        prev_above = (fast_ma > slow_ma).shift(1)
        
        crossover_signal = pd.Series(0, index=data.index)
        
        # 金叉：快线从下方穿越慢线
        golden_cross = current_above & ~prev_above
        crossover_signal[golden_cross] = 1
        
        # 死叉：快线从上方跌破慢线
        death_cross = ~current_above & prev_above
        crossover_signal[death_cross] = -1
        
        return crossover_signal


# =============================================================================
# 趋势类因子注册表
# =============================================================================

class TrendFactorRegistry:
    """趋势类因子注册表"""
    
    def __init__(self):
        self.calculators = {}
        self._register_default_factors()
    
    def _register_default_factors(self):
        """注册默认趋势类因子"""
        # 注册不同周期的SMA
        for period in [5, 10, 20, 50, 200]:
            calc = SimpleMovingAverageCalculator(period)
            self.calculators[calc.factor_id] = calc
        
        # 注册不同周期的EMA
        for period in [5, 10, 20, 50]:
            calc = ExponentialMovingAverageCalculator(period)
            self.calculators[calc.factor_id] = calc
        
        # 注册布林带
        self.calculators["bollinger_bands"] = BollingerBandsCalculator()
        
        # 注册移动平均交叉
        self.calculators["ma_crossover"] = MovingAverageCrossoverCalculator()
        
        # 注册不同参数的移动平均交叉
        self.calculators["ma_cross_5_10"] = MovingAverageCrossoverCalculator(5, 10)
        self.calculators["ma_cross_10_20"] = MovingAverageCrossoverCalculator(10, 20)
        self.calculators["ma_cross_20_50"] = MovingAverageCrossoverCalculator(20, 50)
    
    def get_calculator(self, factor_id: str) -> Optional[BuiltinFactorCalculator]:
        """获取因子计算器"""
        return self.calculators.get(factor_id)
    
    def list_factors(self) -> List[Dict[str, Any]]:
        """列出所有趋势类因子"""
        factors = []
        for calc in self.calculators.values():
            factors.append({
                "factor_id": calc.factor_id,
                "name": calc.name,
                "display_name": calc.display_name,
                "category": calc.category.value,
                "description": calc.description,
                "input_fields": calc.get_required_fields(),
                "default_parameters": calc.default_parameters
            })
        return factors
    
    def calculate_factor(self, factor_id: str, data: pd.DataFrame, 
                        parameters: Dict[str, Any] = None) -> Union[pd.Series, pd.DataFrame]:
        """计算指定因子"""
        calculator = self.get_calculator(factor_id)
        if not calculator:
            raise ValueError(f"未找到因子计算器: {factor_id}")
        
        try:
            return calculator.calculate(data, parameters)
        except Exception as e:
            logger.error(f"计算因子 {factor_id} 时出错: {e}")
            raise


# =============================================================================
# 趋势类因子服务
# =============================================================================

class TrendFactorService:
    """趋势类因子服务"""
    
    def __init__(self):
        self.registry = TrendFactorRegistry()
    
    def get_available_factors(self) -> List[Dict[str, Any]]:
        """获取可用的趋势类因子列表"""
        return self.registry.list_factors()
    
    def calculate_single_factor(self, factor_id: str, data: pd.DataFrame, 
                               parameters: Dict[str, Any] = None) -> Union[pd.Series, pd.DataFrame]:
        """计算单个因子"""
        return self.registry.calculate_factor(factor_id, data, parameters)
    
    def calculate_multiple_factors(self, factor_configs: List[Dict[str, Any]], 
                                  data: pd.DataFrame) -> Dict[str, Union[pd.Series, pd.DataFrame]]:
        """批量计算多个因子"""
        results = {}
        
        for config in factor_configs:
            factor_id = config.get("factor_id")
            parameters = config.get("parameters", {})
            
            try:
                result = self.calculate_single_factor(factor_id, data, parameters)
                results[factor_id] = result
            except Exception as e:
                logger.error(f"计算因子 {factor_id} 失败: {e}")
                results[factor_id] = None
        
        return results
    
    def get_factor_info(self, factor_id: str) -> Optional[Dict[str, Any]]:
        """获取因子信息"""
        calculator = self.registry.get_calculator(factor_id)
        if not calculator:
            return None
        
        return {
            "factor_id": calculator.factor_id,
            "name": calculator.name,
            "display_name": calculator.display_name,
            "category": calculator.category.value,
            "description": calculator.description,
            "input_fields": calculator.get_required_fields(),
            "default_parameters": calculator.default_parameters,
            "parameter_schema": calculator.get_parameter_schema()
        }
    
    def validate_parameters(self, factor_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """验证因子参数"""
        calculator = self.registry.get_calculator(factor_id)
        if not calculator:
            raise ValueError(f"未找到因子: {factor_id}")
        
        # 这里可以添加更复杂的参数验证逻辑
        # 目前简单返回参数（在实际项目中应该实现完整的JSON Schema验证）
        
        validated_params = {}
        default_params = calculator.default_parameters
        
        for key, schema in default_params.items():
            if key in parameters:
                value = parameters[key]
                # 简单的类型和范围验证
                if schema.get("type") == "integer":
                    if not isinstance(value, int):
                        raise ValueError(f"参数 {key} 必须是整数")
                    if "minimum" in schema and value < schema["minimum"]:
                        raise ValueError(f"参数 {key} 不能小于 {schema['minimum']}")
                    if "maximum" in schema and value > schema["maximum"]:
                        raise ValueError(f"参数 {key} 不能大于 {schema['maximum']}")
                elif schema.get("type") == "number":
                    if not isinstance(value, (int, float)):
                        raise ValueError(f"参数 {key} 必须是数字")
                    if "minimum" in schema and value < schema["minimum"]:
                        raise ValueError(f"参数 {key} 不能小于 {schema['minimum']}")
                    if "maximum" in schema and value > schema["maximum"]:
                        raise ValueError(f"参数 {key} 不能大于 {schema['maximum']}")
                
                validated_params[key] = value
            else:
                # 使用默认值
                if "default" in schema:
                    validated_params[key] = schema["default"]
        
        return validated_params


# 全局趋势因子服务实例
trend_factor_service = TrendFactorService()