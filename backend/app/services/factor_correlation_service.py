"""
因子相关性计算服务
提供因子间相关性分析、矩阵计算、聚类分析等功能
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
from scipy import stats
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
from scipy.spatial.distance import pdist, squareform
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import warnings

from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models.factor import FactorCorrelation
from app.schemas.builtin_factors import (
    CorrelationMatrix, FactorComparisonResult,
    SelectedFactor
)
from .builtin_factor_engine import builtin_factor_engine

logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore')


class FactorCorrelationService:
    """因子相关性计算服务"""
    
    def __init__(self):
        self.factor_engine = builtin_factor_engine
    
    def calculate_correlation_matrix(self, factor_data: pd.DataFrame,
                                   method: str = 'pearson') -> CorrelationMatrix:
        """计算因子相关性矩阵"""
        try:
            if factor_data.empty or len(factor_data.columns) < 2:
                return CorrelationMatrix(
                    correlation_matrix={},
                    factor_names=[],
                    method=method,
                    sample_size=0,
                    calculation_date=datetime.utcnow()
                )
            
            # 移除缺失值
            clean_data = factor_data.dropna()
            
            if len(clean_data) < 10:
                return CorrelationMatrix(
                    correlation_matrix={},
                    factor_names=list(factor_data.columns),
                    method=method,
                    sample_size=len(clean_data),
                    calculation_date=datetime.utcnow()
                )
            
            # 计算相关性矩阵
            if method == 'pearson':
                corr_matrix = clean_data.corr(method='pearson')
            elif method == 'spearman':
                corr_matrix = clean_data.corr(method='spearman')
            elif method == 'kendall':
                corr_matrix = clean_data.corr(method='kendall')
            else:
                corr_matrix = clean_data.corr(method='pearson')
            
            # 转换为字典格式
            correlation_dict = {}
            factor_names = list(corr_matrix.columns)
            
            for i, factor1 in enumerate(factor_names):
                correlation_dict[factor1] = {}
                for j, factor2 in enumerate(factor_names):
                    correlation_dict[factor1][factor2] = float(corr_matrix.iloc[i, j])
            
            return CorrelationMatrix(
                correlation_matrix=correlation_dict,
                factor_names=factor_names,
                method=method,
                sample_size=len(clean_data),
                calculation_date=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"计算相关性矩阵失败: {e}")
            return CorrelationMatrix(
                correlation_matrix={},
                factor_names=[],
                method=method,
                sample_size=0,
                calculation_date=datetime.utcnow()
            )
    
    def analyze_factor_correlation_pairs(self, factor_data: pd.DataFrame,
                                       threshold: float = 0.7) -> Dict[str, Any]:
        """分析因子相关性对"""
        try:
            if factor_data.empty or len(factor_data.columns) < 2:
                return {
                    'high_correlation_pairs': [],
                    'low_correlation_pairs': [],
                    'redundant_factors': [],
                    'correlation_summary': {}
                }
            
            # 计算相关性矩阵
            corr_matrix_result = self.calculate_correlation_matrix(factor_data, 'pearson')
            corr_matrix = pd.DataFrame(corr_matrix_result.correlation_matrix)
            
            if corr_matrix.empty:
                return {
                    'high_correlation_pairs': [],
                    'low_correlation_pairs': [],
                    'redundant_factors': [],
                    'correlation_summary': {}
                }
            
            factor_names = list(corr_matrix.columns)
            high_corr_pairs = []
            low_corr_pairs = []
            
            # 分析因子对相关性
            for i in range(len(factor_names)):
                for j in range(i + 1, len(factor_names)):
                    factor1, factor2 = factor_names[i], factor_names[j]
                    correlation = corr_matrix.loc[factor1, factor2]
                    
                    abs_correlation = abs(correlation)
                    
                    pair_info = {
                        'factor1': factor1,
                        'factor2': factor2,
                        'correlation': float(correlation),
                        'abs_correlation': float(abs_correlation),
                        'correlation_strength': self._get_correlation_strength(abs_correlation)
                    }
                    
                    if abs_correlation >= threshold:
                        high_corr_pairs.append(pair_info)
                    elif abs_correlation <= 0.1:
                        low_corr_pairs.append(pair_info)
            
            # 识别冗余因子
            redundant_factors = self._identify_redundant_factors(corr_matrix, threshold)
            
            # 相关性汇总统计
            correlation_summary = self._calculate_correlation_summary(corr_matrix)
            
            return {
                'high_correlation_pairs': sorted(high_corr_pairs, 
                                               key=lambda x: x['abs_correlation'], reverse=True),
                'low_correlation_pairs': sorted(low_corr_pairs,
                                              key=lambda x: x['abs_correlation']),
                'redundant_factors': redundant_factors,
                'correlation_summary': correlation_summary
            }
            
        except Exception as e:
            logger.error(f"分析因子相关性对失败: {e}")
            return {
                'high_correlation_pairs': [],
                'low_correlation_pairs': [],
                'redundant_factors': [],
                'correlation_summary': {}
            }
    
    def _get_correlation_strength(self, abs_correlation: float) -> str:
        """获取相关性强度描述"""
        if abs_correlation >= 0.9:
            return 'very_strong'
        elif abs_correlation >= 0.7:
            return 'strong'
        elif abs_correlation >= 0.5:
            return 'moderate'
        elif abs_correlation >= 0.3:
            return 'weak'
        else:
            return 'very_weak'
    
    def _identify_redundant_factors(self, corr_matrix: pd.DataFrame, 
                                   threshold: float = 0.7) -> List[Dict[str, Any]]:
        """识别冗余因子"""
        try:
            redundant_factors = []
            factor_names = list(corr_matrix.columns)
            processed_factors = set()
            
            for i, factor1 in enumerate(factor_names):
                if factor1 in processed_factors:
                    continue
                
                highly_correlated = []
                for j, factor2 in enumerate(factor_names):
                    if i != j and factor2 not in processed_factors:
                        correlation = abs(corr_matrix.loc[factor1, factor2])
                        if correlation >= threshold:
                            highly_correlated.append({
                                'factor': factor2,
                                'correlation': float(correlation)
                            })
                
                if highly_correlated:
                    # 计算该因子组的冗余度
                    redundancy_group = {
                        'primary_factor': factor1,
                        'redundant_with': highly_correlated,
                        'redundancy_score': sum(item['correlation'] for item in highly_correlated) / len(highly_correlated),
                        'group_size': len(highly_correlated) + 1
                    }
                    
                    redundant_factors.append(redundancy_group)
                    
                    # 标记已处理的因子
                    processed_factors.add(factor1)
                    for item in highly_correlated:
                        processed_factors.add(item['factor'])
            
            return redundant_factors
            
        except Exception as e:
            logger.error(f"识别冗余因子失败: {e}")
            return []
    
    def _calculate_correlation_summary(self, corr_matrix: pd.DataFrame) -> Dict[str, float]:
        """计算相关性汇总统计"""
        try:
            # 获取上三角矩阵（排除对角线）
            upper_triangle = corr_matrix.where(
                np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
            )
            correlations = upper_triangle.stack().values
            
            abs_correlations = np.abs(correlations)
            
            return {
                'mean_correlation': float(np.mean(correlations)),
                'mean_abs_correlation': float(np.mean(abs_correlations)),
                'max_correlation': float(np.max(correlations)),
                'min_correlation': float(np.min(correlations)),
                'max_abs_correlation': float(np.max(abs_correlations)),
                'std_correlation': float(np.std(correlations)),
                'median_correlation': float(np.median(correlations)),
                'q75_correlation': float(np.percentile(abs_correlations, 75)),
                'q95_correlation': float(np.percentile(abs_correlations, 95))
            }
            
        except Exception as e:
            logger.error(f"计算相关性汇总失败: {e}")
            return {}
    
    def perform_correlation_clustering(self, factor_data: pd.DataFrame,
                                     n_clusters: int = None) -> Dict[str, Any]:
        """执行相关性聚类分析"""
        try:
            if factor_data.empty or len(factor_data.columns) < 3:
                return {
                    'clusters': {},
                    'cluster_info': [],
                    'dendrogram_data': {},
                    'silhouette_score': 0.0
                }
            
            # 计算相关性矩阵
            clean_data = factor_data.dropna()
            if len(clean_data) < 10:
                return {
                    'clusters': {},
                    'cluster_info': [],
                    'dendrogram_data': {},
                    'silhouette_score': 0.0
                }
            
            corr_matrix = clean_data.corr(method='pearson').fillna(0)
            
            # 将相关性转换为距离矩阵
            distance_matrix = 1 - np.abs(corr_matrix)
            
            # 层次聚类
            condensed_distances = pdist(distance_matrix, metric='euclidean')
            linkage_matrix = linkage(condensed_distances, method='ward')
            
            # 确定聚类数量
            if n_clusters is None:
                n_clusters = min(max(2, len(factor_data.columns) // 3), 8)
            
            cluster_labels = fcluster(linkage_matrix, n_clusters, criterion='maxclust')
            
            # 组织聚类结果
            clusters = {}
            for i, factor_name in enumerate(corr_matrix.columns):
                cluster_id = int(cluster_labels[i])
                if cluster_id not in clusters:
                    clusters[cluster_id] = []
                clusters[cluster_id].append(factor_name)
            
            # 计算聚类信息
            cluster_info = []
            for cluster_id, factors in clusters.items():
                if len(factors) > 1:
                    # 计算簇内平均相关性
                    cluster_corr_matrix = corr_matrix.loc[factors, factors]
                    upper_triangle = cluster_corr_matrix.where(
                        np.triu(np.ones(cluster_corr_matrix.shape), k=1).astype(bool)
                    )
                    intra_correlations = upper_triangle.stack().values
                    
                    cluster_info.append({
                        'cluster_id': cluster_id,
                        'factors': factors,
                        'size': len(factors),
                        'avg_intra_correlation': float(np.mean(np.abs(intra_correlations))),
                        'max_intra_correlation': float(np.max(np.abs(intra_correlations))),
                        'min_intra_correlation': float(np.min(np.abs(intra_correlations)))
                    })
                else:
                    cluster_info.append({
                        'cluster_id': cluster_id,
                        'factors': factors,
                        'size': 1,
                        'avg_intra_correlation': 0.0,
                        'max_intra_correlation': 0.0,
                        'min_intra_correlation': 0.0
                    })
            
            # 计算轮廓系数（简化版本）
            silhouette_score = self._calculate_simple_silhouette_score(
                corr_matrix, cluster_labels
            )
            
            return {
                'clusters': clusters,
                'cluster_info': cluster_info,
                'dendrogram_data': {
                    'linkage_matrix': linkage_matrix.tolist(),
                    'factor_names': list(corr_matrix.columns)
                },
                'silhouette_score': silhouette_score,
                'optimal_clusters': n_clusters
            }
            
        except Exception as e:
            logger.error(f"相关性聚类分析失败: {e}")
            return {
                'clusters': {},
                'cluster_info': [],
                'dendrogram_data': {},
                'silhouette_score': 0.0
            }
    
    def _calculate_simple_silhouette_score(self, corr_matrix: pd.DataFrame,
                                         cluster_labels: np.ndarray) -> float:
        """计算简化版轮廓系数"""
        try:
            n_factors = len(corr_matrix)
            if n_factors < 2:
                return 0.0
            
            silhouette_scores = []
            
            for i in range(n_factors):
                # 同簇内平均距离
                same_cluster = cluster_labels == cluster_labels[i]
                if np.sum(same_cluster) > 1:
                    a = np.mean(1 - np.abs(corr_matrix.iloc[i, same_cluster]))
                else:
                    a = 0
                
                # 最近异簇平均距离
                b = float('inf')
                for cluster_id in np.unique(cluster_labels):
                    if cluster_id != cluster_labels[i]:
                        other_cluster = cluster_labels == cluster_id
                        if np.sum(other_cluster) > 0:
                            distance = np.mean(1 - np.abs(corr_matrix.iloc[i, other_cluster]))
                            b = min(b, distance)
                
                if b == float('inf'):
                    b = 0
                
                # 轮廓系数
                if max(a, b) > 0:
                    silhouette_scores.append((b - a) / max(a, b))
                else:
                    silhouette_scores.append(0)
            
            return float(np.mean(silhouette_scores))
            
        except Exception as e:
            logger.error(f"计算轮廓系数失败: {e}")
            return 0.0
    
    def detect_multicollinearity(self, factor_data: pd.DataFrame) -> Dict[str, Any]:
        """检测多重共线性"""
        try:
            if factor_data.empty or len(factor_data.columns) < 2:
                return {
                    'vif_scores': {},
                    'condition_number': 0.0,
                    'multicollinearity_level': 'insufficient_data',
                    'problematic_factors': []
                }
            
            clean_data = factor_data.dropna()
            if len(clean_data) < len(factor_data.columns) + 5:
                return {
                    'vif_scores': {},
                    'condition_number': 0.0,
                    'multicollinearity_level': 'insufficient_data',
                    'problematic_factors': []
                }
            
            # 标准化数据
            scaler = StandardScaler()
            scaled_data = scaler.fit_transform(clean_data)
            scaled_df = pd.DataFrame(scaled_data, columns=clean_data.columns)
            
            # 计算方差膨胀因子 (VIF)
            vif_scores = {}
            for i, factor in enumerate(scaled_df.columns):
                try:
                    # 计算R²
                    y = scaled_df[factor]
                    X = scaled_df.drop(columns=[factor])
                    
                    if len(X.columns) > 0:
                        # 简化的R²计算
                        corr_matrix = pd.concat([y, X], axis=1).corr()
                        r_squared = corr_matrix.iloc[0, 1:].abs().max() ** 2
                        
                        # VIF = 1 / (1 - R²)
                        if r_squared < 0.999:
                            vif = 1 / (1 - r_squared)
                        else:
                            vif = 1000.0  # 设置一个很大的值
                        
                        vif_scores[factor] = float(vif)
                    else:
                        vif_scores[factor] = 1.0
                        
                except Exception:
                    vif_scores[factor] = 1.0
            
            # 计算条件数
            try:
                correlation_matrix = scaled_df.corr().fillna(0)
                eigenvalues = np.linalg.eigvals(correlation_matrix)
                eigenvalues = eigenvalues[eigenvalues > 1e-10]  # 避免除零
                condition_number = float(np.sqrt(np.max(eigenvalues) / np.min(eigenvalues)))
            except Exception:
                condition_number = 1.0
            
            # 判断多重共线性水平
            max_vif = max(vif_scores.values()) if vif_scores else 1.0
            
            if max_vif > 10 or condition_number > 30:
                multicollinearity_level = 'severe'
            elif max_vif > 5 or condition_number > 15:
                multicollinearity_level = 'moderate'
            elif max_vif > 2.5 or condition_number > 10:
                multicollinearity_level = 'mild'
            else:
                multicollinearity_level = 'low'
            
            # 识别问题因子
            problematic_factors = [
                {
                    'factor': factor,
                    'vif_score': vif,
                    'severity': 'severe' if vif > 10 else 'moderate' if vif > 5 else 'mild'
                }
                for factor, vif in vif_scores.items() if vif > 2.5
            ]
            
            return {
                'vif_scores': vif_scores,
                'condition_number': condition_number,
                'multicollinearity_level': multicollinearity_level,
                'problematic_factors': sorted(problematic_factors, 
                                           key=lambda x: x['vif_score'], reverse=True)
            }
            
        except Exception as e:
            logger.error(f"多重共线性检测失败: {e}")
            return {
                'vif_scores': {},
                'condition_number': 0.0,
                'multicollinearity_level': 'error',
                'problematic_factors': []
            }
    
    def perform_pca_analysis(self, factor_data: pd.DataFrame,
                           n_components: int = None) -> Dict[str, Any]:
        """执行主成分分析"""
        try:
            if factor_data.empty or len(factor_data.columns) < 2:
                return {
                    'explained_variance_ratio': [],
                    'cumulative_variance_ratio': [],
                    'components': {},
                    'n_components': 0,
                    'total_variance_explained': 0.0
                }
            
            clean_data = factor_data.dropna()
            if len(clean_data) < max(10, len(factor_data.columns)):
                return {
                    'explained_variance_ratio': [],
                    'cumulative_variance_ratio': [],
                    'components': {},
                    'n_components': 0,
                    'total_variance_explained': 0.0
                }
            
            # 标准化数据
            scaler = StandardScaler()
            scaled_data = scaler.fit_transform(clean_data)
            
            # 确定主成分数量
            if n_components is None:
                n_components = min(len(factor_data.columns), len(clean_data) - 1)
            
            # 执行PCA
            pca = PCA(n_components=n_components)
            pca.fit(scaled_data)
            
            # 组织结果
            explained_variance_ratio = pca.explained_variance_ratio_.tolist()
            cumulative_variance_ratio = np.cumsum(explained_variance_ratio).tolist()
            
            # 主成分载荷
            components = {}
            factor_names = list(factor_data.columns)
            
            for i in range(len(explained_variance_ratio)):
                component_name = f'PC{i+1}'
                components[component_name] = {}
                for j, factor_name in enumerate(factor_names):
                    components[component_name][factor_name] = float(pca.components_[i, j])
            
            # 找到解释80%方差所需的主成分数量
            optimal_components = next(
                (i + 1 for i, cum_var in enumerate(cumulative_variance_ratio) if cum_var >= 0.8),
                len(explained_variance_ratio)
            )
            
            return {
                'explained_variance_ratio': explained_variance_ratio,
                'cumulative_variance_ratio': cumulative_variance_ratio,
                'components': components,
                'n_components': len(explained_variance_ratio),
                'optimal_components': optimal_components,
                'total_variance_explained': float(cumulative_variance_ratio[-1]),
                'factor_names': factor_names
            }
            
        except Exception as e:
            logger.error(f"PCA分析失败: {e}")
            return {
                'explained_variance_ratio': [],
                'cumulative_variance_ratio': [],
                'components': {},
                'n_components': 0,
                'total_variance_explained': 0.0
            }
    
    def save_correlation_results(self, factor1_id: str, factor1_type: str,
                               factor2_id: str, factor2_type: str,
                               correlation_coefficient: float,
                               p_value: float = None, sample_size: int = None,
                               db: Session = None) -> bool:
        """保存相关性结果到数据库"""
        try:
            if db is None:
                db = next(get_db())
            
            correlation_record = FactorCorrelation(
                factor1_id=factor1_id,
                factor1_type=factor1_type,
                factor2_id=factor2_id,
                factor2_type=factor2_type,
                correlation_coefficient=correlation_coefficient,
                p_value=p_value,
                analysis_date=datetime.utcnow(),
                sample_size=sample_size
            )
            
            db.add(correlation_record)
            db.commit()
            
            logger.info(f"相关性结果已保存: {factor1_id} - {factor2_id}")
            return True
            
        except Exception as e:
            if db:
                db.rollback()
            logger.error(f"保存相关性结果失败: {e}")
            return False
    
    def get_factor_correlation_history(self, factor_id: str, days: int = 30,
                                     db: Session = None) -> List[Dict[str, Any]]:
        """获取因子相关性历史记录"""
        try:
            if db is None:
                db = next(get_db())
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            correlations = db.query(FactorCorrelation).filter(
                (FactorCorrelation.factor1_id == factor_id) | 
                (FactorCorrelation.factor2_id == factor_id),
                FactorCorrelation.analysis_date >= cutoff_date
            ).order_by(FactorCorrelation.analysis_date.desc()).all()
            
            results = []
            for corr in correlations:
                other_factor_id = corr.factor2_id if corr.factor1_id == factor_id else corr.factor1_id
                other_factor_type = corr.factor2_type if corr.factor1_id == factor_id else corr.factor1_type
                
                results.append({
                    'other_factor_id': other_factor_id,
                    'other_factor_type': other_factor_type,
                    'correlation_coefficient': corr.correlation_coefficient,
                    'p_value': corr.p_value,
                    'sample_size': corr.sample_size,
                    'analysis_date': corr.analysis_date
                })
            
            return results
            
        except Exception as e:
            logger.error(f"获取相关性历史失败: {e}")
            return []


# 全局因子相关性服务实例
factor_correlation_service = FactorCorrelationService()