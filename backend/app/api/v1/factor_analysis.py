"""
因子分析API接口
提供因子统计分析、相关性计算、有效性评估等功能
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Path, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.builtin_factors import (
    FactorStatisticsResult, CorrelationMatrix, EffectivenessAnalysisResult,
    FactorStatisticsResponse, QuantileAnalysisResult, EffectivenessMetrics
)
from app.services.factor_statistics_service import factor_statistics_service
from app.services.factor_correlation_service import factor_correlation_service
from app.services.factor_effectiveness_service import factor_effectiveness_service

router = APIRouter(prefix="/factor-analysis", tags=["因子分析"])


# 请求/响应模型
class FactorDataRequest(BaseModel):
    """因子数据请求"""
    factor_values: List[float]
    factor_id: Optional[str] = None
    factor_name: Optional[str] = None
    stock_symbols: Optional[List[str]] = None


class MultiFactorDataRequest(BaseModel):
    """多因子数据请求"""
    factor_data: Dict[str, List[float]]  # factor_id -> values
    stock_symbols: Optional[List[str]] = None


class CorrelationAnalysisRequest(BaseModel):
    """相关性分析请求"""
    factor_data: Dict[str, List[float]]
    method: str = "pearson"
    threshold: float = 0.7


class EffectivenessAnalysisRequest(BaseModel):
    """有效性分析请求"""
    factor_values: List[float]
    factor_id: Optional[str] = None
    stock_metadata: Optional[Dict[str, Any]] = None


class ComparisonAnalysisRequest(BaseModel):
    """因子比较分析请求"""
    factor_data: Dict[str, List[float]]
    analysis_types: List[str] = ["statistics", "correlation", "effectiveness"]


class QuantileAnalysisRequest(BaseModel):
    """分位数分析请求"""
    factor_values: List[float]
    stock_returns: Optional[List[float]] = None


@router.post("/statistics", response_model=Dict[str, Any])
async def analyze_factor_statistics(request: FactorDataRequest):
    """
    分析单个因子的统计特征
    
    - **factor_values**: 因子值列表
    - **factor_id**: 因子ID（可选）
    - **factor_name**: 因子名称（可选）
    """
    try:
        # 转换为pandas Series
        factor_series = pd.Series(request.factor_values)
        
        if len(factor_series) == 0:
            raise HTTPException(status_code=400, detail="因子数据不能为空")
        
        # 基础统计分析
        basic_stats = factor_statistics_service.calculate_basic_statistics(factor_series)
        
        # 分布分析
        distribution_analysis = factor_statistics_service.analyze_factor_distribution(factor_series)
        
        # 分位数分析
        quantile_analysis = factor_statistics_service.calculate_quantile_analysis(factor_series)
        
        return {
            "factor_id": request.factor_id or "unknown",
            "factor_name": request.factor_name or "Unknown Factor",
            "basic_statistics": basic_stats,
            "distribution_analysis": distribution_analysis,
            "quantile_analysis": quantile_analysis,
            "sample_size": len(factor_series),
            "analysis_timestamp": pd.Timestamp.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"统计分析失败: {str(e)}")


@router.post("/correlation-matrix")
async def calculate_correlation_matrix(request: CorrelationAnalysisRequest):
    """
    计算多因子相关性矩阵
    
    - **factor_data**: 因子数据字典 {factor_id: values}
    - **method**: 相关性计算方法 (pearson/spearman/kendall)
    - **threshold**: 高相关性阈值
    """
    try:
        if len(request.factor_data) < 2:
            raise HTTPException(status_code=400, detail="至少需要2个因子进行相关性分析")
        
        # 转换为DataFrame
        factor_df = pd.DataFrame(request.factor_data)
        
        if factor_df.empty:
            raise HTTPException(status_code=400, detail="因子数据不能为空")
        
        # 计算相关性矩阵
        correlation_result = factor_correlation_service.calculate_correlation_matrix(
            factor_df, method=request.method
        )
        
        # 分析相关性对
        correlation_pairs = factor_correlation_service.analyze_factor_correlation_pairs(
            factor_df, threshold=request.threshold
        )
        
        return {
            "correlation_matrix": correlation_result,
            "correlation_analysis": correlation_pairs,
            "analysis_timestamp": pd.Timestamp.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"相关性分析失败: {str(e)}")


@router.post("/clustering")
async def perform_factor_clustering(request: CorrelationAnalysisRequest):
    """
    执行因子聚类分析
    
    基于因子相关性进行层次聚类
    """
    try:
        if len(request.factor_data) < 3:
            raise HTTPException(status_code=400, detail="聚类分析至少需要3个因子")
        
        # 转换为DataFrame
        factor_df = pd.DataFrame(request.factor_data)
        
        # 执行聚类分析
        clustering_result = factor_correlation_service.perform_correlation_clustering(factor_df)
        
        return {
            "clustering_results": clustering_result,
            "analysis_timestamp": pd.Timestamp.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"聚类分析失败: {str(e)}")


@router.post("/multicollinearity")
async def detect_multicollinearity(request: MultiFactorDataRequest):
    """
    检测多重共线性
    
    计算VIF、条件数等指标
    """
    try:
        if len(request.factor_data) < 2:
            raise HTTPException(status_code=400, detail="多重共线性检测至少需要2个因子")
        
        # 转换为DataFrame
        factor_df = pd.DataFrame(request.factor_data)
        
        # 检测多重共线性
        multicollinearity_result = factor_correlation_service.detect_multicollinearity(factor_df)
        
        return {
            "multicollinearity_analysis": multicollinearity_result,
            "analysis_timestamp": pd.Timestamp.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"多重共线性检测失败: {str(e)}")


@router.post("/pca")
async def perform_pca_analysis(
    request: MultiFactorDataRequest,
    n_components: Optional[int] = Query(None, description="主成分数量")
):
    """
    执行主成分分析 (PCA)
    
    - **factor_data**: 因子数据
    - **n_components**: 主成分数量（可选）
    """
    try:
        if len(request.factor_data) < 2:
            raise HTTPException(status_code=400, detail="PCA分析至少需要2个因子")
        
        # 转换为DataFrame
        factor_df = pd.DataFrame(request.factor_data)
        
        # 执行PCA分析
        pca_result = factor_correlation_service.perform_pca_analysis(
            factor_df, n_components=n_components
        )
        
        return {
            "pca_analysis": pca_result,
            "analysis_timestamp": pd.Timestamp.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PCA分析失败: {str(e)}")


@router.post("/effectiveness")
async def analyze_factor_effectiveness(request: EffectivenessAnalysisRequest):
    """
    分析因子有效性
    
    评估因子的区分度、稳定性、筛选能力等
    """
    try:
        # 转换为pandas Series
        factor_series = pd.Series(request.factor_values)
        
        if len(factor_series) == 0:
            raise HTTPException(status_code=400, detail="因子数据不能为空")
        
        # 构建股票元数据（如果提供）
        stock_metadata = None
        if request.stock_metadata:
            stock_metadata = pd.DataFrame([request.stock_metadata])
        
        # 执行有效性分析
        effectiveness_result = factor_effectiveness_service.analyze_factor_effectiveness(
            factor_series, stock_metadata
        )
        
        return {
            "factor_id": request.factor_id or "unknown",
            "effectiveness_analysis": effectiveness_result,
            "analysis_timestamp": pd.Timestamp.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"有效性分析失败: {str(e)}")


@router.post("/compare-factors")
async def compare_factor_effectiveness(request: ComparisonAnalysisRequest):
    """
    比较多个因子的有效性
    
    - **factor_data**: 因子数据字典
    - **analysis_types**: 分析类型列表
    """
    try:
        if len(request.factor_data) < 2:
            raise HTTPException(status_code=400, detail="因子比较至少需要2个因子")
        
        # 转换数据格式
        factor_series_dict = {
            factor_id: pd.Series(values) 
            for factor_id, values in request.factor_data.items()
        }
        
        results = {}
        
        # 统计特征比较
        if "statistics" in request.analysis_types:
            statistics_comparison = {}
            for factor_id, factor_series in factor_series_dict.items():
                statistics_comparison[factor_id] = factor_statistics_service.calculate_basic_statistics(factor_series)
            results["statistics_comparison"] = statistics_comparison
        
        # 相关性分析
        if "correlation" in request.analysis_types:
            factor_df = pd.DataFrame(request.factor_data)
            correlation_result = factor_correlation_service.calculate_correlation_matrix(factor_df)
            results["correlation_analysis"] = correlation_result
        
        # 有效性比较
        if "effectiveness" in request.analysis_types:
            effectiveness_comparison = factor_effectiveness_service.compare_factor_effectiveness(
                factor_series_dict
            )
            results["effectiveness_comparison"] = effectiveness_comparison
        
        return {
            "comparison_results": results,
            "factor_count": len(request.factor_data),
            "analysis_timestamp": pd.Timestamp.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"因子比较失败: {str(e)}")


@router.post("/quantile-analysis")
async def perform_quantile_analysis(request: QuantileAnalysisRequest):
    """
    执行分位数分析
    
    - **factor_values**: 因子值
    - **stock_returns**: 股票收益率（可选）
    """
    try:
        factor_series = pd.Series(request.factor_values)
        
        if len(factor_series) == 0:
            raise HTTPException(status_code=400, detail="因子数据不能为空")
        
        # 转换收益率数据
        returns_series = None
        if request.stock_returns:
            returns_series = pd.Series(request.stock_returns)
        
        # 执行分位数分析
        quantile_result = factor_statistics_service.calculate_quantile_analysis(
            factor_series, returns_series
        )
        
        return {
            "quantile_analysis": quantile_result,
            "analysis_timestamp": pd.Timestamp.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分位数分析失败: {str(e)}")


@router.post("/combination-effectiveness")
async def analyze_factor_combination(
    factor_data: Dict[str, List[float]],
    weights: Optional[List[float]] = None
):
    """
    分析因子组合的有效性
    
    - **factor_data**: 因子数据字典
    - **weights**: 因子权重（可选，默认等权重）
    """
    try:
        if len(factor_data) < 2:
            raise HTTPException(status_code=400, detail="因子组合至少需要2个因子")
        
        # 转换数据格式
        factor_series_list = [pd.Series(values) for values in factor_data.values()]
        
        # 执行组合有效性分析
        combination_result = factor_effectiveness_service.analyze_factor_combination_effectiveness(
            factor_series_list, weights
        )
        
        return {
            "combination_analysis": combination_result,
            "factor_names": list(factor_data.keys()),
            "analysis_timestamp": pd.Timestamp.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"组合有效性分析失败: {str(e)}")


@router.get("/statistics/history/{factor_id}")
async def get_factor_statistics_history(
    factor_id: str = Path(..., description="因子ID"),
    days: int = Query(30, ge=1, le=365, description="历史天数"),
    db: Session = Depends(get_db)
):
    """获取因子统计分析历史记录"""
    try:
        history_records = factor_statistics_service.get_factor_statistics_history(
            factor_id, days, db
        )
        
        return {
            "factor_id": factor_id,
            "history_records": history_records,
            "record_count": len(history_records),
            "query_days": days
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史记录失败: {str(e)}")


@router.get("/correlation/history/{factor_id}")
async def get_factor_correlation_history(
    factor_id: str = Path(..., description="因子ID"),
    days: int = Query(30, ge=1, le=365, description="历史天数"),
    db: Session = Depends(get_db)
):
    """获取因子相关性分析历史记录"""
    try:
        correlation_history = factor_correlation_service.get_factor_correlation_history(
            factor_id, days, db
        )
        
        return {
            "factor_id": factor_id,
            "correlation_history": correlation_history,
            "record_count": len(correlation_history),
            "query_days": days
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取相关性历史失败: {str(e)}")


@router.post("/batch-analysis")
async def perform_batch_analysis(
    factor_data: Dict[str, List[float]],
    analysis_types: List[str] = ["statistics", "correlation", "effectiveness"]
):
    """
    批量因子分析
    
    对多个因子执行完整的分析流程
    """
    try:
        if not factor_data:
            raise HTTPException(status_code=400, detail="因子数据不能为空")
        
        results = {
            "factor_count": len(factor_data),
            "analysis_types": analysis_types,
            "results": {}
        }
        
        # 转换数据格式
        factor_df = pd.DataFrame(factor_data)
        factor_series_dict = {
            factor_id: pd.Series(values) 
            for factor_id, values in factor_data.items()
        }
        
        # 统计分析
        if "statistics" in analysis_types:
            statistics_results = {}
            for factor_id, factor_series in factor_series_dict.items():
                basic_stats = factor_statistics_service.calculate_basic_statistics(factor_series)
                distribution_analysis = factor_statistics_service.analyze_factor_distribution(factor_series)
                
                statistics_results[factor_id] = {
                    "basic_statistics": basic_stats,
                    "distribution_analysis": distribution_analysis
                }
            
            results["results"]["statistics"] = statistics_results
        
        # 相关性分析
        if "correlation" in analysis_types and len(factor_data) > 1:
            correlation_matrix = factor_correlation_service.calculate_correlation_matrix(factor_df)
            correlation_pairs = factor_correlation_service.analyze_factor_correlation_pairs(factor_df)
            
            results["results"]["correlation"] = {
                "correlation_matrix": correlation_matrix,
                "correlation_pairs": correlation_pairs
            }
        
        # 有效性分析
        if "effectiveness" in analysis_types:
            effectiveness_results = {}
            for factor_id, factor_series in factor_series_dict.items():
                effectiveness_analysis = factor_effectiveness_service.analyze_factor_effectiveness(factor_series)
                effectiveness_results[factor_id] = effectiveness_analysis
            
            # 比较分析
            effectiveness_comparison = factor_effectiveness_service.compare_factor_effectiveness(
                factor_series_dict
            )
            
            results["results"]["effectiveness"] = {
                "individual_analysis": effectiveness_results,
                "comparison": effectiveness_comparison
            }
        
        results["analysis_timestamp"] = pd.Timestamp.now().isoformat()
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量分析失败: {str(e)}")


@router.get("/analysis-summary")
async def get_analysis_summary(
    factor_ids: List[str] = Query(..., description="因子ID列表"),
    days: int = Query(7, ge=1, le=30, description="统计天数"),
    db: Session = Depends(get_db)
):
    """
    获取因子分析汇总信息
    
    提供因子分析的概览和趋势信息
    """
    try:
        summary = {
            "factor_count": len(factor_ids),
            "analysis_period_days": days,
            "factors": {},
            "overall_summary": {}
        }
        
        all_scores = []
        
        # 获取每个因子的最新分析结果
        for factor_id in factor_ids:
            factor_summary = {
                "latest_statistics": None,
                "recent_correlations": [],
                "trend": "stable"
            }
            
            # 获取统计历史
            stats_history = factor_statistics_service.get_factor_statistics_history(
                factor_id, days, db
            )
            
            if stats_history:
                latest_stats = stats_history[0]
                factor_summary["latest_statistics"] = {
                    "effectiveness_score": latest_stats.effectiveness_score,
                    "analysis_date": latest_stats.analysis_date.isoformat(),
                    "mean": latest_stats.mean,
                    "std": latest_stats.std,
                    "null_ratio": latest_stats.null_ratio
                }
                all_scores.append(latest_stats.effectiveness_score)
                
                # 分析趋势
                if len(stats_history) > 1:
                    recent_score = latest_stats.effectiveness_score
                    older_score = stats_history[-1].effectiveness_score
                    
                    if recent_score > older_score + 5:
                        factor_summary["trend"] = "improving"
                    elif recent_score < older_score - 5:
                        factor_summary["trend"] = "declining"
            
            # 获取相关性历史
            corr_history = factor_correlation_service.get_factor_correlation_history(
                factor_id, days, db
            )
            
            factor_summary["recent_correlations"] = [
                {
                    "other_factor": corr["other_factor_id"],
                    "correlation": corr["correlation_coefficient"],
                    "date": corr["analysis_date"].isoformat()
                }
                for corr in corr_history[:5]  # 最近5条记录
            ]
            
            summary["factors"][factor_id] = factor_summary
        
        # 整体汇总
        if all_scores:
            summary["overall_summary"] = {
                "average_effectiveness": float(np.mean(all_scores)),
                "min_effectiveness": float(np.min(all_scores)),
                "max_effectiveness": float(np.max(all_scores)),
                "effectiveness_std": float(np.std(all_scores)),
                "high_quality_factors": len([s for s in all_scores if s > 70]),
                "low_quality_factors": len([s for s in all_scores if s < 50])
            }
        
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分析汇总失败: {str(e)}")