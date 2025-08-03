"""
策略配置管理API端点
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.database import get_db
from app.db.models.strategy import Strategy
from app.schemas.strategy import StrategyCreate, StrategyUpdate, StrategyResponse, StrategyListResponse

router = APIRouter()


@router.get("/", response_model=StrategyListResponse)
async def get_strategy_configs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    created_by: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: Session = Depends(get_db)
):
    """获取策略配置列表"""
    try:
        # 构建查询
        query = db.query(Strategy)
        
        # 过滤条件
        if created_by:
            query = query.filter(Strategy.created_by == created_by)
        
        if search:
            query = query.filter(
                Strategy.name.contains(search) | 
                Strategy.description.contains(search)
            )
        
        # 排序
        if sort_order == "desc":
            query = query.order_by(getattr(Strategy, sort_by).desc())
        else:
            query = query.order_by(getattr(Strategy, sort_by).asc())
        
        # 分页
        total = query.count()
        strategies = query.offset((page - 1) * size).limit(size).all()
        
        return StrategyListResponse(
            strategies=[StrategyResponse.from_orm(s) for s in strategies],
            total=total,
            skip=(page - 1) * size,
            limit=size
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取策略配置失败: {str(e)}")


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy_config(
    strategy_id: str,
    db: Session = Depends(get_db)
):
    """获取指定策略配置"""
    try:
        strategy = db.query(Strategy).filter(Strategy.strategy_id == strategy_id).first()
        if not strategy:
            raise HTTPException(status_code=404, detail="策略配置不存在")
        
        return StrategyResponse.from_orm(strategy)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取策略配置失败: {str(e)}")


@router.post("/", response_model=StrategyResponse)
async def create_strategy_config(
    strategy_data: StrategyCreate,
    created_by: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """创建策略配置"""
    try:
        # 检查策略ID是否已存在
        existing = db.query(Strategy).filter(Strategy.strategy_id == strategy_data.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="策略名称已存在")
        
        # 创建新策略
        strategy = Strategy(
            strategy_id=strategy_data.name,  # 使用name作为strategy_id
            name=strategy_data.name,
            description=strategy_data.description or "",
            factors=strategy_data.factors,
            filters=strategy_data.filters,
            config=strategy_data.config,
            is_active=True,
            created_by=created_by,
            execution_count=0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.add(strategy)
        db.commit()
        db.refresh(strategy)
        
        return StrategyResponse.from_orm(strategy)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建策略配置失败: {str(e)}")


@router.put("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy_config(
    strategy_id: str,
    strategy_data: StrategyUpdate,
    db: Session = Depends(get_db)
):
    """更新策略配置"""
    try:
        strategy = db.query(Strategy).filter(Strategy.strategy_id == strategy_id).first()
        if not strategy:
            raise HTTPException(status_code=404, detail="策略配置不存在")
        
        # 更新字段
        if strategy_data.name is not None:
            strategy.name = strategy_data.name
        if strategy_data.description is not None:
            strategy.description = strategy_data.description
        if strategy_data.factors is not None:
            strategy.factors = strategy_data.factors
        if strategy_data.filters is not None:
            strategy.filters = strategy_data.filters
        if strategy_data.config is not None:
            strategy.config = strategy_data.config
        if strategy_data.is_active is not None:
            strategy.is_active = strategy_data.is_active
        
        strategy.updated_at = datetime.now()
        
        db.commit()
        db.refresh(strategy)
        
        return StrategyResponse.from_orm(strategy)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新策略配置失败: {str(e)}")


@router.delete("/{strategy_id}")
async def delete_strategy_config(
    strategy_id: str,
    db: Session = Depends(get_db)
):
    """删除策略配置"""
    try:
        strategy = db.query(Strategy).filter(Strategy.strategy_id == strategy_id).first()
        if not strategy:
            raise HTTPException(status_code=404, detail="策略配置不存在")
        
        db.delete(strategy)
        db.commit()
        
        return {"message": "策略配置删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除策略配置失败: {str(e)}")


@router.post("/{strategy_id}/duplicate", response_model=StrategyResponse)
async def duplicate_strategy_config(
    strategy_id: str,
    new_name: Optional[str] = None,
    created_by: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """复制策略配置"""
    try:
        original = db.query(Strategy).filter(Strategy.strategy_id == strategy_id).first()
        if not original:
            raise HTTPException(status_code=404, detail="原策略配置不存在")
        
        # 生成新名称
        if not new_name:
            new_name = f"{original.name}_副本"
        
        # 检查新名称是否已存在
        existing = db.query(Strategy).filter(Strategy.strategy_id == new_name).first()
        if existing:
            raise HTTPException(status_code=400, detail="新策略名称已存在")
        
        # 创建副本
        duplicate = Strategy(
            strategy_id=new_name,
            name=new_name,
            description=original.description,
            factors=original.factors,
            filters=original.filters,
            config=original.config,
            is_active=True,
            created_by=created_by,
            execution_count=0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.add(duplicate)
        db.commit()
        db.refresh(duplicate)
        
        return StrategyResponse.from_orm(duplicate)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"复制策略配置失败: {str(e)}")


@router.get("/{strategy_id}/export")
async def export_strategy_config(
    strategy_id: str,
    db: Session = Depends(get_db)
):
    """导出策略配置"""
    try:
        strategy = db.query(Strategy).filter(Strategy.strategy_id == strategy_id).first()
        if not strategy:
            raise HTTPException(status_code=404, detail="策略配置不存在")
        
        # 构建导出数据
        export_data = {
            "strategy_id": strategy.strategy_id,
            "name": strategy.name,
            "description": strategy.description,
            "factors": strategy.factors,
            "filters": strategy.filters,
            "config": strategy.config,
            "created_by": strategy.created_by,
            "created_at": strategy.created_at.isoformat() if strategy.created_at else None,
            "exported_at": datetime.now().isoformat()
        }
        
        return export_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出策略配置失败: {str(e)}")


@router.post("/import")
async def import_strategy_config(
    import_data: dict,
    created_by: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """导入策略配置"""
    try:
        # 检查策略ID是否已存在
        strategy_id = import_data.get("strategy_id") or import_data.get("name")
        if not strategy_id:
            raise HTTPException(status_code=400, detail="策略ID不能为空")
        
        existing = db.query(Strategy).filter(Strategy.strategy_id == strategy_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="策略ID已存在")
        
        # 创建新策略
        strategy = Strategy(
            strategy_id=strategy_id,
            name=import_data.get("name", strategy_id),
            description=import_data.get("description", ""),
            factors=import_data.get("factors", []),
            filters=import_data.get("filters", {}),
            config=import_data.get("config", {}),
            is_active=True,
            created_by=created_by,
            execution_count=0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.add(strategy)
        db.commit()
        db.refresh(strategy)
        
        return StrategyResponse.from_orm(strategy)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"导入策略配置失败: {str(e)}")


@router.post("/{strategy_id}/usage")
async def record_strategy_usage(
    strategy_id: str,
    db: Session = Depends(get_db)
):
    """记录策略使用"""
    try:
        strategy = db.query(Strategy).filter(Strategy.strategy_id == strategy_id).first()
        if not strategy:
            raise HTTPException(status_code=404, detail="策略配置不存在")
        
        strategy.execution_count += 1
        strategy.last_executed_at = datetime.now()
        strategy.updated_at = datetime.now()
        
        db.commit()
        
        return {"message": "使用记录已更新"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"记录策略使用失败: {str(e)}")


@router.get("/popular")
async def get_popular_strategies(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """获取热门策略"""
    try:
        strategies = db.query(Strategy)\
            .filter(Strategy.is_active == True)\
            .order_by(Strategy.execution_count.desc())\
            .limit(limit)\
            .all()
        
        return [StrategyResponse.from_orm(s) for s in strategies]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取热门策略失败: {str(e)}")


@router.get("/statistics")
async def get_strategy_statistics(
    created_by: Optional[str] = None,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """获取策略统计"""
    try:
        query = db.query(Strategy)
        
        if created_by:
            query = query.filter(Strategy.created_by == created_by)
        
        total_strategies = query.count()
        active_strategies = query.filter(Strategy.is_active == True).count()
        total_executions = query.with_entities(db.func.sum(Strategy.execution_count)).scalar() or 0
        
        return {
            "total_strategies": total_strategies,
            "active_strategies": active_strategies,
            "total_executions": total_executions,
            "avg_executions": total_executions / total_strategies if total_strategies > 0 else 0,
            "days": days
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取策略统计失败: {str(e)}") 