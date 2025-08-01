"""
因子管理API接口
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
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
from app.services.factor_service import factor_service

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
        query = db.query(Factor)
        
        if category:
            query = query.filter(Factor.category == category)
        
        if is_active is not None:
            query = query.filter(Factor.is_active == is_active)
        
        factors = query.offset(skip).limit(limit).all()
        
        result = []
        for factor in factors:
            result.append(FactorResponse(
                id=factor.id,
                name=factor.name,
                description=factor.description or "",
                category=factor.category or "",
                code=factor.code,
                isActive=factor.is_active or False,
                version=factor.version or "1.0",
                usageCount=factor.usage_count or 0,
                lastUsedAt=factor.last_used_at.isoformat() if factor.last_used_at else None,
                createdAt=factor.created_at.isoformat() if factor.created_at else "",
                updatedAt=factor.updated_at.isoformat() if factor.updated_at else ""
            ))
        
        return result
    
    except Exception as e:
        logger.error(f"获取因子列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取因子列表失败")


@router.get("/{factor_id}", response_model=FactorResponse)
async def get_factor(
    factor_id: int,
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
        factor = db.query(Factor).filter(Factor.id == factor_id).first()
        if not factor:
            raise HTTPException(status_code=404, detail="因子不存在")
        
        return FactorResponse(
            id=factor.id,
            name=factor.name,
            description=factor.description or "",
            category=factor.category or "",
            code=factor.code,
            isActive=factor.is_active or False,
            version=factor.version or "1.0",
            usageCount=factor.usage_count or 0,
            lastUsedAt=factor.last_used_at.isoformat() if factor.last_used_at else None,
            createdAt=factor.created_at.isoformat() if factor.created_at else "",
            updatedAt=factor.updated_at.isoformat() if factor.updated_at else ""
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
        创建的因子信息
    """
    try:
        # 检查因子名称是否已存在
        existing = db.query(Factor).filter(Factor.name == factor_data.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="因子名称已存在")
        
        # 验证因子代码语法
        try:
            validation_result = await factor_service.validate_factor_code(factor_data.code)
            if not validation_result.is_valid:
                raise HTTPException(
                    status_code=400, 
                    detail=f"因子代码语法错误: {validation_result.error_message}"
                )
        except Exception as e:
            logger.warning(f"因子代码验证失败: {e}")
            # 如果验证服务不可用，继续创建但记录警告
        
        # 创建因子
        new_factor = Factor(
            name=factor_data.name,
            description=factor_data.description,
            category=factor_data.category,
            code=factor_data.code,
            is_active=factor_data.isActive,
            version=factor_data.version or "1.0",
            usage_count=0
        )
        
        db.add(new_factor)
        db.commit()
        db.refresh(new_factor)
        
        logger.info(f"创建因子成功: {new_factor.name}")
        
        return FactorResponse(
            id=new_factor.id,
            name=new_factor.name,
            description=new_factor.description or "",
            category=new_factor.category or "",
            code=new_factor.code,
            isActive=new_factor.is_active or False,
            version=new_factor.version or "1.0",
            usageCount=new_factor.usage_count or 0,
            lastUsedAt=None,
            createdAt=new_factor.created_at.isoformat(),
            updatedAt=new_factor.updated_at.isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建因子失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="创建因子失败")


@router.put("/{factor_id}", response_model=FactorResponse)
async def update_factor(
    factor_id: int,
    factor_data: FactorUpdate,
    db: Session = Depends(get_db)
):
    """
    更新因子
    
    Args:
        factor_id: 因子ID
        factor_data: 更新数据
        db: 数据库会话
    
    Returns:
        更新后的因子信息
    """
    try:
        factor = db.query(Factor).filter(Factor.id == factor_id).first()
        if not factor:
            raise HTTPException(status_code=404, detail="因子不存在")
        
        # 检查名称是否与其他因子冲突
        if factor_data.name and factor_data.name != factor.name:
            existing = db.query(Factor).filter(
                Factor.name == factor_data.name,
                Factor.id != factor_id
            ).first()
            if existing:
                raise HTTPException(status_code=400, detail="因子名称已存在")
        
        # 如果代码有更新，验证语法
        if factor_data.code and factor_data.code != factor.code:
            try:
                validation_result = await factor_service.validate_factor_code(factor_data.code)
                if not validation_result.is_valid:
                    raise HTTPException(
                        status_code=400,
                        detail=f"因子代码语法错误: {validation_result.error_message}"
                    )
            except Exception as e:
                logger.warning(f"因子代码验证失败: {e}")
        
        # 更新字段
        if factor_data.name is not None:
            factor.name = factor_data.name
        if factor_data.description is not None:
            factor.description = factor_data.description
        if factor_data.category is not None:
            factor.category = factor_data.category
        if factor_data.code is not None:
            factor.code = factor_data.code
            # 代码更新时增加版本号
            version_parts = factor.version.split('.')
            if len(version_parts) >= 2:
                factor.version = f"{version_parts[0]}.{int(version_parts[1]) + 1}"
        if factor_data.isActive is not None:
            factor.is_active = factor_data.isActive
        
        db.commit()
        db.refresh(factor)
        
        logger.info(f"更新因子成功: {factor.name}")
        
        return FactorResponse(
            id=factor.id,
            name=factor.name,
            description=factor.description or "",
            category=factor.category or "",
            code=factor.code,
            isActive=factor.is_active or False,
            version=factor.version or "1.0",
            usageCount=factor.usage_count or 0,
            lastUsedAt=factor.last_used_at.isoformat() if factor.last_used_at else None,
            createdAt=factor.created_at.isoformat() if factor.created_at else "",
            updatedAt=factor.updated_at.isoformat() if factor.updated_at else ""
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新因子失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="更新因子失败")


@router.delete("/{factor_id}")
async def delete_factor(
    factor_id: int,
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
        factor = db.query(Factor).filter(Factor.id == factor_id).first()
        if not factor:
            raise HTTPException(status_code=404, detail="因子不存在")
        
        # 检查是否有策略在使用这个因子
        # TODO: 实现策略依赖检查
        
        factor_name = factor.name
        db.delete(factor)
        db.commit()
        
        logger.info(f"删除因子成功: {factor_name}")
        
        return {"message": "因子删除成功", "name": factor_name}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除因子失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="删除因子失败")


@router.post("/{factor_id}/test", response_model=FactorTestResponse)
async def test_factor(
    factor_id: int,
    test_request: FactorTestRequest,
    db: Session = Depends(get_db)
):
    """
    测试因子代码
    
    Args:
        factor_id: 因子ID
        test_request: 测试请求参数
        db: 数据库会话
    
    Returns:
        测试结果
    """
    try:
        factor = db.query(Factor).filter(Factor.id == factor_id).first()
        if not factor:
            raise HTTPException(status_code=404, detail="因子不存在")
        
        # 执行因子测试
        test_result = await factor_service.test_factor(
            factor_code=factor.code,
            test_symbols=test_request.symbols,
            start_date=test_request.startDate,
            end_date=test_request.endDate
        )
        
        # 更新因子使用统计
        factor.usage_count = (factor.usage_count or 0) + 1
        factor.last_used_at = datetime.now()
        db.commit()
        
        return test_result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"测试因子失败: {e}")
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
        # 从数据库获取所有不同的分类
        categories = db.query(Factor.category).distinct().filter(
            Factor.category.isnot(None)
        ).all()
        
        result = [cat[0] for cat in categories if cat[0]]
        
        # 如果没有分类，返回默认分类
        if not result:
            result = ["估值", "技术", "基本面", "情绪", "其他"]
        
        return sorted(result)
    
    except Exception as e:
        logger.error(f"获取因子分类失败: {e}")
        raise HTTPException(status_code=500, detail="获取因子分类失败")