"""
因子管理API接口 - 使用统一因子服务
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from app.db.database import get_db
from app.db.models.factor import Factor, FactorTag, FactorTagRelation
from app.schemas.factors import (
    FactorResponse,
    FactorCreate,
    FactorUpdate,
    FactorTestRequest,
    FactorTestResponse,
    FactorTagCreate,
    FactorTagUpdate,
    FactorTagResponse,
    FactorTagRelationCreate,
    FactorTagRelationResponse
)
from app.services.unified_factor_service import unified_factor_service

logger = logging.getLogger(__name__)

router = APIRouter()


# 因子标签相关API端点
@router.get("/tags/", response_model=List[FactorTagResponse])
async def get_factor_tags(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    获取因子标签列表
    
    Args:
        is_active: 是否启用过滤
        db: 数据库会话
    
    Returns:
        因子标签列表
    """
    try:
        query = db.query(FactorTag)
        if is_active is not None:
            query = query.filter(FactorTag.is_active == is_active)
        
        tags = query.order_by(FactorTag.usage_count.desc(), FactorTag.created_at.desc()).all()
        return tags
    
    except Exception as e:
        logger.error(f"获取因子标签列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取因子标签列表失败")


@router.post("/tags/", response_model=FactorTagResponse)
async def create_factor_tag(
    tag_data: FactorTagCreate,
    db: Session = Depends(get_db)
):
    """
    创建因子标签
    """
    try:
        # 检查标签名称是否已存在
        existing_tag = db.query(FactorTag).filter(FactorTag.name == tag_data.name).first()
        if existing_tag:
            raise HTTPException(status_code=400, detail="标签名称已存在")
        
        tag = FactorTag(**tag_data.dict())
        db.add(tag)
        db.commit()
        db.refresh(tag)
        
        return tag
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"创建因子标签失败: {e}")
        raise HTTPException(status_code=500, detail="创建因子标签失败")


@router.put("/tags/{tag_id}", response_model=FactorTagResponse)
async def update_factor_tag(
    tag_id: int,
    tag_data: FactorTagUpdate,
    db: Session = Depends(get_db)
):
    """
    更新因子标签
    """
    try:
        tag = db.query(FactorTag).filter(FactorTag.id == tag_id).first()
        if not tag:
            raise HTTPException(status_code=404, detail="标签不存在")
        
        update_data = tag_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tag, field, value)
        
        db.commit()
        db.refresh(tag)
        
        return tag
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新因子标签失败: {e}")
        raise HTTPException(status_code=500, detail="更新因子标签失败")


@router.delete("/tags/{tag_id}")
async def delete_factor_tag(
    tag_id: int,
    db: Session = Depends(get_db)
):
    """
    删除因子标签
    """
    try:
        tag = db.query(FactorTag).filter(FactorTag.id == tag_id).first()
        if not tag:
            raise HTTPException(status_code=404, detail="标签不存在")
        
        # 检查是否有因子使用此标签
        relations = db.query(FactorTagRelation).filter(FactorTagRelation.tag_id == tag_id).count()
        if relations > 0:
            raise HTTPException(status_code=400, detail="标签正在被使用，无法删除")
        
        db.delete(tag)
        db.commit()
        
        return {"message": "标签删除成功"}
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除因子标签失败: {e}")
        raise HTTPException(status_code=500, detail="删除因子标签失败")


@router.post("/tags/relations/", response_model=FactorTagRelationResponse)
async def create_factor_tag_relations(
    relation_data: FactorTagRelationCreate,
    db: Session = Depends(get_db)
):
    """
    创建因子标签关联
    """
    try:
        # 删除现有的关联
        db.query(FactorTagRelation).filter(
            FactorTagRelation.factor_id == relation_data.factor_id
        ).delete()
        
        # 创建新的关联
        relations = []
        for tag_id in relation_data.tag_ids:
            relation = FactorTagRelation(
                factor_id=relation_data.factor_id,
                tag_id=tag_id
            )
            relations.append(relation)
        
        db.add_all(relations)
        db.commit()
        
        # 获取关联的标签信息
        tags = db.query(FactorTag).filter(
            FactorTag.id.in_(relation_data.tag_ids)
        ).all()
        
        return FactorTagRelationResponse(
            factor_id=relation_data.factor_id,
            tag_ids=relation_data.tag_ids,
            tags=tags
        )
    
    except Exception as e:
        db.rollback()
        logger.error(f"创建因子标签关联失败: {e}")
        raise HTTPException(status_code=500, detail="创建因子标签关联失败")


@router.get("/{factor_id}/tags/", response_model=List[FactorTagResponse])
async def get_factor_tags(
    factor_id: str,
    db: Session = Depends(get_db)
):
    """
    获取因子的标签列表
    """
    try:
        # 通过关联表查询标签
        tags = db.query(FactorTag).join(
            FactorTagRelation,
            FactorTag.id == FactorTagRelation.tag_id
        ).filter(
            FactorTagRelation.factor_id == factor_id
        ).all()
        
        return tags
    
    except Exception as e:
        logger.error(f"获取因子标签失败: {e}")
        raise HTTPException(status_code=500, detail="获取因子标签失败")


# 现有的因子API端点保持不变
@router.get("/", response_model=List[FactorResponse])
async def get_factors(
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    获取因子列表
    
    Args:
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
            if is_active is not None and factor.get('is_active', True) != is_active:
                continue
            filtered_factors.append(factor)
        
        # 应用分页
        start = skip
        end = start + limit
        paginated_factors = filtered_factors[start:end]
        
        result = []
        for factor in paginated_factors:
            # 获取因子的标签
            factor_tags = db.query(FactorTag).join(
                FactorTagRelation,
                FactorTag.id == FactorTagRelation.tag_id
            ).filter(
                FactorTagRelation.factor_id == factor.get('id', '')
            ).all()
            
            result.append(FactorResponse(
                id=factor.get('id', ''),
                name=factor.get('name', ''),
                display_name=factor.get('display_name', ''),
                description=factor.get('description', ''),
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
                version=factor.get('version', '1.0.0'),
                tags=factor_tags
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
        
        # 获取因子的标签
        factor_tags = db.query(FactorTag).join(
            FactorTagRelation,
            FactorTag.id == FactorTagRelation.tag_id
        ).filter(
            FactorTagRelation.factor_id == id
        ).all()
        
        return FactorResponse(
            id=factor_info.get('id', ''),
            name=factor_info.get('name', ''),
            display_name=factor_info.get('display_name', ''),
            description=factor_info.get('description', ''),
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
            version=factor_info.get('version', '1.0.0'),
            tags=factor_tags
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


