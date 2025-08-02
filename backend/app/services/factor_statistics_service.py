"""
因子统计特征分析服务
提供因子统计分析、有效性评估、分布分析等功能
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
from scipy import stats
from scipy.stats import shapiro, jarque_bera, kstest
import math

from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models.factor import FactorStatistics
from app.schemas.builtin_factors import (
    FactorStatisticsBase, FactorStatisticsResponse,
    QuantileAnalysisResult, EffectivenessMetrics,
    FactorStatisticsResult, FactorCalculationRecord
)
from .builtin_factor_engine import builtin_factor_engine

logger = logging.getLogger(__name__)


class FactorStatisticsService:
    """因子统计特征分析服务"""
    
    def __init__(self):
        self.factor_engine = builtin_factor_engine
    
    def calculate_basic_statistics(self, factor_values: pd.Series) -> Dict[str, float]:
        """计算因子基础统计特征"""
        try:
            # 移除NaN值
            clean_values = factor_values.dropna()
            
            if len(clean_values) == 0:
                return self._get_empty_statistics()
            
            # 基础统计量
            stats_dict = {
                'count': len(clean_values),
                'mean': float(clean_values.mean()),
                'std': float(clean_values.std()),
                'min': float(clean_values.min()),
                'max': float(clean_values.max()),
                'median': float(clean_values.median()),
                'q25': float(clean_values.quantile(0.25)),
                'q75': float(clean_values.quantile(0.75)),
                'null_ratio': float((len(factor_values) - len(clean_values)) / len(factor_values))
            }
            
            # 分布特征
            if len(clean_values) > 3:
                stats_dict['skewness'] = float(stats.skew(clean_values))
                stats_dict['kurtosis'] = float(stats.kurtosis(clean_values))
            else:
                stats_dict['skewness'] = 0.0
                stats_dict['kurtosis'] = 0.0
            
            # 变异系数
            if stats_dict['mean'] != 0:
                stats_dict['cv'] = stats_dict['std'] / abs(stats_dict['mean'])
            else:
                stats_dict['cv'] = 0.0
            
            # 四分位距
            stats_dict['iqr'] = stats_dict['q75'] - stats_dict['q25']
            
            # 极值比例
            q1, q3 = stats_dict['q25'], stats_dict['q75']
            iqr = stats_dict['iqr']
            if iqr > 0:
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                outliers = clean_values[(clean_values < lower_bound) | (clean_values > upper_bound)]
                stats_dict['outlier_ratio'] = float(len(outliers) / len(clean_values))
            else:
                stats_dict['outlier_ratio'] = 0.0
            
            return stats_dict
            
        except Exception as e:
            logger.error(f"计算基础统计量失败: {e}")
            return self._get_empty_statistics()
    
    def _get_empty_statistics(self) -> Dict[str, float]:
        """返回空统计量"""
        return {
            'count': 0, 'mean': 0.0, 'std': 0.0, 'min': 0.0, 'max': 0.0,
            'median': 0.0, 'q25': 0.0, 'q75': 0.0, 'skewness': 0.0,
            'kurtosis': 0.0, 'null_ratio': 1.0, 'cv': 0.0, 'iqr': 0.0,
            'outlier_ratio': 0.0
        }
    
    def analyze_factor_distribution(self, factor_values: pd.Series) -> Dict[str, Any]:
        """分析因子分布特征"""
        try:
            clean_values = factor_values.dropna()
            
            if len(clean_values) < 10:
                return {
                    'distribution_type': 'insufficient_data',
                    'normality_test': {'is_normal': False, 'p_value': 0.0},
                    'distribution_params': {},
                    'histogram_bins': [],
                    'histogram_counts': []
                }
            
            # 正态性检验
            normality_result = self._test_normality(clean_values)
            
            # 分布拟合
            distribution_fit = self._fit_distribution(clean_values)
            
            # 直方图数据
            hist_counts, hist_bins = np.histogram(clean_values, bins=20)
            
            return {
                'distribution_type': distribution_fit['best_fit'],
                'normality_test': normality_result,
                'distribution_params': distribution_fit['params'],
                'histogram_bins': hist_bins.tolist(),
                'histogram_counts': hist_counts.tolist(),
                'distribution_score': distribution_fit['score']
            }
            
        except Exception as e:
            logger.error(f"分析因子分布失败: {e}")
            return {
                'distribution_type': 'unknown',
                'normality_test': {'is_normal': False, 'p_value': 0.0},
                'distribution_params': {},
                'histogram_bins': [],
                'histogram_counts': []
            }
    
    def _test_normality(self, values: pd.Series) -> Dict[str, Any]:
        """正态性检验"""
        try:
            if len(values) < 8:
                return {'is_normal': False, 'p_value': 0.0, 'test_method': 'insufficient_data'}
            
            # Shapiro-Wilk test (适用于小样本)
            if len(values) <= 5000:
                stat, p_value = shapiro(values)
                test_method = 'shapiro_wilk'
            else:
                # Jarque-Bera test (适用于大样本)
                stat, p_value = jarque_bera(values)
                test_method = 'jarque_bera'
            
            return {
                'is_normal': p_value > 0.05,
                'p_value': float(p_value),
                'test_statistic': float(stat),
                'test_method': test_method
            }
            
        except Exception as e:
            logger.error(f"正态性检验失败: {e}")
            return {'is_normal': False, 'p_value': 0.0, 'test_method': 'error'}
    
    def _fit_distribution(self, values: pd.Series) -> Dict[str, Any]:
        """拟合分布"""
        try:
            distributions = [
                ('normal', stats.norm),
                ('lognormal', stats.lognorm),
                ('exponential', stats.expon),
                ('uniform', stats.uniform)
            ]
            
            best_fit = 'normal'
            best_score = -np.inf
            best_params = {}
            
            for name, distribution in distributions:
                try:
                    # 拟合分布参数
                    params = distribution.fit(values)
                    
                    # 使用KS检验评估拟合优度
                    ks_stat, ks_p = kstest(values, lambda x: distribution.cdf(x, *params))
                    
                    # 分数越高越好（p值越大越好）
                    score = ks_p
                    
                    if score > best_score:
                        best_score = score
                        best_fit = name
                        best_params = {f'param_{i}': float(p) for i, p in enumerate(params)}
                        
                except Exception:
                    continue
            
            return {
                'best_fit': best_fit,
                'params': best_params,
                'score': float(best_score)
            }
            
        except Exception as e:
            logger.error(f"分布拟合失败: {e}")
            return {'best_fit': 'unknown', 'params': {}, 'score': 0.0}
    
    def calculate_quantile_analysis(self, factor_values: pd.Series, 
                                   stock_returns: pd.Series = None) -> QuantileAnalysisResult:
        """计算分位数分析"""
        try:
            clean_values = factor_values.dropna()
            
            if len(clean_values) == 0:
                return QuantileAnalysisResult(
                    quantile_stats={},
                    quantile_returns={},
                    ic_by_quantile={},
                    factor_coverage=0.0
                )
            
            # 分位数统计
            quantiles = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
            quantile_stats = {}
            
            for q in quantiles:
                quantile_stats[f'q{int(q*10)}'] = float(clean_values.quantile(q))
            
            # 如果有收益率数据，计算分位数收益率
            quantile_returns = {}
            ic_by_quantile = {}
            
            if stock_returns is not None and len(stock_returns) > 0:
                # 将因子值分为5个分位数组
                factor_quantiles = pd.qcut(clean_values, 5, labels=['Q1', 'Q2', 'Q3', 'Q4', 'Q5'])
                
                for i, q_label in enumerate(['Q1', 'Q2', 'Q3', 'Q4', 'Q5']):
                    q_mask = factor_quantiles == q_label
                    if q_mask.sum() > 0:
                        # 该分位数的平均收益率
                        q_returns = stock_returns[factor_values.index[q_mask]]
                        quantile_returns[q_label] = {
                            'mean_return': float(q_returns.mean()) if len(q_returns) > 0 else 0.0,
                            'std_return': float(q_returns.std()) if len(q_returns) > 0 else 0.0,
                            'count': int(q_mask.sum())
                        }
                        
                        # 计算该分位数内的IC
                        if len(q_returns) > 1:
                            q_factor_values = clean_values[q_mask]
                            if len(q_factor_values) == len(q_returns):
                                ic_corr = np.corrcoef(q_factor_values, q_returns)[0, 1]
                                ic_by_quantile[q_label] = float(ic_corr) if not np.isnan(ic_corr) else 0.0
                            else:
                                ic_by_quantile[q_label] = 0.0
                        else:
                            ic_by_quantile[q_label] = 0.0
            
            # 因子覆盖率
            factor_coverage = float(len(clean_values) / len(factor_values))
            
            return QuantileAnalysisResult(
                quantile_stats=quantile_stats,
                quantile_returns=quantile_returns,
                ic_by_quantile=ic_by_quantile,
                factor_coverage=factor_coverage
            )
            
        except Exception as e:
            logger.error(f"分位数分析失败: {e}")
            return QuantileAnalysisResult(
                quantile_stats={},
                quantile_returns={},
                ic_by_quantile={},
                factor_coverage=0.0
            )
    
    def calculate_effectiveness_metrics(self, factor_values: pd.Series,
                                      stock_returns: pd.Series = None,
                                      benchmark_returns: pd.Series = None) -> EffectivenessMetrics:
        """计算因子有效性指标"""
        try:
            clean_factor = factor_values.dropna()
            
            if len(clean_factor) == 0:
                return self._get_empty_effectiveness_metrics()
            
            # 基础有效性指标
            effectiveness_score = self._calculate_basic_effectiveness_score(clean_factor)
            
            # 如果有收益率数据，计算更多指标
            if stock_returns is not None and len(stock_returns) > 0:
                # 确保索引对齐
                common_index = clean_factor.index.intersection(stock_returns.index)
                if len(common_index) > 10:
                    aligned_factor = clean_factor[common_index]
                    aligned_returns = stock_returns[common_index]
                    
                    # IC (Information Coefficient)
                    ic = np.corrcoef(aligned_factor, aligned_returns)[0, 1]
                    ic = float(ic) if not np.isnan(ic) else 0.0
                    
                    # Rank IC
                    rank_ic = stats.spearmanr(aligned_factor, aligned_returns)[0]
                    rank_ic = float(rank_ic) if not np.isnan(rank_ic) else 0.0
                    
                    # IC 绝对值的平均值
                    abs_ic = abs(ic)
                    
                    # 单调性检验
                    monotonicity = self._test_monotonicity(aligned_factor, aligned_returns)
                    
                    # 分组收益率差异
                    group_spread = self._calculate_group_spread(aligned_factor, aligned_returns)
                    
                    return EffectivenessMetrics(
                        ic=ic,
                        rank_ic=rank_ic,
                        abs_ic=abs_ic,
                        ic_ir=ic / 0.1 if abs(ic) > 0 else 0.0,  # 简化的IR计算
                        effectiveness_score=effectiveness_score,
                        monotonicity=monotonicity,
                        group_spread=group_spread,
                        sample_size=len(common_index)
                    )
            
            # 无收益率数据时的基础指标
            return EffectivenessMetrics(
                ic=0.0,
                rank_ic=0.0,
                abs_ic=0.0,
                ic_ir=0.0,
                effectiveness_score=effectiveness_score,
                monotonicity=0.0,
                group_spread=0.0,
                sample_size=len(clean_factor)
            )
            
        except Exception as e:
            logger.error(f"计算有效性指标失败: {e}")
            return self._get_empty_effectiveness_metrics()
    
    def _get_empty_effectiveness_metrics(self) -> EffectivenessMetrics:
        """返回空的有效性指标"""
        return EffectivenessMetrics(
            ic=0.0, rank_ic=0.0, abs_ic=0.0, ic_ir=0.0,
            effectiveness_score=0.0, monotonicity=0.0,
            group_spread=0.0, sample_size=0
        )
    
    def _calculate_basic_effectiveness_score(self, factor_values: pd.Series) -> float:
        """计算基础有效性得分"""
        try:
            # 基于因子分布特征计算有效性得分
            stats_dict = self.calculate_basic_statistics(factor_values)
            
            # 得分组成：
            # 1. 非空率 (30%)
            non_null_score = (1 - stats_dict['null_ratio']) * 30
            
            # 2. 分布合理性 (25%)
            # 变异系数适中，偏度不过大
            cv_score = min(25, max(0, (1 - abs(stats_dict['cv'] - 0.5)) * 25))
            skew_score = max(0, (1 - abs(stats_dict['skewness']) / 5) * 25)
            distribution_score = (cv_score + skew_score) / 2
            
            # 3. 极值控制 (20%)
            outlier_score = max(0, (1 - stats_dict['outlier_ratio']) * 20)
            
            # 4. 数据量 (25%)
            sample_score = min(25, stats_dict['count'] / 100 * 25)
            
            total_score = non_null_score + distribution_score + outlier_score + sample_score
            
            return min(100.0, total_score)
            
        except Exception as e:
            logger.error(f"计算基础有效性得分失败: {e}")
            return 0.0
    
    def _test_monotonicity(self, factor_values: pd.Series, 
                          stock_returns: pd.Series) -> float:
        """检验因子单调性"""
        try:
            # 将因子分为5组，检验收益率是否单调
            factor_quantiles = pd.qcut(factor_values, 5, labels=False)
            
            group_returns = []
            for i in range(5):
                group_mask = factor_quantiles == i
                if group_mask.sum() > 0:
                    group_return = stock_returns[group_mask].mean()
                    group_returns.append(group_return)
            
            if len(group_returns) < 3:
                return 0.0
            
            # 计算单调性：检查是否单调递增或递减
            diffs = np.diff(group_returns)
            
            # 单调递增
            monotonic_inc = np.all(diffs >= 0)
            # 单调递减
            monotonic_dec = np.all(diffs <= 0)
            
            if monotonic_inc or monotonic_dec:
                # 计算单调性强度
                abs_diffs = np.abs(diffs)
                monotonicity = np.mean(abs_diffs) / (np.std(group_returns) + 1e-8)
                return min(1.0, monotonicity)
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"单调性检验失败: {e}")
            return 0.0
    
    def _calculate_group_spread(self, factor_values: pd.Series,
                               stock_returns: pd.Series) -> float:
        """计算分组收益率差异"""
        try:
            # 将因子分为5组
            factor_quantiles = pd.qcut(factor_values, 5, labels=False)
            
            group_returns = []
            for i in range(5):
                group_mask = factor_quantiles == i
                if group_mask.sum() > 0:
                    group_return = stock_returns[group_mask].mean()
                    group_returns.append(group_return)
            
            if len(group_returns) < 2:
                return 0.0
            
            # 最高组与最低组的收益率差异
            spread = max(group_returns) - min(group_returns)
            return float(spread)
            
        except Exception as e:
            logger.error(f"计算分组差异失败: {e}")
            return 0.0
    
    def analyze_factor_stability(self, factor_time_series: pd.DataFrame,
                                time_window: int = 30) -> Dict[str, Any]:
        """分析因子时间稳定性"""
        try:
            if len(factor_time_series) < time_window * 2:
                return {
                    'stability_score': 0.0,
                    'rolling_mean_std': 0.0,
                    'rolling_correlation': 0.0,
                    'trend_analysis': 'insufficient_data'
                }
            
            # 计算滚动统计量
            rolling_mean = factor_time_series.rolling(window=time_window).mean()
            rolling_std = factor_time_series.rolling(window=time_window).std()
            
            # 稳定性得分：基于滚动标准差的变化
            mean_std_change = rolling_std.std()
            mean_mean_change = rolling_mean.std()
            
            # 标准化稳定性得分
            stability_score = 1.0 / (1.0 + mean_std_change + mean_mean_change)
            
            # 滚动相关性
            if len(factor_time_series.columns) > 1:
                # 多列数据的相关性稳定性
                rolling_corr = factor_time_series.rolling(window=time_window).corr()
                avg_corr_std = rolling_corr.std().mean()
            else:
                # 单列数据与滞后序列的相关性
                lagged_series = factor_time_series.shift(1)
                rolling_corr = factor_time_series.rolling(window=time_window).corr(lagged_series)
                avg_corr_std = rolling_corr.std().mean()
            
            # 趋势分析
            trend_analysis = self._analyze_trend(factor_time_series)
            
            return {
                'stability_score': float(stability_score),
                'rolling_mean_std': float(mean_mean_change),
                'rolling_std_std': float(mean_std_change),
                'rolling_correlation': float(avg_corr_std) if not np.isnan(avg_corr_std) else 0.0,
                'trend_analysis': trend_analysis
            }
            
        except Exception as e:
            logger.error(f"稳定性分析失败: {e}")
            return {
                'stability_score': 0.0,
                'rolling_mean_std': 0.0,
                'rolling_correlation': 0.0,
                'trend_analysis': 'error'
            }
    
    def _analyze_trend(self, time_series: pd.DataFrame) -> str:
        """分析时间序列趋势"""
        try:
            # 简单的趋势分析：线性回归斜率
            if len(time_series) < 10:
                return 'insufficient_data'
            
            y = time_series.mean(axis=1) if len(time_series.columns) > 1 else time_series.iloc[:, 0]
            x = np.arange(len(y))
            
            # 线性回归
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            
            if p_value < 0.05:  # 显著性检验
                if slope > 0:
                    return 'upward_trend'
                else:
                    return 'downward_trend'
            else:
                return 'no_significant_trend'
                
        except Exception as e:
            logger.error(f"趋势分析失败: {e}")
            return 'error'
    
    def save_factor_statistics(self, factor_id: str, factor_type: str,
                              statistics: Dict[str, Any], db: Session = None) -> bool:
        """保存因子统计结果到数据库"""
        try:
            if db is None:
                db = next(get_db())
            
            # 创建统计记录
            factor_stats = FactorStatistics(
                factor_id=factor_id,
                factor_type=factor_type,
                analysis_date=datetime.utcnow(),
                mean=statistics.get('mean', 0.0),
                std=statistics.get('std', 0.0),
                min=statistics.get('min', 0.0),
                max=statistics.get('max', 0.0),
                median=statistics.get('median', 0.0),
                q25=statistics.get('q25', 0.0),
                q75=statistics.get('q75', 0.0),
                skewness=statistics.get('skewness', 0.0),
                kurtosis=statistics.get('kurtosis', 0.0),
                null_ratio=statistics.get('null_ratio', 0.0),
                effectiveness_score=statistics.get('effectiveness_score', 0.0)
            )
            
            db.add(factor_stats)
            db.commit()
            
            logger.info(f"因子统计结果已保存: {factor_id}")
            return True
            
        except Exception as e:
            if db:
                db.rollback()
            logger.error(f"保存因子统计结果失败: {e}")
            return False
    
    def get_factor_statistics_history(self, factor_id: str, 
                                     days: int = 30, db: Session = None) -> List[FactorStatisticsResponse]:
        """获取因子统计历史记录"""
        try:
            if db is None:
                db = next(get_db())
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            stats_records = db.query(FactorStatistics).filter(
                FactorStatistics.factor_id == factor_id,
                FactorStatistics.analysis_date >= cutoff_date
            ).order_by(FactorStatistics.analysis_date.desc()).all()
            
            return [self._db_to_response(record) for record in stats_records]
            
        except Exception as e:
            logger.error(f"获取因子统计历史失败: {e}")
            return []
    
    def _db_to_response(self, db_stats: FactorStatistics) -> FactorStatisticsResponse:
        """将数据库对象转换为响应对象"""
        return FactorStatisticsResponse(
            id=db_stats.id,
            factor_id=db_stats.factor_id,
            factor_type=db_stats.factor_type,
            analysis_date=db_stats.analysis_date,
            mean=db_stats.mean,
            std=db_stats.std,
            min=db_stats.min,
            max=db_stats.max,
            median=db_stats.median,
            q25=db_stats.q25,
            q75=db_stats.q75,
            skewness=db_stats.skewness,
            kurtosis=db_stats.kurtosis,
            null_ratio=db_stats.null_ratio,
            effectiveness_score=db_stats.effectiveness_score
        )


# 全局因子统计服务实例
factor_statistics_service = FactorStatisticsService()