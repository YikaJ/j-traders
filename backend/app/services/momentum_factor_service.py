"""
动量类因子计算服务
提供RSI、MACD、KDJ、随机振荡器等动量技术指标
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union
import logging
from .builtin_factor_service import BuiltinFactorCalculator, FactorCategory

logger = logging.getLogger(__name__)


# =============================================================================
# 动量类因子计算器
# =============================================================================

class RelativeStrengthIndexCalculator(BuiltinFactorCalculator):
    """相对强弱指数(RSI)计算器"""
    
    def __init__(self, period: int = 14):
        super().__init__(
            factor_id=f"rsi_{period}",
            name=f"RSI{period}",
            display_name=f"{period}日相对强弱指数",
            category=FactorCategory.MOMENTUM,
            description=f"计算{period}日RSI，用于判断超买超卖状态，值域0-100"
        )
        self.default_parameters = {
            "period": {"type": "integer", "minimum": 2, "maximum": 100, "default": period}
        }
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        """计算RSI指标"""
        self.validate_data(data)
        
        period = parameters.get("period", 14) if parameters else 14
        
        # 计算价格变化
        price_diff = data['close'].diff()
        
        # 分离涨跌
        gains = price_diff.where(price_diff > 0, 0)
        losses = -price_diff.where(price_diff < 0, 0)
        
        # 计算平均涨跌幅
        avg_gains = gains.rolling(window=period, min_periods=1).mean()
        avg_losses = losses.rolling(window=period, min_periods=1).mean()
        
        # 计算相对强度
        rs = avg_gains / avg_losses
        
        # 计算RSI
        rsi = 100 - (100 / (1 + rs))
        
        # 处理无穷大和NaN值
        rsi = rsi.fillna(50)  # 初始值设为中性50
        
        return rsi


class MACDCalculator(BuiltinFactorCalculator):
    """MACD指标计算器"""
    
    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        super().__init__(
            factor_id="macd",
            name="MACD",
            display_name="指数平滑移动平均收敛散度",
            category=FactorCategory.MOMENTUM,
            description="计算MACD指标，包含DIF线、DEA线和柱状图"
        )
        self.default_parameters = {
            "fast_period": {"type": "integer", "minimum": 1, "maximum": 50, "default": fast_period},
            "slow_period": {"type": "integer", "minimum": 2, "maximum": 100, "default": slow_period},
            "signal_period": {"type": "integer", "minimum": 1, "maximum": 50, "default": signal_period}
        }
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.DataFrame:
        """计算MACD指标"""
        self.validate_data(data)
        
        fast_period = parameters.get("fast_period", 12) if parameters else 12
        slow_period = parameters.get("slow_period", 26) if parameters else 26
        signal_period = parameters.get("signal_period", 9) if parameters else 9
        
        if fast_period >= slow_period:
            raise ValueError("快线周期必须小于慢线周期")
        
        # 计算快线和慢线EMA
        ema_fast = data['close'].ewm(span=fast_period).mean()
        ema_slow = data['close'].ewm(span=slow_period).mean()
        
        # 计算DIF线（快线-慢线）
        macd_line = ema_fast - ema_slow
        
        # 计算DEA线（信号线）
        signal_line = macd_line.ewm(span=signal_period).mean()
        
        # 计算MACD柱状图
        histogram = macd_line - signal_line
        
        return pd.DataFrame({
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        })


class KDJCalculator(BuiltinFactorCalculator):
    """KDJ随机指标计算器"""
    
    def __init__(self, k_period: int = 9, d_period: int = 3, j_factor: int = 3):
        super().__init__(
            factor_id="kdj",
            name="KDJ",
            display_name="随机指标",
            category=FactorCategory.MOMENTUM,
            description="计算KDJ随机指标，用于判断超买超卖和趋势转折"
        )
        self.input_fields = ["close", "high", "low"]
        self.default_parameters = {
            "k_period": {"type": "integer", "minimum": 1, "maximum": 50, "default": k_period},
            "d_period": {"type": "integer", "minimum": 1, "maximum": 20, "default": d_period},
            "j_factor": {"type": "integer", "minimum": 1, "maximum": 10, "default": j_factor}
        }
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.DataFrame:
        """计算KDJ指标"""
        self.validate_data(data)
        
        k_period = parameters.get("k_period", 9) if parameters else 9
        d_period = parameters.get("d_period", 3) if parameters else 3
        j_factor = parameters.get("j_factor", 3) if parameters else 3
        
        # 计算最高价和最低价的滚动窗口
        high_n = data['high'].rolling(window=k_period).max()
        low_n = data['low'].rolling(window=k_period).min()
        
        # 计算RSV（未成熟随机值）
        rsv = ((data['close'] - low_n) / (high_n - low_n)) * 100
        rsv = rsv.fillna(50)  # 填充NaN值
        
        # 计算K值（使用指数移动平均）
        k_values = rsv.ewm(alpha=1/d_period, adjust=False).mean()
        
        # 计算D值（K值的指数移动平均）
        d_values = k_values.ewm(alpha=1/d_period, adjust=False).mean()
        
        # 计算J值
        j_values = j_factor * k_values - (j_factor - 1) * d_values
        
        return pd.DataFrame({
            'k': k_values,
            'd': d_values,
            'j': j_values
        })


class StochasticOscillatorCalculator(BuiltinFactorCalculator):
    """随机振荡器计算器"""
    
    def __init__(self, k_period: int = 14, d_period: int = 3):
        super().__init__(
            factor_id="stochastic",
            name="STOCH",
            display_name="随机振荡器",
            category=FactorCategory.MOMENTUM,
            description="计算随机振荡器%K和%D线，用于识别超买超卖条件"
        )
        self.input_fields = ["close", "high", "low"]
        self.default_parameters = {
            "k_period": {"type": "integer", "minimum": 1, "maximum": 50, "default": k_period},
            "d_period": {"type": "integer", "minimum": 1, "maximum": 20, "default": d_period}
        }
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.DataFrame:
        """计算随机振荡器"""
        self.validate_data(data)
        
        k_period = parameters.get("k_period", 14) if parameters else 14
        d_period = parameters.get("d_period", 3) if parameters else 3
        
        # 计算最高价和最低价
        high_n = data['high'].rolling(window=k_period).max()
        low_n = data['low'].rolling(window=k_period).min()
        
        # 计算%K
        k_percent = ((data['close'] - low_n) / (high_n - low_n)) * 100
        k_percent = k_percent.fillna(50)
        
        # 计算%D（%K的移动平均）
        d_percent = k_percent.rolling(window=d_period).mean()
        
        return pd.DataFrame({
            'percent_k': k_percent,
            'percent_d': d_percent
        })


class WilliamsRCalculator(BuiltinFactorCalculator):
    """威廉指标(%R)计算器"""
    
    def __init__(self, period: int = 14):
        super().__init__(
            factor_id=f"williams_r_{period}",
            name=f"%R{period}",
            display_name=f"{period}日威廉指标",
            category=FactorCategory.MOMENTUM,
            description=f"计算{period}日威廉%R指标，用于判断超买超卖，值域-100到0"
        )
        self.input_fields = ["close", "high", "low"]
        self.default_parameters = {
            "period": {"type": "integer", "minimum": 1, "maximum": 100, "default": period}
        }
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        """计算威廉%R指标"""
        self.validate_data(data)
        
        period = parameters.get("period", 14) if parameters else 14
        
        # 计算周期内最高价和最低价
        high_n = data['high'].rolling(window=period).max()
        low_n = data['low'].rolling(window=period).min()
        
        # 计算威廉%R
        williams_r = ((high_n - data['close']) / (high_n - low_n)) * -100
        williams_r = williams_r.fillna(-50)  # 填充为中性值
        
        return williams_r


class CommodityChannelIndexCalculator(BuiltinFactorCalculator):
    """商品通道指数(CCI)计算器"""
    
    def __init__(self, period: int = 20):
        super().__init__(
            factor_id=f"cci_{period}",
            name=f"CCI{period}",
            display_name=f"{period}日商品通道指数",
            category=FactorCategory.MOMENTUM,
            description=f"计算{period}日CCI指标，用于识别循环性买卖信号"
        )
        self.input_fields = ["close", "high", "low"]
        self.default_parameters = {
            "period": {"type": "integer", "minimum": 1, "maximum": 100, "default": period}
        }
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        """计算CCI指标"""
        self.validate_data(data)
        
        period = parameters.get("period", 20) if parameters else 20
        
        # 计算典型价格（TP）
        typical_price = (data['high'] + data['low'] + data['close']) / 3
        
        # 计算移动平均
        sma_tp = typical_price.rolling(window=period).mean()
        
        # 计算平均绝对偏差
        mad = typical_price.rolling(window=period).apply(
            lambda x: np.mean(np.abs(x - x.mean())), raw=True
        )
        
        # 计算CCI
        cci = (typical_price - sma_tp) / (0.015 * mad)
        cci = cci.fillna(0)
        
        return cci


class MomentumCalculator(BuiltinFactorCalculator):
    """动量指标计算器"""
    
    def __init__(self, period: int = 10):
        super().__init__(
            factor_id=f"momentum_{period}",
            name=f"MOM{period}",
            display_name=f"{period}日动量指标",
            category=FactorCategory.MOMENTUM,
            description=f"计算{period}日价格动量，当前价格与{period}天前价格的比率"
        )
        self.default_parameters = {
            "period": {"type": "integer", "minimum": 1, "maximum": 100, "default": period}
        }
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        """计算动量指标"""
        self.validate_data(data)
        
        period = parameters.get("period", 10) if parameters else 10
        
        # 计算动量：当前价格 / period天前价格
        momentum = data['close'] / data['close'].shift(period)
        
        return momentum.fillna(1.0)  # 缺失值填充为1（无变化）


class RateOfChangeCalculator(BuiltinFactorCalculator):
    """变化率(ROC)计算器"""
    
    def __init__(self, period: int = 12):
        super().__init__(
            factor_id=f"roc_{period}",
            name=f"ROC{period}",
            display_name=f"{period}日变化率",
            category=FactorCategory.MOMENTUM,
            description=f"计算{period}日价格变化率，以百分比表示"
        )
        self.default_parameters = {
            "period": {"type": "integer", "minimum": 1, "maximum": 100, "default": period}
        }
    
    def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> pd.Series:
        """计算变化率指标"""
        self.validate_data(data)
        
        period = parameters.get("period", 12) if parameters else 12
        
        # 计算变化率：(当前价格 - period天前价格) / period天前价格 * 100
        roc = ((data['close'] - data['close'].shift(period)) / data['close'].shift(period)) * 100
        
        return roc.fillna(0.0)  # 缺失值填充为0


# =============================================================================
# 动量类因子注册表
# =============================================================================

class MomentumFactorRegistry:
    """动量类因子注册表"""
    
    def __init__(self):
        self.calculators = {}
        self._register_default_factors()
    
    def _register_default_factors(self):
        """注册默认动量类因子"""
        # 注册不同周期的RSI
        for period in [6, 14, 21]:
            calc = RelativeStrengthIndexCalculator(period)
            self.calculators[calc.factor_id] = calc
        
        # 注册MACD（默认参数和快速参数）
        self.calculators["macd"] = MACDCalculator()
        self.calculators["macd_fast"] = MACDCalculator(fast_period=8, slow_period=21, signal_period=5)
        
        # 注册KDJ
        self.calculators["kdj"] = KDJCalculator()
        self.calculators["kdj_fast"] = KDJCalculator(k_period=5, d_period=2)
        
        # 注册随机振荡器
        self.calculators["stochastic"] = StochasticOscillatorCalculator()
        self.calculators["stochastic_fast"] = StochasticOscillatorCalculator(k_period=5, d_period=2)
        
        # 注册威廉指标
        for period in [10, 14, 20]:
            calc = WilliamsRCalculator(period)
            self.calculators[calc.factor_id] = calc
        
        # 注册CCI
        for period in [14, 20]:
            calc = CommodityChannelIndexCalculator(period)
            self.calculators[calc.factor_id] = calc
        
        # 注册动量指标
        for period in [5, 10, 20]:
            calc = MomentumCalculator(period)
            self.calculators[calc.factor_id] = calc
        
        # 注册变化率
        for period in [6, 12, 21]:
            calc = RateOfChangeCalculator(period)
            self.calculators[calc.factor_id] = calc
    
    def get_calculator(self, factor_id: str) -> Optional[BuiltinFactorCalculator]:
        """获取因子计算器"""
        return self.calculators.get(factor_id)
    
    def list_factors(self) -> List[Dict[str, Any]]:
        """列出所有动量类因子"""
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
# 动量类因子服务
# =============================================================================

class MomentumFactorService:
    """动量类因子服务"""
    
    def __init__(self):
        self.registry = MomentumFactorRegistry()
    
    def get_available_factors(self) -> List[Dict[str, Any]]:
        """获取可用的动量类因子列表"""
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
    
    def get_signal_analysis(self, factor_id: str, data: pd.DataFrame, 
                           parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """获取信号分析"""
        result = self.calculate_single_factor(factor_id, data, parameters)
        
        if isinstance(result, pd.Series):
            latest_value = result.iloc[-1] if len(result) > 0 else None
            signal_analysis = self._analyze_single_signal(factor_id, latest_value)
        else:
            # 对于多列结果，分析主要指标
            latest_values = result.iloc[-1].to_dict() if len(result) > 0 else {}
            signal_analysis = self._analyze_multi_signal(factor_id, latest_values)
        
        return {
            "factor_id": factor_id,
            "latest_values": latest_values if isinstance(result, pd.DataFrame) else {"value": latest_value},
            "signal": signal_analysis.get("signal", "neutral"),
            "strength": signal_analysis.get("strength", "medium"),
            "description": signal_analysis.get("description", ""),
            "recommendation": signal_analysis.get("recommendation", "")
        }
    
    def _analyze_single_signal(self, factor_id: str, value: float) -> Dict[str, str]:
        """分析单一数值信号"""
        if value is None or np.isnan(value):
            return {"signal": "neutral", "strength": "medium", "description": "数据不足", "recommendation": "等待更多数据"}
        
        # RSI信号分析
        if "rsi" in factor_id:
            if value >= 70:
                return {"signal": "sell", "strength": "strong", "description": "RSI超买", "recommendation": "考虑卖出"}
            elif value <= 30:
                return {"signal": "buy", "strength": "strong", "description": "RSI超卖", "recommendation": "考虑买入"}
            elif value >= 60:
                return {"signal": "sell", "strength": "medium", "description": "RSI偏高", "recommendation": "谨慎观察"}
            elif value <= 40:
                return {"signal": "buy", "strength": "medium", "description": "RSI偏低", "recommendation": "关注买入机会"}
        
        # 威廉指标分析
        elif "williams_r" in factor_id:
            if value <= -80:
                return {"signal": "buy", "strength": "strong", "description": "%R超卖", "recommendation": "考虑买入"}
            elif value >= -20:
                return {"signal": "sell", "strength": "strong", "description": "%R超买", "recommendation": "考虑卖出"}
        
        # 动量指标分析
        elif "momentum" in factor_id:
            if value > 1.05:
                return {"signal": "buy", "strength": "medium", "description": "正动量强劲", "recommendation": "趋势向上"}
            elif value < 0.95:
                return {"signal": "sell", "strength": "medium", "description": "负动量明显", "recommendation": "趋势向下"}
        
        return {"signal": "neutral", "strength": "medium", "description": "中性信号", "recommendation": "继续观察"}
    
    def _analyze_multi_signal(self, factor_id: str, values: Dict[str, float]) -> Dict[str, str]:
        """分析多数值信号"""
        # MACD信号分析
        if factor_id == "macd":
            macd_val = values.get("macd", 0)
            signal_val = values.get("signal", 0)
            histogram = values.get("histogram", 0)
            
            if macd_val > signal_val and histogram > 0:
                return {"signal": "buy", "strength": "strong", "description": "MACD金叉且柱状图为正", "recommendation": "强烈买入信号"}
            elif macd_val < signal_val and histogram < 0:
                return {"signal": "sell", "strength": "strong", "description": "MACD死叉且柱状图为负", "recommendation": "强烈卖出信号"}
        
        # KDJ信号分析
        elif factor_id in ["kdj", "kdj_fast"]:
            k_val = values.get("k", 50)
            d_val = values.get("d", 50)
            j_val = values.get("j", 50)
            
            if k_val > d_val and k_val < 20:
                return {"signal": "buy", "strength": "strong", "description": "KDJ低位金叉", "recommendation": "买入信号"}
            elif k_val < d_val and k_val > 80:
                return {"signal": "sell", "strength": "strong", "description": "KDJ高位死叉", "recommendation": "卖出信号"}
        
        return {"signal": "neutral", "strength": "medium", "description": "中性信号", "recommendation": "继续观察"}


# 全局动量因子服务实例
momentum_factor_service = MomentumFactorService()