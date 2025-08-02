"""
策略管理API端点
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.db.database import get_db
from app.schemas.strategy import (
    StrategyCreate, StrategyUpdate, StrategyResponse,
    StrategyListRequest, StrategyListResponse,
    StrategyExecutionRequest, StrategyExecutionResult, StrategyExecutionDetail
)
from app.services.strategy_management_service import strategy_management_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=StrategyResponse)
async def create_strategy(
    strategy_data: StrategyCreate,
    db: Session = Depends(get_db),
    created_by: Optional[str] = Query(None, description="创建者")
):
    """
    创建新策略
    
    - **name**: 策略名称（必填）
    - **description**: 策略描述
    - **factors**: 因子配置列表（必填）
    - **filters**: 筛选条件
    - **config**: 策略配置
    """
    try:
        return await strategy_management_service.create_strategy(db, strategy_data, created_by)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建策略失败: {e}")
        raise HTTPException(status_code=500, detail="创建策略失败")


@router.get("/", response_model=StrategyListResponse)
async def get_strategies(
    is_active: Optional[bool] = Query(None, description="是否启用"),
    created_by: Optional[str] = Query(None, description="创建者筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回记录数"),
    db: Session = Depends(get_db)
):
    """
    获取策略列表
    
    支持按活跃状态、创建者、关键词筛选，以及分页
    """
    try:
        request = StrategyListRequest(
            is_active=is_active,
            created_by=created_by,
            keyword=keyword,
            skip=skip,
            limit=limit
        )
        return await strategy_management_service.get_strategies(db, request)
    except Exception as e:
        logger.error(f"获取策略列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取策略列表失败")


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(
    strategy_id: str,
    db: Session = Depends(get_db)
):
    """
    获取单个策略详情
    """
    try:
        strategy = await strategy_management_service.get_strategy(db, strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail=f"策略不存在: {strategy_id}")
        return strategy
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取策略失败: {e}")
        raise HTTPException(status_code=500, detail="获取策略失败")


@router.put("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_id: str,
    strategy_data: StrategyUpdate,
    db: Session = Depends(get_db)
):
    """
    更新策略
    
    可以部分更新策略的任意字段
    """
    try:
        strategy = await strategy_management_service.update_strategy(db, strategy_id, strategy_data)
        if not strategy:
            raise HTTPException(status_code=404, detail=f"策略不存在: {strategy_id}")
        return strategy
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新策略失败: {e}")
        raise HTTPException(status_code=500, detail="更新策略失败")


@router.delete("/{strategy_id}")
async def delete_strategy(
    strategy_id: str,
    db: Session = Depends(get_db)
):
    """
    删除策略
    
    删除策略及其所有执行记录
    """
    try:
        success = await strategy_management_service.delete_strategy(db, strategy_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"策略不存在: {strategy_id}")
        return {"message": "策略删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除策略失败: {e}")
        raise HTTPException(status_code=500, detail="删除策略失败")


@router.post("/{strategy_id}/execute", response_model=StrategyExecutionResult)
async def execute_strategy(
    strategy_id: str,
    request: StrategyExecutionRequest,
    db: Session = Depends(get_db)
):
    """
    执行策略选股
    
    - **execution_date**: 执行日期，默认为今天
    - **dry_run**: 是否为模拟执行，不保存结果
    - **save_result**: 是否保存执行结果
    """
    try:
        return await strategy_management_service.execute_strategy(db, strategy_id, request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"执行策略失败: {e}")
        raise HTTPException(status_code=500, detail="执行策略失败")


@router.get("/{strategy_id}/executions", response_model=List[StrategyExecutionResult])
async def get_execution_history(
    strategy_id: str,
    limit: int = Query(20, ge=1, le=100, description="返回记录数"),
    db: Session = Depends(get_db)
):
    """
    获取策略执行历史
    
    返回最近的执行记录，按时间倒序
    """
    try:
        return await strategy_management_service.get_execution_history(db, strategy_id, limit)
    except Exception as e:
        logger.error(f"获取执行历史失败: {e}")
        raise HTTPException(status_code=500, detail="获取执行历史失败")


@router.get("/executions/{execution_id}", response_model=StrategyExecutionDetail)
async def get_execution_detail(
    execution_id: str,
    db: Session = Depends(get_db)
):
    """
    获取执行详情
    
    包含选中的股票列表、因子表现等详细信息
    """
    try:
        execution = await strategy_management_service.get_execution_detail(db, execution_id)
        if not execution:
            raise HTTPException(status_code=404, detail=f"执行记录不存在: {execution_id}")
        return execution
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取执行详情失败: {e}")
        raise HTTPException(status_code=500, detail="获取执行详情失败")


@router.get("/{strategy_id}/available-factors")
async def get_available_factors(
    strategy_id: str,
    db: Session = Depends(get_db)
):
    """
    获取可用于策略的因子列表
    
    返回所有可用的因子及其基本信息
    """
    try:
        # 这里可以集成因子服务，获取所有可用的因子
        from app.services.factor_service import factor_service
        
        factors = await factor_service.get_all_factors(db)
        
        # 转换为简化格式，方便前端使用
        available_factors = []
        for factor in factors:
            available_factors.append({
                "factor_id": factor.factor_id,
                "factor_name": factor.name,
                "display_name": factor.display_name,
                "description": factor.description,
                "category": factor.category,
                "is_active": factor.is_active
            })
        
        return {"factors": available_factors}
        
    except Exception as e:
        logger.error(f"获取可用因子失败: {e}")
        raise HTTPException(status_code=500, detail="获取可用因子失败")


@router.post("/{strategy_id}/validate")
async def validate_strategy(
    strategy_id: str,
    db: Session = Depends(get_db)
):
    """
    验证策略配置
    
    检查策略的因子配置、权重设置等是否有效
    """
    try:
        strategy = await strategy_management_service.get_strategy(db, strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail=f"策略不存在: {strategy_id}")
        
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        # 验证因子权重
        total_weight = sum(factor.weight for factor in strategy.factors if factor.is_enabled)
        if abs(total_weight - 1.0) > 0.001:
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"启用因子的权重总和必须为1.0，当前为{total_weight}")
        
        # 验证因子存在性
        from app.db.models.factor import Factor
        factor_ids = [factor.factor_id for factor in strategy.factors]
        existing_factors = db.query(Factor).filter(Factor.factor_id.in_(factor_ids)).all()
        existing_ids = {factor.factor_id for factor in existing_factors}
        
        missing_ids = set(factor_ids) - existing_ids
        if missing_ids:
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"因子不存在: {', '.join(missing_ids)}")
        
        # 检查是否有启用的因子
        enabled_factors = [factor for factor in strategy.factors if factor.is_enabled]
        if not enabled_factors:
            validation_result["is_valid"] = False
            validation_result["errors"].append("至少需要启用一个因子")
        
        return validation_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"验证策略失败: {e}")
        raise HTTPException(status_code=500, detail="验证策略失败")