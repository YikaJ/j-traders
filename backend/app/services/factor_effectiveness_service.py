"""
因子有效性分析服务
提供因子有效性评估、区分度分析、筛选能力测试等功能
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
from scipy import stats
from sklearn.metrics import roc_auc_score, precision_recall_curve
import warnings

from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.builtin_factors import (
    EffectivenessAnalysisResult, EffectivenessMetrics,
    FactorCalculationRecord
)
from .factor_statistics_service import factor_statistics_service
from .factor_correlation_service import factor_correlation_service

logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore')


class FactorEffectivenessService:
    """因子有效性分析服务"""
    
    def __init__(self):
        self.stats_service = factor_statistics_service
        self.correlation_service = factor_correlation_service
    
    def analyze_factor_effectiveness(self, factor_values: pd.Series,
                                   stock_metadata: pd.DataFrame = None,
                                   benchmark_data: pd.DataFrame = None) -> EffectivenessAnalysisResult:
        """分析因子有效性"""
        try:
            clean_factor = factor_values.dropna()
            
            if len(clean_factor) == 0:
                return self._get_empty_effectiveness_result()
            
            # 基础统计分析
            basic_stats = self.stats_service.calculate_basic_statistics(factor_values)
            
            # 区分度分析
            discrimination_result = self._analyze_factor_discrimination(clean_factor)
            
            # 稳定性分析（简化版）
            stability_result = self._analyze_factor_stability_simple(clean_factor)
            
            # 分布合理性分析
            distribution_result = self.stats_service.analyze_factor_distribution(factor_values)
            
            # 筛选能力分析
            screening_ability = self._analyze_screening_ability(clean_factor, stock_metadata)
            
            # 综合有效性评分
            overall_score = self._calculate_overall_effectiveness_score(
                basic_stats, discrimination_result, stability_result,
                distribution_result, screening_ability
            )
            
            # 生成建议
            recommendations = self._generate_effectiveness_recommendations(
                basic_stats, discrimination_result, stability_result,
                distribution_result, screening_ability, overall_score
            )
            
            return EffectivenessAnalysisResult(
                overall_effectiveness_score=overall_score,
                discrimination_power=discrimination_result['discrimination_score'],
                stability_score=stability_result['stability_score'],
                distribution_quality=distribution_result.get('distribution_score', 0.0),
                screening_ability=screening_ability['screening_score'],
                statistical_significance=screening_ability.get('significance_level', 0.0),
                sample_coverage=float(len(clean_factor) / len(factor_values)),
                analysis_details={
                    'basic_statistics': basic_stats,
                    'discrimination_analysis': discrimination_result,
                    'stability_analysis': stability_result,
                    'distribution_analysis': distribution_result,
                    'screening_analysis': screening_ability
                },
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"因子有效性分析失败: {e}")
            return self._get_empty_effectiveness_result()
    
    def _get_empty_effectiveness_result(self) -> EffectivenessAnalysisResult:
        """返回空的有效性分析结果"""
        return EffectivenessAnalysisResult(
            overall_effectiveness_score=0.0,
            discrimination_power=0.0,
            stability_score=0.0,
            distribution_quality=0.0,
            screening_ability=0.0,
            statistical_significance=0.0,
            sample_coverage=0.0,
            analysis_details={},
            recommendations=["数据不足，无法进行有效性分析"]
        )
    
    def _analyze_factor_discrimination(self, factor_values: pd.Series) -> Dict[str, Any]:
        """分析因子区分度"""
        try:
            if len(factor_values) < 10:
                return {
                    'discrimination_score': 0.0,
                    'value_range': 0.0,
                    'unique_ratio': 0.0,
                    'quantile_spread': 0.0,
                    'concentration_index': 1.0
                }
            
            # 值域分析
            value_range = float(factor_values.max() - factor_values.min())
            
            # 唯一值比例
            unique_ratio = float(len(factor_values.unique()) / len(factor_values))
            
            # 分位数展布
            q75 = factor_values.quantile(0.75)
            q25 = factor_values.quantile(0.25)
            iqr = q75 - q25
            median = factor_values.median()
            
            # 避免除零
            if median != 0:
                quantile_spread = float(iqr / abs(median))
            else:
                quantile_spread = float(iqr) if iqr > 0 else 0.0
            
            # 集中度指数 (Herfindahl Index)
            # 将值分箱计算分布的集中度
            try:
                bins = min(20, max(5, len(factor_values.unique())))
                hist, _ = np.histogram(factor_values, bins=bins)
                probabilities = hist / hist.sum()
                probabilities = probabilities[probabilities > 0]  # 移除零概率
                concentration_index = float(np.sum(probabilities ** 2))
            except Exception:
                concentration_index = 1.0
            
            # 变异系数
            cv = float(factor_values.std() / abs(factor_values.mean())) if factor_values.mean() != 0 else 0.0
            
            # 综合区分度得分
            # 区分度好的因子应该有：较大的值域、高的唯一值比例、合适的展布、低的集中度
            range_score = min(1.0, value_range / (factor_values.std() * 6)) if factor_values.std() > 0 else 0.0
            unique_score = unique_ratio
            spread_score = min(1.0, quantile_spread / 2.0) if quantile_spread > 0 else 0.0
            diversity_score = 1.0 - concentration_index
            cv_score = min(1.0, cv / 2.0) if cv > 0 else 0.0
            
            discrimination_score = (range_score * 0.2 + unique_score * 0.3 + 
                                  spread_score * 0.2 + diversity_score * 0.2 + cv_score * 0.1)
            
            return {
                'discrimination_score': float(discrimination_score),
                'value_range': value_range,
                'unique_ratio': unique_ratio,
                'quantile_spread': quantile_spread,
                'concentration_index': concentration_index,
                'coefficient_of_variation': cv,
                'component_scores': {
                    'range_score': range_score,
                    'unique_score': unique_score,
                    'spread_score': spread_score,
                    'diversity_score': diversity_score,
                    'cv_score': cv_score
                }
            }
            
        except Exception as e:
            logger.error(f"区分度分析失败: {e}")
            return {
                'discrimination_score': 0.0,
                'value_range': 0.0,
                'unique_ratio': 0.0,
                'quantile_spread': 0.0,
                'concentration_index': 1.0
            }
    
    def _analyze_factor_stability_simple(self, factor_values: pd.Series) -> Dict[str, Any]:
        """简化的因子稳定性分析"""
        try:
            if len(factor_values) < 20:
                return {
                    'stability_score': 0.0,
                    'outlier_impact': 1.0,
                    'robust_statistics': {}
                }
            
            # 异常值影响分析
            q1, q3 = factor_values.quantile(0.25), factor_values.quantile(0.75)
            iqr = q3 - q1
            
            if iqr > 0:
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                outliers = factor_values[(factor_values < lower_bound) | (factor_values > upper_bound)]
                outlier_ratio = len(outliers) / len(factor_values)
            else:
                outlier_ratio = 0.0
            
            # 稳健性统计
            median = factor_values.median()
            mad = float((factor_values - median).abs().median())  # 中位数绝对偏差
            
            # 与均值/标准差的比较
            mean = factor_values.mean()
            std = factor_values.std()
            
            # 稳健性评分
            if std > 0:
                robust_ratio = mad / std
                location_stability = 1 - abs(median - mean) / std
            else:
                robust_ratio = 1.0
                location_stability = 1.0
            
            outlier_impact = 1.0 - outlier_ratio
            
            # 综合稳定性得分
            stability_score = (robust_ratio * 0.4 + location_stability * 0.4 + outlier_impact * 0.2)
            stability_score = max(0.0, min(1.0, stability_score))
            
            return {
                'stability_score': float(stability_score),
                'outlier_ratio': outlier_ratio,
                'outlier_impact': float(outlier_impact),
                'robust_statistics': {
                    'median': float(median),
                    'mad': mad,
                    'robust_ratio': float(robust_ratio),
                    'location_stability': float(location_stability)
                }
            }
            
        except Exception as e:
            logger.error(f"稳定性分析失败: {e}")
            return {
                'stability_score': 0.0,
                'outlier_impact': 1.0,
                'robust_statistics': {}
            }
    
    def _analyze_screening_ability(self, factor_values: pd.Series,
                                 stock_metadata: pd.DataFrame = None) -> Dict[str, Any]:
        """分析筛选能力"""
        try:
            if len(factor_values) < 20:
                return {
                    'screening_score': 0.0,
                    'group_separation': 0.0,
                    'significance_level': 0.0
                }
            
            # 分组分析 - 将因子值分为5组
            try:
                factor_groups = pd.qcut(factor_values, 5, labels=['G1', 'G2', 'G3', 'G4', 'G5'], duplicates='drop')
            except ValueError:
                # 如果无法分为5组（重复值太多），则尝试分为更少的组
                try:
                    factor_groups = pd.qcut(factor_values, 3, labels=['G1', 'G2', 'G3'], duplicates='drop')
                except ValueError:
                    # 如果仍然无法分组，返回默认值
                    return {
                        'screening_score': 0.0,
                        'group_separation': 0.0,
                        'significance_level': 0.0,
                        'group_stats': {}
                    }
            
            # 计算各组统计信息
            group_stats = {}
            group_means = []
            group_sizes = []
            
            for group in factor_groups.cat.categories:
                group_mask = factor_groups == group
                group_values = factor_values[group_mask]
                
                if len(group_values) > 0:
                    group_stats[group] = {
                        'count': len(group_values),
                        'mean': float(group_values.mean()),
                        'std': float(group_values.std()),
                        'min': float(group_values.min()),
                        'max': float(group_values.max())
                    }
                    group_means.append(group_values.mean())
                    group_sizes.append(len(group_values))
            
            if len(group_means) < 2:
                return {
                    'screening_score': 0.0,
                    'group_separation': 0.0,
                    'significance_level': 0.0,
                    'group_stats': group_stats
                }
            
            # 组间分离度
            between_group_var = np.var(group_means, ddof=1) if len(group_means) > 1 else 0.0
            within_group_var = np.mean([group_stats[g]['std']**2 for g in group_stats if group_stats[g]['std'] > 0])
            
            if within_group_var > 0:
                group_separation = float(between_group_var / within_group_var)
            else:
                group_separation = 0.0
            
            # F检验 - 检验组间差异的显著性
            try:
                group_data = [factor_values[factor_groups == group].values for group in factor_groups.cat.categories]
                group_data = [g for g in group_data if len(g) > 0]  # 移除空组
                
                if len(group_data) >= 2:
                    f_stat, p_value = stats.f_oneway(*group_data)
                    significance_level = float(1 - p_value) if not np.isnan(p_value) else 0.0
                else:
                    significance_level = 0.0
            except Exception:
                significance_level = 0.0
            
            # 筛选能力得分
            separation_score = min(1.0, group_separation / 5.0)  # 标准化到0-1
            significance_score = significance_level
            
            screening_score = (separation_score * 0.6 + significance_score * 0.4)
            
            return {
                'screening_score': float(screening_score),
                'group_separation': group_separation,
                'significance_level': significance_level,
                'group_stats': group_stats,
                'f_statistic': float(f_stat) if 'f_stat' in locals() and not np.isnan(f_stat) else 0.0,
                'p_value': float(p_value) if 'p_value' in locals() and not np.isnan(p_value) else 1.0
            }
            
        except Exception as e:
            logger.error(f"筛选能力分析失败: {e}")
            return {
                'screening_score': 0.0,
                'group_separation': 0.0,
                'significance_level': 0.0
            }
    
    def _calculate_overall_effectiveness_score(self, basic_stats: Dict, 
                                             discrimination: Dict,
                                             stability: Dict, 
                                             distribution: Dict,
                                             screening: Dict) -> float:
        """计算综合有效性得分"""
        try:
            # 各项得分权重
            weights = {
                'data_quality': 0.2,      # 数据质量（非空率等）
                'discrimination': 0.25,   # 区分度
                'stability': 0.2,         # 稳定性
                'distribution': 0.15,     # 分布合理性
                'screening': 0.2          # 筛选能力
            }
            
            # 数据质量得分
            data_quality_score = (1 - basic_stats.get('null_ratio', 1.0)) * 0.6 + \
                               min(1.0, basic_stats.get('count', 0) / 100) * 0.4
            
            # 区分度得分
            discrimination_score = discrimination.get('discrimination_score', 0.0)
            
            # 稳定性得分
            stability_score = stability.get('stability_score', 0.0)
            
            # 分布合理性得分
            distribution_score = self._calculate_distribution_score(distribution)
            
            # 筛选能力得分
            screening_score = screening.get('screening_score', 0.0)
            
            # 加权综合得分
            overall_score = (
                data_quality_score * weights['data_quality'] +
                discrimination_score * weights['discrimination'] +
                stability_score * weights['stability'] +
                distribution_score * weights['distribution'] +
                screening_score * weights['screening']
            )
            
            # 确保得分在0-100之间
            return float(max(0.0, min(100.0, overall_score * 100)))
            
        except Exception as e:
            logger.error(f"计算综合得分失败: {e}")
            return 0.0
    
    def _calculate_distribution_score(self, distribution: Dict) -> float:
        """计算分布合理性得分"""
        try:
            # 基于分布特征计算得分
            normality_test = distribution.get('normality_test', {})
            distribution_score = distribution.get('distribution_score', 0.0)
            
            # 正态性得分（不要求完全正态，但也不要过于偏斜）
            p_value = normality_test.get('p_value', 0.0)
            normality_score = 0.5 + 0.5 * min(1.0, p_value * 10)  # 基准0.5分，p值越大加分越多
            
            # 分布拟合得分
            fit_score = min(1.0, distribution_score * 2)  # 标准化到0-1
            
            # 综合分布得分
            return float((normality_score * 0.4 + fit_score * 0.6))
            
        except Exception as e:
            logger.error(f"计算分布得分失败: {e}")
            return 0.5  # 返回中等得分
    
    def _generate_effectiveness_recommendations(self, basic_stats: Dict,
                                              discrimination: Dict,
                                              stability: Dict,
                                              distribution: Dict,
                                              screening: Dict,
                                              overall_score: float) -> List[str]:
        """生成有效性改进建议"""
        recommendations = []
        
        try:
            # 数据质量建议
            null_ratio = basic_stats.get('null_ratio', 0.0)
            if null_ratio > 0.1:
                recommendations.append(f"数据缺失率为{null_ratio:.1%}，建议改进数据质量或处理缺失值")
            
            sample_size = basic_stats.get('count', 0)
            if sample_size < 100:
                recommendations.append(f"样本量为{sample_size}，建议增加样本量以提高分析可靠性")
            
            # 区分度建议
            discrimination_score = discrimination.get('discrimination_score', 0.0)
            if discrimination_score < 0.5:
                unique_ratio = discrimination.get('unique_ratio', 0.0)
                if unique_ratio < 0.1:
                    recommendations.append("因子值过于集中，建议调整计算方法以增加区分度")
                
                concentration = discrimination.get('concentration_index', 0.0)
                if concentration > 0.8:
                    recommendations.append("因子值分布过于集中，考虑使用变换或标准化方法")
            
            # 稳定性建议
            stability_score = stability.get('stability_score', 0.0)
            if stability_score < 0.6:
                outlier_ratio = stability.get('outlier_ratio', 0.0)
                if outlier_ratio > 0.05:
                    recommendations.append(f"异常值比例为{outlier_ratio:.1%}，建议进行异常值处理")
            
            # 筛选能力建议
            screening_score = screening.get('screening_score', 0.0)
            if screening_score < 0.5:
                significance = screening.get('significance_level', 0.0)
                if significance < 0.8:
                    recommendations.append("因子筛选能力较弱，建议检查计算逻辑或考虑与其他因子组合")
            
            # 综合建议
            if overall_score < 50:
                recommendations.append("因子整体有效性较低，建议重新设计或更换因子")
            elif overall_score < 70:
                recommendations.append("因子有效性中等，建议针对薄弱环节进行优化")
            else:
                recommendations.append("因子有效性良好，可以考虑在策略中使用")
            
            # 如果没有具体建议，给出通用建议
            if len(recommendations) == 0:
                recommendations.append("因子表现正常，建议持续监控其有效性")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"生成建议失败: {e}")
            return ["建议对因子进行进一步分析和优化"]
    
    def compare_factor_effectiveness(self, factor_data: Dict[str, pd.Series],
                                   stock_metadata: pd.DataFrame = None) -> Dict[str, Any]:
        """比较多个因子的有效性"""
        try:
            if not factor_data or len(factor_data) < 2:
                return {
                    'comparison_results': {},
                    'ranking': [],
                    'summary': {}
                }
            
            comparison_results = {}
            effectiveness_scores = {}
            
            # 分析每个因子
            for factor_name, factor_values in factor_data.items():
                try:
                    analysis_result = self.analyze_factor_effectiveness(
                        factor_values, stock_metadata
                    )
                    comparison_results[factor_name] = analysis_result
                    effectiveness_scores[factor_name] = analysis_result.overall_effectiveness_score
                except Exception as e:
                    logger.error(f"分析因子 {factor_name} 失败: {e}")
                    effectiveness_scores[factor_name] = 0.0
            
            # 排序
            ranking = sorted(effectiveness_scores.items(), 
                           key=lambda x: x[1], reverse=True)
            
            # 汇总统计
            scores = list(effectiveness_scores.values())
            summary = {
                'total_factors': len(factor_data),
                'analyzed_factors': len([s for s in scores if s > 0]),
                'average_score': float(np.mean(scores)) if scores else 0.0,
                'best_factor': ranking[0][0] if ranking else None,
                'best_score': ranking[0][1] if ranking else 0.0,
                'worst_factor': ranking[-1][0] if ranking else None,
                'worst_score': ranking[-1][1] if ranking else 0.0,
                'score_std': float(np.std(scores)) if len(scores) > 1 else 0.0
            }
            
            return {
                'comparison_results': comparison_results,
                'ranking': [{'factor': name, 'score': score} for name, score in ranking],
                'summary': summary
            }
            
        except Exception as e:
            logger.error(f"因子有效性比较失败: {e}")
            return {
                'comparison_results': {},
                'ranking': [],
                'summary': {}
            }
    
    def analyze_factor_combination_effectiveness(self, factors: List[pd.Series],
                                               weights: List[float] = None) -> Dict[str, Any]:
        """分析因子组合的有效性"""
        try:
            if not factors or len(factors) < 2:
                return {
                    'combination_score': 0.0,
                    'individual_contributions': {},
                    'synergy_effect': 0.0,
                    'recommendations': []
                }
            
            # 默认等权重
            if weights is None:
                weights = [1.0 / len(factors)] * len(factors)
            elif len(weights) != len(factors):
                raise ValueError("权重数量与因子数量不匹配")
            
            # 标准化权重
            total_weight = sum(weights)
            if total_weight > 0:
                weights = [w / total_weight for w in weights]
            
            # 计算组合因子
            combined_factor = pd.Series(0.0, index=factors[0].index)
            for factor, weight in zip(factors, weights):
                # 标准化因子值
                normalized_factor = (factor - factor.mean()) / factor.std() if factor.std() > 0 else factor
                combined_factor += normalized_factor * weight
            
            # 分析组合因子有效性
            combination_analysis = self.analyze_factor_effectiveness(combined_factor)
            
            # 分析各个因子的个体贡献
            individual_contributions = {}
            individual_scores = []
            
            for i, factor in enumerate(factors):
                individual_analysis = self.analyze_factor_effectiveness(factor)
                factor_name = f"factor_{i+1}"
                individual_contributions[factor_name] = {
                    'effectiveness_score': individual_analysis.overall_effectiveness_score,
                    'weight': weights[i],
                    'weighted_contribution': individual_analysis.overall_effectiveness_score * weights[i]
                }
                individual_scores.append(individual_analysis.overall_effectiveness_score)
            
            # 计算协同效应
            weighted_average_score = sum(score * weight for score, weight in zip(individual_scores, weights))
            combination_score = combination_analysis.overall_effectiveness_score
            synergy_effect = combination_score - weighted_average_score
            
            # 生成建议
            recommendations = []
            if synergy_effect > 5:
                recommendations.append("因子组合产生正向协同效应，建议保持当前配置")
            elif synergy_effect < -5:
                recommendations.append("因子组合产生负向协同效应，建议调整权重或更换因子")
            else:
                recommendations.append("因子组合效果与个体效果相当，考虑简化策略")
            
            if max(individual_scores) > combination_score:
                best_individual = max(range(len(individual_scores)), key=lambda i: individual_scores[i])
                recommendations.append(f"单独使用factor_{best_individual+1}可能效果更好")
            
            return {
                'combination_score': combination_score,
                'individual_contributions': individual_contributions,
                'synergy_effect': synergy_effect,
                'weighted_average_score': weighted_average_score,
                'recommendations': recommendations,
                'analysis_details': {
                    'combination_analysis': combination_analysis,
                    'factor_weights': weights
                }
            }
            
        except Exception as e:
            logger.error(f"因子组合有效性分析失败: {e}")
            return {
                'combination_score': 0.0,
                'individual_contributions': {},
                'synergy_effect': 0.0,
                'recommendations': ["分析失败，请检查数据质量"]
            }


# 全局因子有效性服务实例
factor_effectiveness_service = FactorEffectivenessService()