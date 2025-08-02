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
                id=factor.get('id', 0),
                name=factor.get('name', ''),
                description=factor.get('description', ''),
                category=factor.get('category', ''),
                code=factor.get('formula', ''),
                isActive=factor.get('is_active', True),
                version=factor.get('version', '1.0'),
                usageCount=factor.get('usage_count', 0),
                lastUsedAt=factor.get('last_used_at'),
                createdAt=factor.get('created_at'),
                updatedAt=factor.get('updated_at')
            ))
        
        return result
    
    except Exception as e:
        logger.error(f"获取因子列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取因子列表失败")


@router.get("/{factor_id}", response_model=FactorResponse)
async def get_factor(
    factor_id: str,
    db: Session = Depends(get_db)
):
    """
    获取单个因子详情
    
    Args:
        factor_id: 因子ID
        db: 数据库会话
    
    Returns:
        因子详情
    """
    try:
        factor_info = unified_factor_service.get_factor_by_id(factor_id, db)
        if not factor_info:
            raise HTTPException(status_code=404, detail="因子不存在")
        
        return FactorResponse(
            id=factor_info.get('id', 0),
            name=factor_info.get('name', ''),
            description=factor_info.get('description', ''),
            category=factor_info.get('category', ''),
            code=factor_info.get('formula', ''),
            isActive=factor_info.get('is_active', True),
            version=factor_info.get('version', '1.0'),
            usageCount=factor_info.get('usage_count', 0),
            lastUsedAt=factor_info.get('last_used_at'),
            createdAt=factor_info.get('created_at'),
            updatedAt=factor_info.get('updated_at')
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
    
    Args:
        factor_data: 因子创建数据
        db: 数据库会话
    
    Returns:
        创建的因子
    """
    try:
        # 转换为统一因子服务格式
        factor_info = {
            'factor_id': factor_data.name.lower().replace(' ', '_'),
            'name': factor_data.name,
            'display_name': factor_data.name,
            'description': factor_data.description or '',
            'category': factor_data.category or 'custom',
            'formula': factor_data.code,
            'input_fields': ['close', 'high', 'low', 'volume'],
            'default_parameters': {},
            'parameter_schema': {},
            'calculation_method': 'custom',
            'is_active': True,
            'is_builtin': False,
            'version': '1.0.0'
        }
        
        created_factor = unified_factor_service.create_factor(factor_info, db)
        if not created_factor:
            raise HTTPException(status_code=400, detail="创建因子失败")
        
        return FactorResponse(
            id=created_factor.get('id', 0),
            name=created_factor.get('name', ''),
            description=created_factor.get('description', ''),
            category=created_factor.get('category', ''),
            code=created_factor.get('formula', ''),
            isActive=created_factor.get('is_active', True),
            version=created_factor.get('version', '1.0'),
            usageCount=created_factor.get('usage_count', 0),
            lastUsedAt=created_factor.get('last_used_at'),
            createdAt=created_factor.get('created_at'),
            updatedAt=created_factor.get('updated_at')
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建因子失败: {e}")
        raise HTTPException(status_code=500, detail="创建因子失败")


@router.put("/{factor_id}", response_model=FactorResponse)
async def update_factor(
    factor_id: str,
    factor_data: FactorUpdate,
    db: Session = Depends(get_db)
):
    """
    更新因子
    
    Args:
        factor_id: 因子ID
        factor_data: 因子更新数据
        db: 数据库会话
    
    Returns:
        更新后的因子
    """
    try:
        # 构建更新数据
        update_data = {}
        if factor_data.name is not None:
            update_data['name'] = factor_data.name
            update_data['display_name'] = factor_data.name
        
        if factor_data.description is not None:
            update_data['description'] = factor_data.description
        
        if factor_data.category is not None:
            update_data['category'] = factor_data.category
        
        if factor_data.code is not None:
            update_data['formula'] = factor_data.code
        
        # 更新因子
        updated_factor = unified_factor_service.update_factor(factor_id, update_data, db)
        if not updated_factor:
            raise HTTPException(status_code=404, detail="因子不存在")
        
        return FactorResponse(
            id=updated_factor.get('id', 0),
            name=updated_factor.get('name', ''),
            description=updated_factor.get('description', ''),
            category=updated_factor.get('category', ''),
            code=updated_factor.get('formula', ''),
            isActive=updated_factor.get('is_active', True),
            version=updated_factor.get('version', '1.0'),
            usageCount=updated_factor.get('usage_count', 0),
            lastUsedAt=updated_factor.get('last_used_at'),
            createdAt=updated_factor.get('created_at'),
            updatedAt=updated_factor.get('updated_at')
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新因子失败: {e}")
        raise HTTPException(status_code=500, detail="更新因子失败")


@router.delete("/{factor_id}")
async def delete_factor(
    factor_id: str,
    db: Session = Depends(get_db)
):
    """
    删除因子
    
    Args:
        factor_id: 因子ID
        db: 数据库会话
    
    Returns:
        删除结果
    """
    try:
        success = unified_factor_service.delete_factor(factor_id, db)
        if not success:
            raise HTTPException(status_code=404, detail="因子不存在")
        
        return {"message": "因子删除成功"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除因子失败: {e}")
        raise HTTPException(status_code=500, detail="删除因子失败")


@router.post("/{factor_id}/test", response_model=FactorTestResponse)
async def test_factor(
    factor_id: str,
    test_request: FactorTestRequest,
    db: Session = Depends(get_db)
):
    """
    测试因子
    
    Args:
        factor_id: 因子ID
        test_request: 测试请求
        db: 数据库会话
    
    Returns:
        测试结果
    """
    try:
        # 这里可以添加因子测试逻辑
        # 目前返回模拟结果
        return FactorTestResponse(
            success=True,
            message="因子测试成功",
            executionTime=0.1,
            results=[],
            statistics={}
        )
    
    except Exception as e:
        logger.error(f"测试因子失败: {e}")
        raise HTTPException(status_code=500, detail="测试因子失败")


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