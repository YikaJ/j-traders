"""
数据字段配置API端点
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
import logging

from app.schemas.data_fields import (
    FactorInputFieldsRequest, FactorInputFieldsResponse,
    DataFieldCategory, DataField
)
from app.services.data_field_service import data_field_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/fields", response_model=FactorInputFieldsResponse)
async def get_factor_input_fields(
    categories: Optional[List[DataFieldCategory]] = Query(None, description="数据字段分类筛选"),
    include_common_only: bool = Query(True, description="是否只包含常用字段")
):
    """
    获取因子输入字段配置
    
    - **categories**: 要获取的字段分类，不传则获取所有分类
    - **include_common_only**: 是否只返回常用字段，默认为true
    """
    try:
        request = FactorInputFieldsRequest(
            categories=categories,
            include_common_only=include_common_only
        )
        
        response = data_field_service.get_available_fields(request)
        return response
        
    except Exception as e:
        logger.error(f"获取数据字段配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fields/common", response_model=List[DataField])
async def get_common_fields():
    """
    获取常用数据字段列表
    """
    try:
        common_fields = data_field_service.get_common_fields()
        return common_fields
        
    except Exception as e:
        logger.error(f"获取常用字段失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fields/{field_id}", response_model=DataField)
async def get_field_by_id(field_id: str):
    """
    根据字段ID获取字段详细信息
    """
    try:
        field = data_field_service.get_field_by_id(field_id)
        if not field:
            raise HTTPException(status_code=404, detail=f"字段 {field_id} 未找到")
        
        return field
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取字段信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fields/validate")
async def validate_field_combination(field_ids: List[str]):
    """
    验证字段组合的有效性
    """
    try:
        validation_result = data_field_service.validate_field_combination(field_ids)
        return validation_result
        
    except Exception as e:
        logger.error(f"验证字段组合失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))