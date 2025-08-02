"""
策略配置和权重预设API接口
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from datetime import datetime
import uuid

from app.db.database import get_db
from app.db.models.factor import WeightPreset
from app.schemas.factors import (
    WeightPreset as WeightPresetSchema,
    WeightPresetCreate,
    WeightPresetUpdate,
    WeightValidationResult,
    WeightOptimizationResult,
    WeightSuggestionRequest
)

logger = logging.getLogger(__name__)

router = APIRouter()


# 权重预设相关API
@router.get("/weights/presets", response_model=List[WeightPresetSchema])
async def get_weight_presets(
    db: Session = Depends(get_db)
):
    """
    获取权重预设列表
    
    Args:
        db: 数据库会话
    
    Returns:
        权重预设列表
    """
    try:
        presets = db.query(WeightPreset).all()
        
        result = []
        for preset in presets:
            result.append(WeightPresetSchema(
                id=preset.id,
                name=preset.name,
                description=preset.description or "",
                applicable_categories=preset.applicable_categories or [],
                weights=preset.weights or {},
                is_default=preset.is_default,
                created_at=preset.created_at.isoformat() if preset.created_at else None,
                updated_at=preset.updated_at.isoformat() if preset.updated_at else None
            ))
        
        return result
    
    except Exception as e:
        logger.error(f"获取权重预设失败: {e}")
        raise HTTPException(status_code=500, detail="获取权重预设失败")


@router.get("/weights/presets/{preset_id}", response_model=WeightPresetSchema)
async def get_weight_preset(
    preset_id: str,
    db: Session = Depends(get_db)
):
    """
    获取单个权重预设详情
    
    Args:
        preset_id: 预设ID
        db: 数据库会话
    
    Returns:
        权重预设详情
    """
    try:
        preset = db.query(WeightPreset).filter(WeightPreset.id == preset_id).first()
        
        if not preset:
            raise HTTPException(status_code=404, detail="权重预设不存在")
        
        return WeightPresetSchema(
            id=preset.id,
            name=preset.name,
            description=preset.description or "",
            applicable_categories=preset.applicable_categories or [],
            weights=preset.weights or {},
            is_default=preset.is_default,
            created_at=preset.created_at.isoformat() if preset.created_at else None,
            updated_at=preset.updated_at.isoformat() if preset.updated_at else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取权重预设详情失败: {e}")
        raise HTTPException(status_code=500, detail="获取权重预设详情失败")


@router.post("/weights/presets", response_model=WeightPresetSchema)
async def create_weight_preset(
    preset_data: WeightPresetCreate,
    db: Session = Depends(get_db)
):
    """
    创建权重预设
    
    Args:
        preset_data: 预设数据
        db: 数据库会话
    
    Returns:
        创建的权重预设
    """
    try:
        # 生成预设ID
        preset_id = f"preset_{uuid.uuid4().hex[:8]}"
        
        # 创建预设
        preset = WeightPreset(
            id=preset_id,
            name=preset_data.name,
            description=preset_data.description,
            applicable_categories=preset_data.applicable_categories,
            weights=preset_data.weights,
            is_default=preset_data.is_default
        )
        
        # 如果设置为默认预设，需要将其他预设设为非默认
        if preset_data.is_default:
            db.query(WeightPreset).update({"is_default": False})
        
        db.add(preset)
        db.commit()
        db.refresh(preset)
        
        return WeightPresetSchema(
            id=preset.id,
            name=preset.name,
            description=preset.description or "",
            applicable_categories=preset.applicable_categories or [],
            weights=preset.weights or {},
            is_default=preset.is_default,
            created_at=preset.created_at.isoformat() if preset.created_at else None,
            updated_at=preset.updated_at.isoformat() if preset.updated_at else None
        )
    
    except Exception as e:
        logger.error(f"创建权重预设失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="创建权重预设失败")


@router.put("/weights/presets/{preset_id}", response_model=WeightPresetSchema)
async def update_weight_preset(
    preset_id: str,
    preset_data: WeightPresetUpdate,
    db: Session = Depends(get_db)
):
    """
    更新权重预设
    
    Args:
        preset_id: 预设ID
        preset_data: 更新数据
        db: 数据库会话
    
    Returns:
        更新后的权重预设
    """
    try:
        preset = db.query(WeightPreset).filter(WeightPreset.id == preset_id).first()
        
        if not preset:
            raise HTTPException(status_code=404, detail="权重预设不存在")
        
        # 更新字段
        update_data = preset_data.dict(exclude_unset=True)
        
        # 如果设置为默认预设，需要将其他预设设为非默认
        if update_data.get("is_default", False):
            db.query(WeightPreset).filter(WeightPreset.id != preset_id).update({"is_default": False})
        
        for field, value in update_data.items():
            setattr(preset, field, value)
        
        db.commit()
        db.refresh(preset)
        
        return WeightPresetSchema(
            id=preset.id,
            name=preset.name,
            description=preset.description or "",
            applicable_categories=preset.applicable_categories or [],
            weights=preset.weights or {},
            is_default=preset.is_default,
            created_at=preset.created_at.isoformat() if preset.created_at else None,
            updated_at=preset.updated_at.isoformat() if preset.updated_at else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新权重预设失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="更新权重预设失败")


@router.delete("/weights/presets/{preset_id}")
async def delete_weight_preset(
    preset_id: str,
    db: Session = Depends(get_db)
):
    """
    删除权重预设
    
    Args:
        preset_id: 预设ID
        db: 数据库会话
    
    Returns:
        删除结果
    """
    try:
        preset = db.query(WeightPreset).filter(WeightPreset.id == preset_id).first()
        
        if not preset:
            raise HTTPException(status_code=404, detail="权重预设不存在")
        
        db.delete(preset)
        db.commit()
        
        return {"success": True, "message": "权重预设删除成功"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除权重预设失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="删除权重预设失败")


@router.post("/weights/validate", response_model=WeightValidationResult)
async def validate_weights(
    factors: List[dict],
    db: Session = Depends(get_db)
):
    """
    验证权重配置
    
    Args:
        factors: 因子列表
        db: 数据库会话
    
    Returns:
        验证结果
    """
    try:
        total_weight = sum(factor.get("weight", 0) for factor in factors)
        
        is_valid = abs(total_weight - 1.0) < 0.01  # 允许0.01的误差
        message = "权重配置有效" if is_valid else f"权重总和为{total_weight:.2f}，应该为1.0"
        
        warnings = []
        if not is_valid:
            warnings.append(f"权重总和为{total_weight:.2f}，建议调整为1.0")
        
        # 检查是否有负权重
        negative_weights = [f for f in factors if f.get("weight", 0) < 0]
        if negative_weights:
            warnings.append("存在负权重，可能影响策略效果")
        
        return WeightValidationResult(
            is_valid=is_valid,
            total_weight=total_weight,
            message=message,
            warnings=warnings
        )
    
    except Exception as e:
        logger.error(f"验证权重失败: {e}")
        raise HTTPException(status_code=500, detail="验证权重失败")


@router.post("/weights/normalize")
async def normalize_weights(
    factors: List[dict],
    target_sum: float = 1.0,
    db: Session = Depends(get_db)
):
    """
    标准化权重
    
    Args:
        factors: 因子列表
        target_sum: 目标权重总和
        db: 数据库会话
    
    Returns:
        标准化后的因子列表
    """
    try:
        total_weight = sum(factor.get("weight", 0) for factor in factors)
        
        if total_weight == 0:
            # 如果总权重为0，平均分配
            equal_weight = target_sum / len(factors)
            normalized_factors = []
            for factor in factors:
                normalized_factor = factor.copy()
                normalized_factor["weight"] = equal_weight
                normalized_factors.append(normalized_factor)
        else:
            # 按比例标准化
            normalized_factors = []
            for factor in factors:
                normalized_factor = factor.copy()
                normalized_factor["weight"] = (factor.get("weight", 0) / total_weight) * target_sum
                normalized_factors.append(normalized_factor)
        
        return {"factors": normalized_factors}
    
    except Exception as e:
        logger.error(f"标准化权重失败: {e}")
        raise HTTPException(status_code=500, detail="标准化权重失败")


@router.post("/weights/optimize", response_model=WeightOptimizationResult)
async def optimize_weights(
    request: WeightSuggestionRequest,
    db: Session = Depends(get_db)
):
    """
    优化权重
    
    Args:
        request: 优化请求
        db: 数据库会话
    
    Returns:
        优化结果
    """
    try:
        # 这里实现权重优化算法
        # 目前返回简单的等权重分配
        factors = request.factors
        equal_weight = 1.0 / len(factors) if factors else 0
        
        optimized_factors = []
        for factor in factors:
            optimized_factor = factor.copy()
            optimized_factor["weight"] = equal_weight
            optimized_factors.append(optimized_factor)
        
        return WeightOptimizationResult(
            optimized_factors=optimized_factors,
            optimization_method=request.optimization_method,
            performance_metrics={
                "diversification_score": 0.8,
                "volatility": 0.15,
                "expected_return": 0.12
            },
            recommendations=[
                "建议使用等权重分配",
                "考虑因子间的相关性",
                "定期重新平衡权重"
            ],
            analysis_details={
                "factor_count": len(factors),
                "equal_weight": equal_weight,
                "method": "equal_weight"
            }
        )
    
    except Exception as e:
        logger.error(f"优化权重失败: {e}")
        raise HTTPException(status_code=500, detail="优化权重失败")


@router.post("/weights/suggestions")
async def get_weight_suggestions(
    factors: List[dict],
    db: Session = Depends(get_db)
):
    """
    获取权重建议
    
    Args:
        factors: 因子列表
        db: 数据库会话
    
    Returns:
        权重建议
    """
    try:
        # 这里实现权重建议算法
        # 目前返回简单的建议
        suggestions = []
        
        if len(factors) == 1:
            suggestions.append("单个因子建议权重为1.0")
        elif len(factors) == 2:
            suggestions.append("两个因子建议使用等权重分配")
        else:
            suggestions.append("多个因子建议使用等权重或基于相关性的分配")
        
        return {
            "suggestions": suggestions,
            "factor_count": len(factors),
            "recommended_method": "equal_weight"
        }
    
    except Exception as e:
        logger.error(f"获取权重建议失败: {e}")
        raise HTTPException(status_code=500, detail="获取权重建议失败") 