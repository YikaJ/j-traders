"""
价量类因子计算服务
提供OBV、MFI、VPT、成交量比率等价量技术指标
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union
import logging
from .builtin_factor_service import BuiltinFactorCalculator, FactorCategory

logger = logging.getLogger(__name__)


# =============================================================================
# 价量类因子计算器
# =============================================================================

class OnBalanceVolumeCalculator(BuiltinFactorCalculator):
    """平衡成交量(OBV)计算器"""
    
    def __init__(self):
        super().__init__(
            factor_id="obv",
            name="OBV",
            display_name="平衡成交量",
            category=FactorCategory.VOLUME,
            description="计算OBV指标，通过价格变化方向累积成交量，用于确认价格趋势"
        )
        self.input_fields = ["close", "volume"]
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        """计算OBV指标"""
        self.validate_data(data)
        
        # 计算价格变化方向
        price_change = data['close'].diff()
        
        # 根据价格变化确定成交量符号
        volume_direction = pd.Series(0, index=data.index)
        volume_direction[price_change > 0] = 1   # 上涨日
        volume_direction[price_change < 0] = -1  # 下跌日
        volume_direction[price_change == 0] = 0  # 平盘日
        
        # 计算带方向的成交量
        signed_volume = data['volume'] * volume_direction
        
        # 累积求和得到OBV
        obv = signed_volume.cumsum()
        
        return obv


class MoneyFlowIndexCalculator(BuiltinFactorCalculator):
    """资金流量指标(MFI)计算器"""
    
    def __init__(self, period: int = 14):
        super().__init__(
            factor_id=f"mfi_{period}",
            name=f"MFI{period}",
            display_name=f"{period}日资金流量指标",
            category=FactorCategory.VOLUME,
            description=f"计算{period}日MFI指标，结合价格和成交量判断买卖压力，值域0-100"
        )
        self.input_fields = ["close", "high", "low", "volume"]
        self.default_parameters = {
            "period": {"type": "integer", "minimum": 1, "maximum": 100, "default": period}
        }
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        """计算MFI指标"""
        self.validate_data(data)
        
        period = parameters.get("period", 14) if parameters else 14
        
        # 计算典型价格
        typical_price = (data['high'] + data['low'] + data['close']) / 3
        
        # 计算资金流量
        money_flow = typical_price * data['volume']
        
        # 计算典型价格变化
        tp_change = typical_price.diff()
        
        # 分离正负资金流量
        positive_mf = money_flow.where(tp_change > 0, 0)
        negative_mf = money_flow.where(tp_change < 0, 0)
        
        # 计算周期内的正负资金流量总和
        positive_mf_sum = positive_mf.rolling(window=period, min_periods=1).sum()
        negative_mf_sum = negative_mf.rolling(window=period, min_periods=1).sum()
        
        # 计算资金流量比率
        money_flow_ratio = positive_mf_sum / negative_mf_sum
        
        # 计算MFI
        mfi = 100 - (100 / (1 + money_flow_ratio))
        
        # 处理除零和无穷大情况
        mfi = mfi.fillna(50)  # 填充为中性值
        
        return mfi


class VolumeRatioCalculator(BuiltinFactorCalculator):
    """成交量比率计算器"""
    
    def __init__(self, period: int = 5):
        super().__init__(
            factor_id=f"volume_ratio_{period}",
            name=f"VR{period}",
            display_name=f"{period}日成交量比率",
            category=FactorCategory.VOLUME,
            description=f"计算{period}日成交量比率，当日成交量与均值的比率"
        )
        self.input_fields = ["volume"]
        self.default_parameters = {
            "period": {"type": "integer", "minimum": 1, "maximum": 50, "default": period}
        }
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        """计算成交量比率"""
        self.validate_data(data)
        
        period = parameters.get("period", 5) if parameters else 5
        
        # 计算成交量移动平均
        volume_ma = data['volume'].rolling(window=period, min_periods=1).mean()
        
        # 计算成交量比率
        volume_ratio = data['volume'] / volume_ma
        
        return volume_ratio.fillna(1.0)


class VolumeRelativeRatioCalculator(BuiltinFactorCalculator):
    """相对成交量比率(VRR)计算器"""
    
    def __init__(self, period: int = 10):
        super().__init__(
            factor_id=f"vrr_{period}",
            name=f"VRR{period}",
            display_name=f"{period}日相对成交量比率", 
            category=FactorCategory.VOLUME,
            description=f"计算{period}日上涨和下跌日成交量的比率"
        )
        self.input_fields = ["close", "volume"]
        self.default_parameters = {
            "period": {"type": "integer", "minimum": 1, "maximum": 100, "default": period}
        }
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        """计算相对成交量比率"""
        self.validate_data(data)
        
        period = parameters.get("period", 10) if parameters else 10
        
        # 计算价格变化
        price_change = data['close'].diff()
        
        # 分离上涨和下跌日的成交量
        up_volume = data['volume'].where(price_change > 0, 0)
        down_volume = data['volume'].where(price_change < 0, 0)
        
        # 计算滚动窗口内的成交量总和
        up_volume_sum = up_volume.rolling(window=period, min_periods=1).sum()
        down_volume_sum = down_volume.rolling(window=period, min_periods=1).sum()
        
        # 计算比率
        vrr = up_volume_sum / (down_volume_sum + 1e-8)  # 避免除零
        
        return vrr


class VolumePriceTrendCalculator(BuiltinFactorCalculator):
    """量价趋势指标(VPT)计算器"""
    
    def __init__(self):
        super().__init__(
            factor_id="vpt",
            name="VPT",
            display_name="量价趋势指标",
            category=FactorCategory.VOLUME,
            description="计算VPT指标，基于价格变化百分比加权的累积成交量"
        )
        self.input_fields = ["close", "volume"]
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        """计算VPT指标"""
        self.validate_data(data)
        
        # 计算价格变化百分比
        price_change_pct = data['close'].pct_change()
        
        # 计算加权成交量
        weighted_volume = data['volume'] * price_change_pct
        
        # 累积求和
        vpt = weighted_volume.cumsum()
        
        return vpt.fillna(0)


class AccumulationDistributionCalculator(BuiltinFactorCalculator):
    """累积/分布线(A/D)计算器"""
    
    def __init__(self):
        super().__init__(
            factor_id="ad_line",
            name="A/D",
            display_name="累积分布线",
            category=FactorCategory.VOLUME,
            description="计算A/D线，评估资金流入流出情况"
        )
        self.input_fields = ["close", "high", "low", "volume"]
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        """计算A/D线"""
        self.validate_data(data)
        
        # 计算多空比率
        # CLV = [(Close - Low) - (High - Close)] / (High - Low)
        clv = ((data['close'] - data['low']) - (data['high'] - data['close'])) / (data['high'] - data['low'])
        
        # 处理high = low的情况
        clv = clv.fillna(0)
        
        # 计算资金流量乘数
        money_flow_multiplier = clv
        
        # 计算资金流量
        money_flow_volume = money_flow_multiplier * data['volume']
        
        # 累积求和得到A/D线
        ad_line = money_flow_volume.cumsum()
        
        return ad_line


class ChaikinOscillatorCalculator(BuiltinFactorCalculator):
    """佳庆振荡器计算器"""
    
    def __init__(self, fast_period: int = 3, slow_period: int = 10):
        super().__init__(
            factor_id="chaikin_osc",
            name="CHO",
            display_name="佳庆振荡器",
            category=FactorCategory.VOLUME,
            description="计算佳庆振荡器，A/D线的快慢线差值"
        )
        self.input_fields = ["close", "high", "low", "volume"]
        self.default_parameters = {
            "fast_period": {"type": "integer", "minimum": 1, "maximum": 20, "default": fast_period},
            "slow_period": {"type": "integer", "minimum": 2, "maximum": 50, "default": slow_period}
        }
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        """计算佳庆振荡器"""
        self.validate_data(data)
        
        fast_period = parameters.get("fast_period", 3) if parameters else 3
        slow_period = parameters.get("slow_period", 10) if parameters else 10
        
        if fast_period >= slow_period:
            raise ValueError("快线周期必须小于慢线周期")
        
        # 先计算A/D线
        ad_calc = AccumulationDistributionCalculator()
        ad_line = ad_calc.calculate(data)
        
        # 计算快线和慢线EMA
        fast_ema = ad_line.ewm(span=fast_period).mean()
        slow_ema = ad_line.ewm(span=slow_period).mean()
        
        # 计算振荡器
        chaikin_osc = fast_ema - slow_ema
        
        return chaikin_osc


class VolumeWeightedAveragePriceCalculator(BuiltinFactorCalculator):
    """成交量加权平均价格(VWAP)计算器"""
    
    def __init__(self, period: int = 20):
        super().__init__(
            factor_id=f"vwap_{period}",
            name=f"VWAP{period}",
            display_name=f"{period}日成交量加权平均价格",
            category=FactorCategory.VOLUME,
            description=f"计算{period}日VWAP，反映平均成交价格"
        )
        self.input_fields = ["close", "high", "low", "volume"]
        self.default_parameters = {
            "period": {"type": "integer", "minimum": 1, "maximum": 100, "default": period}
        }
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        """计算VWAP"""
        self.validate_data(data)
        
        period = parameters.get("period", 20) if parameters else 20
        
        # 计算典型价格
        typical_price = (data['high'] + data['low'] + data['close']) / 3
        
        # 计算价格×成交量
        price_volume = typical_price * data['volume']
        
        # 计算滚动窗口内的总和
        pv_sum = price_volume.rolling(window=period, min_periods=1).sum()
        volume_sum = data['volume'].rolling(window=period, min_periods=1).sum()
        
        # 计算VWAP
        vwap = pv_sum / volume_sum
        
        return vwap


class VolumeOscillatorCalculator(BuiltinFactorCalculator):
    """成交量振荡器计算器"""
    
    def __init__(self, fast_period: int = 5, slow_period: int = 10):
        super().__init__(
            factor_id="volume_osc",
            name="VO",
            display_name="成交量振荡器",
            category=FactorCategory.VOLUME,
            description="计算成交量振荡器，成交量快慢线的差值百分比"
        )
        self.input_fields = ["volume"]
        self.default_parameters = {
            "fast_period": {"type": "integer", "minimum": 1, "maximum": 20, "default": fast_period},
            "slow_period": {"type": "integer", "minimum": 2, "maximum": 50, "default": slow_period}
        }
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        """计算成交量振荡器"""
        self.validate_data(data)
        
        fast_period = parameters.get("fast_period", 5) if parameters else 5
        slow_period = parameters.get("slow_period", 10) if parameters else 10
        
        if fast_period >= slow_period:
            raise ValueError("快线周期必须小于慢线周期")
        
        # 计算快线和慢线移动平均
        fast_ma = data['volume'].rolling(window=fast_period).mean()
        slow_ma = data['volume'].rolling(window=slow_period).mean()
        
        # 计算振荡器百分比
        volume_osc = ((fast_ma - slow_ma) / slow_ma) * 100
        
        return volume_osc.fillna(0)


# =============================================================================
# 价量类因子注册表
# =============================================================================

class VolumeFactorRegistry:
    """价量类因子注册表"""
    
    def __init__(self):
        self.calculators = {}
        self._register_default_factors()
    
    def _register_default_factors(self):
        """注册默认价量类因子"""
        # 注册OBV
        self.calculators["obv"] = OnBalanceVolumeCalculator()
        
        # 注册不同周期的MFI
        for period in [14, 21]:
            calc = MoneyFlowIndexCalculator(period)
            self.calculators[calc.factor_id] = calc
        
        # 注册不同周期的成交量比率
        for period in [5, 10, 20]:
            calc = VolumeRatioCalculator(period)
            self.calculators[calc.factor_id] = calc
        
        # 注册相对成交量比率
        for period in [10, 20]:
            calc = VolumeRelativeRatioCalculator(period)
            self.calculators[calc.factor_id] = calc
        
        # 注册VPT
        self.calculators["vpt"] = VolumePriceTrendCalculator()
        
        # 注册A/D线
        self.calculators["ad_line"] = AccumulationDistributionCalculator()
        
        # 注册佳庆振荡器
        self.calculators["chaikin_osc"] = ChaikinOscillatorCalculator()
        
        # 注册不同周期的VWAP
        for period in [10, 20, 50]:
            calc = VolumeWeightedAveragePriceCalculator(period)
            self.calculators[calc.factor_id] = calc
        
        # 注册成交量振荡器
        self.calculators["volume_osc"] = VolumeOscillatorCalculator()
        self.calculators["volume_osc_fast"] = VolumeOscillatorCalculator(fast_period=3, slow_period=8)
    
    def get_calculator(self, factor_id: str) -> Optional[BuiltinFactorCalculator]:
        """获取因子计算器"""
        return self.calculators.get(factor_id)
    
    def list_factors(self) -> List[Dict[str, Any]]:
        """列出所有价量类因子"""
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
# 价量类因子服务
# =============================================================================

class VolumeFactorService:
    """价量类因子服务"""
    
    def __init__(self):
        self.registry = VolumeFactorRegistry()
    
    def get_available_factors(self) -> List[Dict[str, Any]]:
        """获取可用的价量类因子列表"""
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
    
    def analyze_volume_strength(self, data: pd.DataFrame, 
                               recent_days: int = 5) -> Dict[str, Any]:
        """分析成交量强度"""
        if len(data) < recent_days:
            return {"error": "数据不足"}
        
        recent_data = data.tail(recent_days)
        
        # 计算平均成交量
        avg_volume = recent_data['volume'].mean()
        historical_avg = data['volume'].mean()
        
        # 计算成交量比率
        volume_ratio = avg_volume / historical_avg
        
        # 计算价量配合度
        price_changes = recent_data['close'].diff()
        volume_changes = recent_data['volume'].diff()
        
        # 计算价量相关性
        if len(price_changes) > 1:
            correlation = price_changes.corr(volume_changes)
        else:
            correlation = 0
        
        # 分析结果
        strength_level = "normal"
        if volume_ratio > 1.5:
            strength_level = "high"
        elif volume_ratio < 0.7:
            strength_level = "low"
        
        coordination = "good" if abs(correlation) > 0.3 else "poor"
        
        return {
            "volume_ratio": round(volume_ratio, 2),
            "strength_level": strength_level,
            "price_volume_correlation": round(correlation, 3) if not np.isnan(correlation) else 0,
            "coordination": coordination,
            "recent_avg_volume": int(avg_volume),
            "historical_avg_volume": int(historical_avg)
        }


# 全局价量因子服务实例
volume_factor_service = VolumeFactorService()