"""
策略配置管理API接口
提供策略配置的增删改查、权重验证、导入导出等功能
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Path, Depends, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.builtin_factors import (
    StrategyConfigCreate, StrategyConfigUpdate, StrategyConfigResponse,
    SelectedFactor, PaginatedStrategies, BatchOperationResult,
    StrategyPreviewResult, WeightPreset, WeightOptimizationResult
)
from app.services.strategy_config_service import strategy_config_service
from app.services.weight_optimization_service import weight_optimization_service

router = APIRouter(prefix="/strategy-configs", tags=["策略配置管理"])


# 请求/响应模型
class StrategyConfigQuery(BaseModel):
    """策略配置查询参数"""
    page: int = 1
    size: int = 20
    created_by: Optional[str] = None
    tags: Optional[List[str]] = None
    search: Optional[str] = None
    sort_by: str = "created_at"
    sort_order: str = "desc"


class StrategyDuplicationRequest(BaseModel):
    """策略复制请求"""
    new_name: Optional[str] = None
    created_by: Optional[str] = None


class BatchDeleteRequest(BaseModel):
    """批量删除请求"""
    config_ids: List[str]


class StrategyImportRequest(BaseModel):
    """策略导入请求"""
    import_data: Dict[str, Any]
    created_by: Optional[str] = None


class WeightValidationRequest(BaseModel):
    """权重验证请求"""
    factors: List[SelectedFactor]


class WeightNormalizationRequest(BaseModel):
    """权重标准化请求"""
    factors: List[SelectedFactor]
    target_sum: float = 1.0


class WeightPresetRequest(BaseModel):
    """权重预设应用请求"""
    factors: List[SelectedFactor]
    preset_id: str


class WeightOptimizationRequest(BaseModel):
    """权重优化请求"""
    factors: List[SelectedFactor]
    optimization_method: str = "correlation_adjusted"


class StrategyUsageRequest(BaseModel):
    """策略使用记录请求"""
    config_id: str


@router.post("/", response_model=StrategyConfigResponse)
async def create_strategy_config(
    strategy_data: StrategyConfigCreate,
    created_by: Optional[str] = Query(None, description="创建者ID"),
    db: Session = Depends(get_db)
):
    """
    创建策略配置
    
    - **strategy_data**: 策略配置数据
    - **created_by**: 创建者ID（可选）
    """
    try:
        result = strategy_config_service.create_strategy_config(
            strategy_data, created_by, db
        )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建策略配置失败: {str(e)}")


@router.get("/", response_model=PaginatedStrategies)
async def list_strategy_configs(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    created_by: Optional[str] = Query(None, description="创建者筛选"),
    tags: Optional[str] = Query(None, description="标签筛选，逗号分隔"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向"),
    db: Session = Depends(get_db)
):
    """
    获取策略配置列表
    
    支持分页、筛选、搜索和排序
    """
    try:
        # 解析标签
        tag_list = tags.split(',') if tags else None
        
        result = strategy_config_service.list_strategy_configs(
            page=page,
            size=size,
            created_by=created_by,
            tags=tag_list,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            db=db
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取策略列表失败: {str(e)}")


@router.get("/{config_id}", response_model=StrategyConfigResponse)
async def get_strategy_config(
    config_id: str = Path(..., description="策略配置ID"),
    db: Session = Depends(get_db)
):
    """获取指定策略配置详情"""
    try:
        result = strategy_config_service.get_strategy_config(config_id, db)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"策略配置不存在: {config_id}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取策略配置失败: {str(e)}")


@router.put("/{config_id}", response_model=StrategyConfigResponse)
async def update_strategy_config(
    config_id: str = Path(..., description="策略配置ID"),
    strategy_data: StrategyConfigUpdate = None,
    db: Session = Depends(get_db)
):
    """更新策略配置"""
    try:
        result = strategy_config_service.update_strategy_config(
            config_id, strategy_data, db
        )
        
        if not result:
            raise HTTPException(status_code=404, detail=f"策略配置不存在: {config_id}")
        
        return result
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新策略配置失败: {str(e)}")


@router.delete("/{config_id}")
async def delete_strategy_config(
    config_id: str = Path(..., description="策略配置ID"),
    db: Session = Depends(get_db)
):
    """删除策略配置"""
    try:
        success = strategy_config_service.delete_strategy_config(config_id, db)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"策略配置不存在: {config_id}")
        
        return {"message": "策略配置删除成功", "config_id": config_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除策略配置失败: {str(e)}")


@router.post("/{config_id}/duplicate", response_model=StrategyConfigResponse)
async def duplicate_strategy_config(
    config_id: str = Path(..., description="策略配置ID"),
    duplication_request: StrategyDuplicationRequest = None,
    db: Session = Depends(get_db)
):
    """复制策略配置"""
    try:
        if not duplication_request:
            duplication_request = StrategyDuplicationRequest()
        
        result = strategy_config_service.duplicate_strategy_config(
            config_id=config_id,
            new_name=duplication_request.new_name,
            created_by=duplication_request.created_by,
            db=db
        )
        
        if not result:
            raise HTTPException(status_code=404, detail=f"策略配置不存在: {config_id}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"复制策略配置失败: {str(e)}")


@router.post("/batch-delete", response_model=BatchOperationResult)
async def batch_delete_strategies(
    request: BatchDeleteRequest,
    db: Session = Depends(get_db)
):
    """批量删除策略配置"""
    try:
        result = strategy_config_service.batch_delete_strategies(
            request.config_ids, db
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量删除失败: {str(e)}")


@router.get("/{config_id}/export")
async def export_strategy_config(
    config_id: str = Path(..., description="策略配置ID"),
    db: Session = Depends(get_db)
):
    """导出策略配置为JSON"""
    try:
        export_data = strategy_config_service.export_strategy_config(config_id, db)
        
        if not export_data:
            raise HTTPException(status_code=404, detail=f"策略配置不存在: {config_id}")
        
        return JSONResponse(
            content=export_data,
            headers={
                "Content-Disposition": f"attachment; filename=strategy_{config_id}.json"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出策略配置失败: {str(e)}")


@router.post("/import", response_model=StrategyConfigResponse)
async def import_strategy_config(
    request: StrategyImportRequest,
    db: Session = Depends(get_db)
):
    """从JSON导入策略配置"""
    try:
        result = strategy_config_service.import_strategy_config(
            import_data=request.import_data,
            created_by=request.created_by,
            db=db
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入策略配置失败: {str(e)}")


@router.post("/import-file", response_model=StrategyConfigResponse)
async def import_strategy_config_file(
    file: UploadFile = File(..., description="策略配置JSON文件"),
    created_by: Optional[str] = Query(None, description="创建者ID"),
    db: Session = Depends(get_db)
):
    """从上传的JSON文件导入策略配置"""
    try:
        # 检查文件类型
        if not file.filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="只支持JSON文件格式")
        
        # 读取文件内容
        content = await file.read()
        
        try:
            import json
            import_data = json.loads(content.decode('utf-8'))
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="无效的JSON文件格式")
        
        # 导入策略配置
        result = strategy_config_service.import_strategy_config(
            import_data=import_data,
            created_by=created_by,
            db=db
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件导入失败: {str(e)}")


@router.post("/preview", response_model=StrategyPreviewResult)
async def preview_strategy(
    factors: List[SelectedFactor]
):
    """获取策略预览"""
    try:
        result = strategy_config_service.get_strategy_preview(factors)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"策略预览失败: {str(e)}")


@router.post("/{config_id}/usage")
async def record_strategy_usage(
    config_id: str = Path(..., description="策略配置ID"),
    db: Session = Depends(get_db)
):
    """记录策略使用"""
    try:
        strategy_config_service.record_strategy_usage(config_id, db)
        return {"message": "使用记录已更新", "config_id": config_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"记录使用失败: {str(e)}")


# 权重管理相关API
@router.post("/weights/validate")
async def validate_weights(request: WeightValidationRequest):
    """验证因子权重配置"""
    try:
        result = weight_optimization_service.validate_weights(request.factors)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"权重验证失败: {str(e)}")


@router.post("/weights/normalize")
async def normalize_weights(request: WeightNormalizationRequest):
    """标准化权重"""
    try:
        result = weight_optimization_service.normalize_weights(
            request.factors, request.target_sum
        )
        
        # 返回标准化后的因子配置
        return {"factors": result, "target_sum": request.target_sum}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"权重标准化失败: {str(e)}")


@router.get("/weights/presets", response_model=List[WeightPreset])
async def get_weight_presets():
    """获取权重预设列表"""
    try:
        result = weight_optimization_service.get_weight_presets()
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取权重预设失败: {str(e)}")


@router.post("/weights/apply-preset")
async def apply_weight_preset(request: WeightPresetRequest):
    """应用权重预设"""
    try:
        result = weight_optimization_service.apply_weight_preset(
            request.factors, request.preset_id
        )
        
        return {"factors": result, "preset_id": request.preset_id}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"应用权重预设失败: {str(e)}")


@router.post("/weights/optimize", response_model=WeightOptimizationResult)
async def optimize_weights(request: WeightOptimizationRequest):
    """优化权重配置"""
    try:
        result = weight_optimization_service.optimize_weights(
            factors=request.factors,
            optimization_method=request.optimization_method
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"权重优化失败: {str(e)}")


@router.post("/weights/suggestions")
async def get_weight_suggestions(request: WeightValidationRequest):
    """获取权重配置建议"""
    try:
        result = weight_optimization_service.generate_weight_suggestions(request.factors)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成权重建议失败: {str(e)}")


# 统计和分析相关API
@router.get("/statistics")
async def get_strategy_statistics(
    created_by: Optional[str] = Query(None, description="创建者筛选"),
    days: int = Query(30, description="统计天数"),
    db: Session = Depends(get_db)
):
    """获取策略配置统计信息"""
    try:
        # 这里可以实现策略配置的统计分析
        # 目前返回基础统计信息
        
        # 获取策略列表进行统计
        strategies = strategy_config_service.list_strategy_configs(
            page=1, size=1000, created_by=created_by, db=db
        )
        
        # 计算统计信息
        total_strategies = strategies.total
        
        # 按标签统计
        tag_counts = {}
        category_counts = {}
        
        for strategy in strategies.items:
            # 统计标签
            for tag in strategy.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            # 统计因子分类
            for factor in strategy.factors:
                if factor.is_enabled:
                    # 这里需要获取因子信息来确定分类
                    # 简化处理，按因子名称前缀分类
                    if 'sma' in factor.factor_id or 'ema' in factor.factor_id:
                        category = 'trend'
                    elif 'rsi' in factor.factor_id or 'macd' in factor.factor_id:
                        category = 'momentum'
                    elif 'volume' in factor.factor_id or 'obv' in factor.factor_id:
                        category = 'volume'
                    else:
                        category = 'other'
                    
                    category_counts[category] = category_counts.get(category, 0) + 1
        
        # 使用频率统计
        usage_stats = {
            "high_usage": sum(1 for s in strategies.items if s.usage_count > 10),
            "medium_usage": sum(1 for s in strategies.items if 3 <= s.usage_count <= 10),
            "low_usage": sum(1 for s in strategies.items if s.usage_count < 3)
        }
        
        return {
            "total_strategies": total_strategies,
            "tag_distribution": tag_counts,
            "factor_category_distribution": category_counts,
            "usage_distribution": usage_stats,
            "average_factors_per_strategy": sum(len(s.factors) for s in strategies.items) / total_strategies if total_strategies > 0 else 0,
            "active_strategies": sum(1 for s in strategies.items if s.usage_count > 0),
            "template_based_strategies": sum(1 for s in strategies.items if "template" in s.tags)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@router.get("/popular")
async def get_popular_strategies(
    limit: int = Query(10, ge=1, le=50, description="返回数量限制"),
    db: Session = Depends(get_db)
):
    """获取热门策略配置"""
    try:
        # 按使用次数排序获取热门策略
        strategies = strategy_config_service.list_strategy_configs(
            page=1, size=limit, sort_by="usage_count", sort_order="desc", db=db
        )
        
        return {
            "popular_strategies": strategies.items,
            "total_count": strategies.total
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取热门策略失败: {str(e)}")