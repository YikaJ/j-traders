"""
因子管理API接口 - 使用统一因子服务
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from app.db.database import get_db
from app.db.models.factor import Factor
from app.schemas.factors import (
    FactorResponse,
    FactorCreate,
    FactorUpdate,
    FactorTestRequest,
    FactorTestResponse
)
from app.services.unified_factor_service import unified_factor_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[FactorResponse])
async def get_factors(
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    获取因子列表
    
    Args:
        category: 因子分类过滤
        is_active: 是否启用过滤
        skip: 跳过记录数
        limit: 返回记录数限制
        db: 数据库会话
    
    Returns:
        因子列表
    """
    try:
        # 使用统一因子服务获取因子列表
        all_factors = unified_factor_service.get_all_factors(db)
        
        # 应用过滤
        filtered_factors = []
        for factor in all_factors:
            if category and factor.get('category') != category:
                continue
            if is_active is not None and factor.get('is_active', True) != is_active:
                continue
            filtered_factors.append(factor)
        
        # 应用分页
        start = skip
        end = start + limit
        paginated_factors = filtered_factors[start:end]
        
        result = []
        for factor in paginated_factors:
            result.append(FactorResponse(
                id=factor.get('id', ''),
                name=factor.get('name', ''),
                display_name=factor.get('display_name', ''),
                description=factor.get('description', ''),
                category=factor.get('category', ''),
                code=factor.get('code', ''),
                input_fields=factor.get('input_fields', []),
                default_parameters=factor.get('default_parameters', {}),
                parameter_schema=factor.get('parameter_schema'),
                calculation_method=factor.get('calculation_method', 'custom'),
                is_active=factor.get('is_active', True),
                is_builtin=factor.get('is_builtin', False),
                usage_count=factor.get('usage_count', 0),
                last_used_at=factor.get('last_used_at'),
                created_at=factor.get('created_at'),
                updated_at=factor.get('updated_at'),
                version=factor.get('version', '1.0.0')
            ))
        
        return result
    
    except Exception as e:
        logger.error(f"获取因子列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取因子列表失败")


@router.get("/{id}", response_model=FactorResponse)
async def get_factor(
    id: str,
    db: Session = Depends(get_db)
):
    """
    根据ID获取因子详情
    """
    try:
        factor_info = unified_factor_service.get_factor_by_id(id, db)
        if not factor_info:
            raise HTTPException(status_code=404, detail="因子不存在")
        
        return FactorResponse(
            id=factor_info.get('id', ''),
            name=factor_info.get('name', ''),
            display_name=factor_info.get('display_name', ''),
            description=factor_info.get('description', ''),
            category=factor_info.get('category', ''),
            code=factor_info.get('code', ''),
            input_fields=factor_info.get('input_fields', []),
            default_parameters=factor_info.get('default_parameters', {}),
            parameter_schema=factor_info.get('parameter_schema'),
            calculation_method=factor_info.get('calculation_method', 'custom'),
            is_active=factor_info.get('is_active', True),
            is_builtin=factor_info.get('is_builtin', False),
            usage_count=factor_info.get('usage_count', 0),
            last_used_at=factor_info.get('last_used_at'),
            created_at=factor_info.get('created_at'),
            updated_at=factor_info.get('updated_at'),
            version=factor_info.get('version', '1.0.0')
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取因子详情失败: {e}")
        raise HTTPException(status_code=500, detail="获取因子详情失败")


@router.post("/", response_model=FactorResponse)
async def create_factor(
    factor_data: FactorCreate,
    db: Session = Depends(get_db)
):
    """
    创建新因子
    """
    try:
        # 处理前端发送的数据格式
        factor_data_dict = factor_data.dict()
        
        # 如果前端发送的是formula，需要映射到code字段
        if 'formula' in factor_data_dict and 'code' not in factor_data_dict:
            factor_data_dict['code'] = factor_data_dict['formula']
        
        # 移除因子ID相关字段，让后端自动生成
        factor_data_dict.pop('id', None)
        factor_data_dict.pop('factor_id', None)
        
        created_factor = unified_factor_service.create_factor(factor_data_dict, db)
        return created_factor
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建因子失败: {str(e)}")


@router.put("/{id}", response_model=FactorResponse)
async def update_factor(
    id: str,
    factor_data: FactorUpdate,
    db: Session = Depends(get_db)
):
    """
    更新因子信息
    """
    try:
        update_data = factor_data.dict(exclude_unset=True)
        if 'code' in update_data:
            update_data['code'] = factor_data.code
        
        updated_factor = unified_factor_service.update_factor(id, update_data, db)
        return updated_factor
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新因子失败: {str(e)}")


@router.delete("/{id}")
async def delete_factor(
    id: str,
    db: Session = Depends(get_db)
):
    """
    删除因子
    """
    try:
        success = unified_factor_service.delete_factor(id, db)
        if success:
            return {"message": "因子删除成功"}
        else:
            raise HTTPException(status_code=404, detail="因子不存在")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除因子失败: {str(e)}")


@router.post("/{id}/test", response_model=FactorTestResponse)
async def test_factor(
    id: str,
    test_request: FactorTestRequest,
    db: Session = Depends(get_db)
):
    """
    测试因子代码
    """
    try:
        result = unified_factor_service.test_factor(id, test_request.dict(), db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试因子失败: {str(e)}")


@router.get("/categories/", response_model=List[str])
async def get_factor_categories(db: Session = Depends(get_db)):
    """
    获取因子分类列表
    
    Args:
        db: 数据库会话
    
    Returns:
        因子分类列表
    """
    try:
        # 使用统一因子服务获取分类
        all_factors = unified_factor_service.get_all_factors(db)
        categories = list(set(factor.get('category', 'unknown') for factor in all_factors))
        return categories
    
    except Exception as e:
        logger.error(f"获取因子分类失败: {e}")
        raise HTTPException(status_code=500, detail="获取因子分类失败")