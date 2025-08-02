"""
权重配置验证和优化服务
提供权重标准化、预设方案、优化建议等功能
"""

import math
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
import logging

from app.schemas.builtin_factors import (
    SelectedFactor, WeightPresetType, WeightPreset, 
    WeightOptimizationResult, FactorParameters
)
from .builtin_factor_engine import builtin_factor_engine

logger = logging.getLogger(__name__)


class WeightOptimizationService:
    """权重配置验证和优化服务"""
    
    def __init__(self):
        self.factor_engine = builtin_factor_engine
        self.preset_configs = self._initialize_weight_presets()
    
    def _initialize_weight_presets(self) -> List[WeightPreset]:
        """初始化权重预设配置"""
        return [
            WeightPreset(
                id="equal_weight",
                name="等权重",
                description="所有因子使用相等权重",
                preset_type=WeightPresetType.EQUAL,
                calculation_method="均匀分配权重给所有启用的因子",
                is_default=True
            ),
            WeightPreset(
                id="category_balanced",
                name="分类平衡",
                description="按因子分类均衡分配权重",
                preset_type=WeightPresetType.CUSTOM,
                calculation_method="同一分类内等权重，不同分类间平衡分配",
                is_default=False
            ),
            WeightPreset(
                id="inverse_volatility",
                name="反波动率加权",
                description="波动率越小权重越大",
                preset_type=WeightPresetType.INVERSE_VOLATILITY,
                calculation_method="基于因子历史波动率的倒数分配权重",
                is_default=False
            ),
            WeightPreset(
                id="risk_parity",
                name="风险平价",
                description="按风险贡献平均分配权重",
                preset_type=WeightPresetType.RISK_PARITY,
                calculation_method="使每个因子对总风险的贡献相等",
                is_default=False
            )
        ]
    
    def get_weight_presets(self) -> List[WeightPreset]:
        """获取权重预设列表"""
        return self.preset_configs
    
    def validate_weights(self, factors: List[SelectedFactor]) -> Dict[str, Any]:
        """验证因子权重配置"""
        errors = []
        warnings = []
        
        enabled_factors = [f for f in factors if f.is_enabled]
        
        if not enabled_factors:
            errors.append("至少需要启用一个因子")
            return {"is_valid": False, "errors": errors, "warnings": warnings}
        
        # 检查权重总和
        total_weight = sum(f.weight for f in enabled_factors)
        
        if total_weight <= 0:
            errors.append("权重总和必须大于0")
        elif abs(total_weight - 1.0) > 0.01:  # 允许1%误差
            if total_weight < 0.5:
                errors.append("权重总和过小，可能导致策略无效")
            elif total_weight > 1.5:
                errors.append("权重总和过大，建议调整至100%")
            else:
                warnings.append(f"权重总和为{total_weight:.1%}，建议调整至100%")
        
        # 检查单个权重
        for factor in enabled_factors:
            if factor.weight < 0:
                errors.append(f"因子 {factor.factor_name} 权重不能为负数")
            elif factor.weight > 1.0:
                warnings.append(f"因子 {factor.factor_name} 权重超过100%")
            elif factor.weight == 0:
                warnings.append(f"因子 {factor.factor_name} 已启用但权重为0")
        
        # 检查权重分布
        if enabled_factors:
            max_weight = max(f.weight for f in enabled_factors)
            min_weight = min(f.weight for f in enabled_factors if f.weight > 0)
            
            if max_weight > 0 and min_weight > 0:
                weight_ratio = max_weight / min_weight
                if weight_ratio > 20:  # 最大权重是最小权重的20倍以上
                    warnings.append("权重分布极不均衡，建议优化权重配置")
                elif weight_ratio > 10:
                    warnings.append("权重分布不够均衡，可能影响策略稳定性")
        
        # 检查因子多样性
        if len(enabled_factors) < 3:
            warnings.append("建议使用3个以上因子以提高策略稳定性")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "total_weight": total_weight,
            "enabled_factors": len(enabled_factors)
        }
    
    def normalize_weights(self, factors: List[SelectedFactor], 
                         target_sum: float = 1.0) -> List[SelectedFactor]:
        """标准化权重使总和等于目标值"""
        enabled_factors = [f for f in factors if f.is_enabled]
        
        if not enabled_factors:
            return factors
        
        # 计算当前权重总和
        current_sum = sum(f.weight for f in enabled_factors)
        
        if current_sum <= 0:
            # 如果当前权重总和为0或负数，使用等权重
            equal_weight = target_sum / len(enabled_factors)
            for factor in factors:
                if factor.is_enabled:
                    factor.weight = equal_weight
        else:
            # 按比例调整权重
            scale_factor = target_sum / current_sum
            for factor in factors:
                if factor.is_enabled:
                    factor.weight *= scale_factor
        
        return factors
    
    def apply_weight_preset(self, factors: List[SelectedFactor], 
                           preset_id: str) -> List[SelectedFactor]:
        """应用权重预设"""
        preset = next((p for p in self.preset_configs if p.id == preset_id), None)
        
        if not preset:
            raise ValueError(f"未找到权重预设: {preset_id}")
        
        enabled_factors = [f for f in factors if f.is_enabled]
        
        if not enabled_factors:
            return factors
        
        if preset.preset_type == WeightPresetType.EQUAL:
            return self._apply_equal_weight(factors)
        elif preset.id == "category_balanced":
            return self._apply_category_balanced_weight(factors)
        elif preset.preset_type == WeightPresetType.INVERSE_VOLATILITY:
            return self._apply_inverse_volatility_weight(factors)
        elif preset.preset_type == WeightPresetType.RISK_PARITY:
            return self._apply_risk_parity_weight(factors)
        else:
            # 默认使用等权重
            return self._apply_equal_weight(factors)
    
    def _apply_equal_weight(self, factors: List[SelectedFactor]) -> List[SelectedFactor]:
        """应用等权重"""
        enabled_factors = [f for f in factors if f.is_enabled]
        
        if enabled_factors:
            equal_weight = 1.0 / len(enabled_factors)
            for factor in factors:
                if factor.is_enabled:
                    factor.weight = equal_weight
                else:
                    factor.weight = 0.0
        
        return factors
    
    def _apply_category_balanced_weight(self, factors: List[SelectedFactor]) -> List[SelectedFactor]:
        """应用分类平衡权重"""
        enabled_factors = [f for f in factors if f.is_enabled]
        
        if not enabled_factors:
            return factors
        
        # 按分类统计因子数量
        category_counts = {}
        for factor in enabled_factors:
            factor_info = self.factor_engine.get_factor_info(factor.factor_id)
            category = factor_info['category'] if factor_info else 'unknown'
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # 计算每个分类的权重
        num_categories = len(category_counts)
        if num_categories == 0:
            return self._apply_equal_weight(factors)
        
        category_weight = 1.0 / num_categories
        
        # 分配权重
        for factor in factors:
            if factor.is_enabled:
                factor_info = self.factor_engine.get_factor_info(factor.factor_id)
                category = factor_info['category'] if factor_info else 'unknown'
                factor_count_in_category = category_counts.get(category, 1)
                factor.weight = category_weight / factor_count_in_category
            else:
                factor.weight = 0.0
        
        return factors
    
    def _apply_inverse_volatility_weight(self, factors: List[SelectedFactor]) -> List[SelectedFactor]:
        """应用反波动率权重（简化版本）"""
        enabled_factors = [f for f in factors if f.is_enabled]
        
        if not enabled_factors:
            return factors
        
        # 简化的反波动率权重：根据因子类型分配权重
        # 在实际应用中应该基于历史数据计算真实的波动率
        volatility_weights = {
            'trend': 0.8,      # 趋势因子相对稳定
            'momentum': 1.2,   # 动量因子波动较大
            'volume': 1.0      # 价量因子中等波动
        }
        
        total_inverse_vol = 0
        factor_inverse_vols = {}
        
        for factor in enabled_factors:
            factor_info = self.factor_engine.get_factor_info(factor.factor_id)
            category = factor_info['category'] if factor_info else 'volume'
            vol = volatility_weights.get(category, 1.0)
            inverse_vol = 1.0 / vol
            factor_inverse_vols[factor.factor_id] = inverse_vol
            total_inverse_vol += inverse_vol
        
        # 分配权重
        for factor in factors:
            if factor.is_enabled:
                inverse_vol = factor_inverse_vols.get(factor.factor_id, 1.0)
                factor.weight = inverse_vol / total_inverse_vol
            else:
                factor.weight = 0.0
        
        return factors
    
    def _apply_risk_parity_weight(self, factors: List[SelectedFactor]) -> List[SelectedFactor]:
        """应用风险平价权重（简化版本）"""
        enabled_factors = [f for f in factors if f.is_enabled]
        
        if not enabled_factors:
            return factors
        
        # 简化的风险平价：假设相关性和波动率
        # 在实际应用中应该基于历史数据计算协方差矩阵
        
        # 这里使用启发式方法：给高相关性的因子分配较小权重
        factor_risk_scores = {}
        
        for factor in enabled_factors:
            factor_info = self.factor_engine.get_factor_info(factor.factor_id)
            category = factor_info['category'] if factor_info else 'volume'
            
            # 计算与其他因子的预估相关性
            correlation_penalty = 0
            for other_factor in enabled_factors:
                if other_factor.factor_id != factor.factor_id:
                    other_info = self.factor_engine.get_factor_info(other_factor.factor_id)
                    other_category = other_info['category'] if other_info else 'volume'
                    
                    # 同类因子相关性更高
                    if category == other_category:
                        correlation_penalty += 0.3
                    else:
                        correlation_penalty += 0.1
            
            # 风险得分 = 基础风险 + 相关性惩罚
            base_risk = {'trend': 0.8, 'momentum': 1.2, 'volume': 1.0}.get(category, 1.0)
            risk_score = base_risk + correlation_penalty
            factor_risk_scores[factor.factor_id] = risk_score
        
        # 计算风险平价权重
        total_inverse_risk = sum(1.0 / score for score in factor_risk_scores.values())
        
        for factor in factors:
            if factor.is_enabled:
                risk_score = factor_risk_scores.get(factor.factor_id, 1.0)
                factor.weight = (1.0 / risk_score) / total_inverse_risk
            else:
                factor.weight = 0.0
        
        return factors
    
    def optimize_weights(self, factors: List[SelectedFactor], 
                        historical_data: pd.DataFrame = None,
                        optimization_method: str = "correlation_adjusted") -> WeightOptimizationResult:
        """优化权重配置"""
        enabled_factors = [f for f in factors if f.is_enabled]
        
        if not enabled_factors:
            return WeightOptimizationResult(
                optimized_weights={},
                optimization_method=optimization_method,
                performance_metrics={},
                recommendations=["至少需要启用一个因子"]
            )
        
        if optimization_method == "correlation_adjusted":
            optimized_factors = self._optimize_by_correlation(factors)
        elif optimization_method == "equal_weight":
            optimized_factors = self._apply_equal_weight(factors.copy())
        elif optimization_method == "category_balanced":
            optimized_factors = self._apply_category_balanced_weight(factors.copy())
        else:
            optimized_factors = self._apply_equal_weight(factors.copy())
        
        # 生成优化后的权重映射
        optimized_weights = {}
        for factor in optimized_factors:
            if factor.is_enabled:
                optimized_weights[factor.factor_id] = factor.weight
        
        # 计算性能指标
        performance_metrics = self._calculate_performance_metrics(optimized_factors)
        
        # 生成建议
        recommendations = self._generate_optimization_recommendations(factors, optimized_factors)
        
        return WeightOptimizationResult(
            optimized_weights=optimized_weights,
            optimization_method=optimization_method,
            performance_metrics=performance_metrics,
            recommendations=recommendations
        )
    
    def _optimize_by_correlation(self, factors: List[SelectedFactor]) -> List[SelectedFactor]:
        """基于相关性调整权重"""
        enabled_factors = [f for f in factors if f.is_enabled]
        
        if len(enabled_factors) <= 1:
            return self._apply_equal_weight(factors)
        
        # 估算因子相关性矩阵（简化版本）
        correlation_matrix = self._estimate_correlation_matrix(enabled_factors)
        
        # 计算多样化权重
        n = len(enabled_factors)
        base_weight = 1.0 / n
        
        adjusted_weights = []
        for i, factor in enumerate(enabled_factors):
            # 计算与其他因子的平均相关性
            avg_correlation = sum(abs(correlation_matrix[i][j]) 
                                for j in range(n) if i != j) / (n - 1) if n > 1 else 0
            
            # 相关性越高，权重调整越小
            adjustment_factor = 1.0 - (avg_correlation * 0.5)  # 最多减少50%
            adjusted_weight = base_weight * adjustment_factor
            adjusted_weights.append(adjusted_weight)
        
        # 标准化权重
        total_weight = sum(adjusted_weights)
        if total_weight > 0:
            adjusted_weights = [w / total_weight for w in adjusted_weights]
        
        # 应用优化后的权重
        optimized_factors = factors.copy()
        for i, factor in enumerate(optimized_factors):
            if factor.is_enabled:
                factor_index = next(j for j, f in enumerate(enabled_factors) if f.factor_id == factor.factor_id)
                factor.weight = adjusted_weights[factor_index]
            else:
                factor.weight = 0.0
        
        return optimized_factors
    
    def _estimate_correlation_matrix(self, factors: List[SelectedFactor]) -> List[List[float]]:
        """估算因子相关性矩阵"""
        n = len(factors)
        matrix = [[0.0 for _ in range(n)] for _ in range(n)]
        
        for i in range(n):
            for j in range(n):
                if i == j:
                    matrix[i][j] = 1.0
                else:
                    # 简化的相关性估算
                    factor1_info = self.factor_engine.get_factor_info(factors[i].factor_id)
                    factor2_info = self.factor_engine.get_factor_info(factors[j].factor_id)
                    
                    category1 = factor1_info['category'] if factor1_info else 'unknown'
                    category2 = factor2_info['category'] if factor2_info else 'unknown'
                    
                    if category1 == category2:
                        # 同类因子相关性较高
                        correlation = 0.6 + np.random.uniform(-0.2, 0.2)
                    else:
                        # 不同类因子相关性较低
                        correlation = 0.2 + np.random.uniform(-0.1, 0.1)
                    
                    matrix[i][j] = max(-1.0, min(1.0, correlation))
        
        return matrix
    
    def _calculate_performance_metrics(self, factors: List[SelectedFactor]) -> Dict[str, float]:
        """计算性能指标"""
        enabled_factors = [f for f in factors if f.is_enabled]
        
        if not enabled_factors:
            return {}
        
        # 权重统计
        weights = [f.weight for f in enabled_factors]
        
        # 计算权重分布的集中度 (Herfindahl Index)
        concentration = sum(w**2 for w in weights)
        
        # 计算权重分布的均匀度
        max_weight = max(weights) if weights else 0
        min_weight = min(weights) if weights else 0
        weight_range = max_weight - min_weight
        
        # 计算分类多样性
        categories = set()
        for factor in enabled_factors:
            factor_info = self.factor_engine.get_factor_info(factor.factor_id)
            if factor_info:
                categories.add(factor_info['category'])
        
        diversity_score = len(categories) / 5.0  # 假设最多5个分类
        
        return {
            'concentration_index': concentration,
            'weight_range': weight_range,
            'max_weight': max_weight,
            'min_weight': min_weight,
            'diversity_score': diversity_score,
            'factor_count': len(enabled_factors)
        }
    
    def _generate_optimization_recommendations(self, 
                                             original_factors: List[SelectedFactor],
                                             optimized_factors: List[SelectedFactor]) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        original_enabled = [f for f in original_factors if f.is_enabled]
        optimized_enabled = [f for f in optimized_factors if f.is_enabled]
        
        # 比较权重变化
        significant_changes = []
        for orig, opt in zip(original_enabled, optimized_enabled):
            if abs(orig.weight - opt.weight) > 0.1:  # 权重变化超过10%
                change_percent = (opt.weight - orig.weight) * 100
                significant_changes.append(f"{orig.factor_name}: {change_percent:+.1f}%")
        
        if significant_changes:
            recommendations.append(f"建议调整权重: {', '.join(significant_changes)}")
        
        # 检查分类多样性
        categories = set()
        for factor in optimized_enabled:
            factor_info = self.factor_engine.get_factor_info(factor.factor_id)
            if factor_info:
                categories.add(factor_info['category'])
        
        if len(categories) < 3:
            recommendations.append("建议增加不同类别的因子以提高策略多样性")
        
        # 检查权重分布
        if optimized_enabled:
            max_weight = max(f.weight for f in optimized_enabled)
            if max_weight > 0.5:
                recommendations.append("某个因子权重过高，建议分散风险")
        
        if not recommendations:
            recommendations.append("当前权重配置已经相对合理")
        
        return recommendations
    
    def generate_weight_suggestions(self, factors: List[SelectedFactor]) -> Dict[str, Any]:
        """生成权重配置建议"""
        enabled_factors = [f for f in factors if f.is_enabled]
        
        if not enabled_factors:
            return {"error": "没有启用的因子"}
        
        suggestions = {}
        
        # 等权重建议
        equal_factors = self._apply_equal_weight(factors.copy())
        suggestions["equal_weight"] = {
            "name": "等权重分配",
            "weights": {f.factor_id: f.weight for f in equal_factors if f.is_enabled},
            "description": "所有因子使用相等权重"
        }
        
        # 分类平衡建议
        balanced_factors = self._apply_category_balanced_weight(factors.copy())
        suggestions["category_balanced"] = {
            "name": "分类平衡",
            "weights": {f.factor_id: f.weight for f in balanced_factors if f.is_enabled},
            "description": "按因子分类均衡分配权重"
        }
        
        # 反波动率建议
        inverse_vol_factors = self._apply_inverse_volatility_weight(factors.copy())
        suggestions["inverse_volatility"] = {
            "name": "反波动率加权",
            "weights": {f.factor_id: f.weight for f in inverse_vol_factors if f.is_enabled},
            "description": "波动率较小的因子获得更高权重"
        }
        
        return suggestions


# 全局权重优化服务实例
weight_optimization_service = WeightOptimizationService()