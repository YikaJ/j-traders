"""
策略管理和执行API接口
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from datetime import datetime

from app.db.database import get_db
from app.db.models.factor import Strategy, StrategyExecution, SelectionResult
from app.schemas.factors import (
    StrategyResponse,
    StrategyCreate,
    StrategyUpdate,
    StrategyExecutionRequest,
    StrategyExecutionResponse
)
from app.services.strategy_service import strategy_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[StrategyResponse])
async def get_strategies(
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    获取策略列表
    
    Args:
        is_active: 是否启用过滤
        skip: 跳过记录数
        limit: 返回记录数限制
        db: 数据库会话
    
    Returns:
        策略列表
    """
    try:
        query = db.query(Strategy)
        
        if is_active is not None:
            query = query.filter(Strategy.is_active == is_active)
        
        strategies = query.offset(skip).limit(limit).all()
        
        result = []
        for strategy in strategies:
            # 计算平均执行时间
            avg_execution_time = None
            if strategy.execution_count and strategy.execution_count > 0:
                executions = db.query(StrategyExecution).filter(
                    StrategyExecution.strategy_id == strategy.id,
                    StrategyExecution.execution_time.isnot(None)
                ).all()
                if executions:
                    avg_execution_time = sum(e.execution_time for e in executions) / len(executions)
            
            result.append(StrategyResponse(
                id=strategy.id,
                name=strategy.name,
                description=strategy.description or "",
                factorIds=strategy.factor_ids or [],
                factorWeights=strategy.factor_weights or {},
                maxResults=strategy.max_results or 50,
                minMarketCap=strategy.min_market_cap,
                maxMarketCap=strategy.max_market_cap,
                excludeSt=strategy.exclude_st or True,
                excludeNewStock=strategy.exclude_new_stock or True,
                minTurnover=strategy.min_turnover,
                isActive=strategy.is_active or False,
                executionCount=strategy.execution_count or 0,
                lastExecutedAt=strategy.last_executed_at.isoformat() if strategy.last_executed_at else None,
                avgExecutionTime=avg_execution_time,
                createdAt=strategy.created_at.isoformat() if strategy.created_at else "",
                updatedAt=strategy.updated_at.isoformat() if strategy.updated_at else ""
            ))
        
        return result
    
    except Exception as e:
        logger.error(f"获取策略列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取策略列表失败")


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(
    strategy_id: int,
    db: Session = Depends(get_db)
):
    """
    获取单个策略详情
    
    Args:
        strategy_id: 策略ID
        db: 数据库会话
    
    Returns:
        策略详情
    """
    try:
        strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not strategy:
            raise HTTPException(status_code=404, detail="策略不存在")
        
        # 计算平均执行时间
        avg_execution_time = None
        if strategy.execution_count and strategy.execution_count > 0:
            executions = db.query(StrategyExecution).filter(
                StrategyExecution.strategy_id == strategy.id,
                StrategyExecution.execution_time.isnot(None)
            ).all()
            if executions:
                avg_execution_time = sum(e.execution_time for e in executions) / len(executions)
        
        return StrategyResponse(
            id=strategy.id,
            name=strategy.name,
            description=strategy.description or "",
            factorIds=strategy.factor_ids or [],
            factorWeights=strategy.factor_weights or {},
            maxResults=strategy.max_results or 50,
            minMarketCap=strategy.min_market_cap,
            maxMarketCap=strategy.max_market_cap,
            excludeSt=strategy.exclude_st or True,
            excludeNewStock=strategy.exclude_new_stock or True,
            minTurnover=strategy.min_turnover,
            isActive=strategy.is_active or False,
            executionCount=strategy.execution_count or 0,
            lastExecutedAt=strategy.last_executed_at.isoformat() if strategy.last_executed_at else None,
            avgExecutionTime=avg_execution_time,
            createdAt=strategy.created_at.isoformat() if strategy.created_at else "",
            updatedAt=strategy.updated_at.isoformat() if strategy.updated_at else ""
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取策略详情失败: {e}")
        raise HTTPException(status_code=500, detail="获取策略详情失败")


@router.post("/", response_model=StrategyResponse)
async def create_strategy(
    strategy_data: StrategyCreate,
    db: Session = Depends(get_db)
):
    """
    创建新策略
    
    Args:
        strategy_data: 策略创建数据
        db: 数据库会话
    
    Returns:
        创建的策略信息
    """
    try:
        # 检查策略名称是否已存在
        existing = db.query(Strategy).filter(Strategy.name == strategy_data.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="策略名称已存在")
        
        # 验证因子ID是否存在
        from app.db.models.factor import Factor
        for factor_id in strategy_data.factorIds:
            factor = db.query(Factor).filter(Factor.id == factor_id).first()
            if not factor:
                raise HTTPException(status_code=400, detail=f"因子ID {factor_id} 不存在")
            if not factor.is_active:
                raise HTTPException(status_code=400, detail=f"因子 {factor.name} 未启用")
        
        # 创建策略
        new_strategy = Strategy(
            name=strategy_data.name,
            description=strategy_data.description,
            factor_ids=strategy_data.factorIds,
            factor_weights=strategy_data.factorWeights or {},
            max_results=strategy_data.maxResults or 50,
            min_market_cap=strategy_data.minMarketCap,
            max_market_cap=strategy_data.maxMarketCap,
            exclude_st=strategy_data.excludeSt,
            exclude_new_stock=strategy_data.excludeNewStock,
            min_turnover=strategy_data.minTurnover,
            is_active=True,
            execution_count=0
        )
        
        db.add(new_strategy)
        db.commit()
        db.refresh(new_strategy)
        
        logger.info(f"创建策略成功: {new_strategy.name}")
        
        return StrategyResponse(
            id=new_strategy.id,
            name=new_strategy.name,
            description=new_strategy.description or "",
            factorIds=new_strategy.factor_ids or [],
            factorWeights=new_strategy.factor_weights or {},
            maxResults=new_strategy.max_results or 50,
            minMarketCap=new_strategy.min_market_cap,
            maxMarketCap=new_strategy.max_market_cap,
            excludeSt=new_strategy.exclude_st or True,
            excludeNewStock=new_strategy.exclude_new_stock or True,
            minTurnover=new_strategy.min_turnover,
            isActive=new_strategy.is_active or False,
            executionCount=0,
            lastExecutedAt=None,
            avgExecutionTime=None,
            createdAt=new_strategy.created_at.isoformat(),
            updatedAt=new_strategy.updated_at.isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建策略失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="创建策略失败")


@router.put("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_id: int,
    strategy_data: StrategyUpdate,
    db: Session = Depends(get_db)
):
    """
    更新策略
    
    Args:
        strategy_id: 策略ID
        strategy_data: 更新数据
        db: 数据库会话
    
    Returns:
        更新后的策略信息
    """
    try:
        strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not strategy:
            raise HTTPException(status_code=404, detail="策略不存在")
        
        # 检查名称是否与其他策略冲突
        if strategy_data.name and strategy_data.name != strategy.name:
            existing = db.query(Strategy).filter(
                Strategy.name == strategy_data.name,
                Strategy.id != strategy_id
            ).first()
            if existing:
                raise HTTPException(status_code=400, detail="策略名称已存在")
        
        # 验证因子ID
        if strategy_data.factorIds:
            from app.db.models.factor import Factor
            for factor_id in strategy_data.factorIds:
                factor = db.query(Factor).filter(Factor.id == factor_id).first()
                if not factor:
                    raise HTTPException(status_code=400, detail=f"因子ID {factor_id} 不存在")
        
        # 更新字段
        if strategy_data.name is not None:
            strategy.name = strategy_data.name
        if strategy_data.description is not None:
            strategy.description = strategy_data.description
        if strategy_data.factorIds is not None:
            strategy.factor_ids = strategy_data.factorIds
        if strategy_data.factorWeights is not None:
            strategy.factor_weights = strategy_data.factorWeights
        if strategy_data.maxResults is not None:
            strategy.max_results = strategy_data.maxResults
        if strategy_data.minMarketCap is not None:
            strategy.min_market_cap = strategy_data.minMarketCap
        if strategy_data.maxMarketCap is not None:
            strategy.max_market_cap = strategy_data.maxMarketCap
        if strategy_data.excludeSt is not None:
            strategy.exclude_st = strategy_data.excludeSt
        if strategy_data.excludeNewStock is not None:
            strategy.exclude_new_stock = strategy_data.excludeNewStock
        if strategy_data.minTurnover is not None:
            strategy.min_turnover = strategy_data.minTurnover
        if strategy_data.isActive is not None:
            strategy.is_active = strategy_data.isActive
        
        db.commit()
        db.refresh(strategy)
        
        logger.info(f"更新策略成功: {strategy.name}")
        
        # 计算平均执行时间
        avg_execution_time = None
        if strategy.execution_count and strategy.execution_count > 0:
            executions = db.query(StrategyExecution).filter(
                StrategyExecution.strategy_id == strategy.id,
                StrategyExecution.execution_time.isnot(None)
            ).all()
            if executions:
                avg_execution_time = sum(e.execution_time for e in executions) / len(executions)
        
        return StrategyResponse(
            id=strategy.id,
            name=strategy.name,
            description=strategy.description or "",
            factorIds=strategy.factor_ids or [],
            factorWeights=strategy.factor_weights or {},
            maxResults=strategy.max_results or 50,
            minMarketCap=strategy.min_market_cap,
            maxMarketCap=strategy.max_market_cap,
            excludeSt=strategy.exclude_st or True,
            excludeNewStock=strategy.exclude_new_stock or True,
            minTurnover=strategy.min_turnover,
            isActive=strategy.is_active or False,
            executionCount=strategy.execution_count or 0,
            lastExecutedAt=strategy.last_executed_at.isoformat() if strategy.last_executed_at else None,
            avgExecutionTime=avg_execution_time,
            createdAt=strategy.created_at.isoformat() if strategy.created_at else "",
            updatedAt=strategy.updated_at.isoformat() if strategy.updated_at else ""
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新策略失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="更新策略失败")


@router.delete("/{strategy_id}")
async def delete_strategy(
    strategy_id: int,
    db: Session = Depends(get_db)
):
    """
    删除策略
    
    Args:
        strategy_id: 策略ID
        db: 数据库会话
    
    Returns:
        删除结果
    """
    try:
        strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not strategy:
            raise HTTPException(status_code=404, detail="策略不存在")
        
        strategy_name = strategy.name
        
        # 删除相关的执行记录和选股结果
        db.query(SelectionResult).filter(
            SelectionResult.strategy_id == strategy_id
        ).delete()
        
        db.query(StrategyExecution).filter(
            StrategyExecution.strategy_id == strategy_id
        ).delete()
        
        db.delete(strategy)
        db.commit()
        
        logger.info(f"删除策略成功: {strategy_name}")
        
        return {"message": "策略删除成功", "name": strategy_name}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除策略失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="删除策略失败")


@router.post("/{strategy_id}/execute", response_model=StrategyExecutionResponse)
async def execute_strategy(
    strategy_id: int,
    execution_request: StrategyExecutionRequest,
    db: Session = Depends(get_db)
):
    """
    执行策略选股
    
    Args:
        strategy_id: 策略ID
        execution_request: 执行请求参数
        db: 数据库会话
    
    Returns:
        执行结果
    """
    try:
        strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not strategy:
            raise HTTPException(status_code=404, detail="策略不存在")
        
        if not strategy.is_active:
            raise HTTPException(status_code=400, detail="策略未启用")
        
        # 执行策略
        execution_result = await strategy_service.execute_strategy(
            strategy=strategy,
            execution_date=execution_request.executionDate,
            dry_run=execution_request.dryRun or False,
            db=db
        )
        
        return execution_result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"执行策略失败: {e}")
        raise HTTPException(status_code=500, detail=f"执行策略失败: {str(e)}")


@router.get("/{strategy_id}/executions")
async def get_strategy_executions(
    strategy_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    获取策略执行历史
    
    Args:
        strategy_id: 策略ID
        skip: 跳过记录数
        limit: 返回记录数限制
        db: 数据库会话
    
    Returns:
        执行历史列表
    """
    try:
        strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not strategy:
            raise HTTPException(status_code=404, detail="策略不存在")
        
        executions = db.query(StrategyExecution).filter(
            StrategyExecution.strategy_id == strategy_id
        ).order_by(StrategyExecution.executed_at.desc()).offset(skip).limit(limit).all()
        
        result = []
        for execution in executions:
            result.append({
                "id": execution.id,
                "executedAt": execution.executed_at.isoformat() if execution.executed_at else "",
                "success": execution.success,
                "message": execution.message or "",
                "executionTime": execution.execution_time,
                "totalStocks": execution.total_stocks or 0,
                "resultCount": execution.result_count or 0,
                "executionDate": execution.execution_date
            })
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取策略执行历史失败: {e}")
        raise HTTPException(status_code=500, detail="获取策略执行历史失败")


@router.get("/{strategy_id}/results")
async def get_strategy_results(
    strategy_id: int,
    execution_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    获取策略选股结果
    
    Args:
        strategy_id: 策略ID
        execution_id: 执行ID，不指定则获取最新结果
        skip: 跳过记录数
        limit: 返回记录数限制
        db: 数据库会话
    
    Returns:
        选股结果列表
    """
    try:
        strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not strategy:
            raise HTTPException(status_code=404, detail="策略不存在")
        
        query = db.query(SelectionResult).filter(SelectionResult.strategy_id == strategy_id)
        
        if execution_id:
            query = query.filter(SelectionResult.execution_id == execution_id)
        else:
            # 获取最新执行的结果
            latest_execution = db.query(StrategyExecution).filter(
                StrategyExecution.strategy_id == strategy_id,
                StrategyExecution.success == True
            ).order_by(StrategyExecution.executed_at.desc()).first()
            
            if latest_execution:
                query = query.filter(SelectionResult.execution_id == latest_execution.id)
        
        results = query.order_by(SelectionResult.rank).offset(skip).limit(limit).all()
        
        result_list = []
        for result in results:
            result_list.append({
                "symbol": result.symbol,
                "name": result.name or "",
                "totalScore": result.total_score,
                "rank": result.rank,
                "factorScores": result.factor_scores or {},
                "price": result.price,
                "marketCap": result.market_cap,
                "peRatio": result.pe_ratio,
                "pbRatio": result.pb_ratio
            })
        
        return result_list
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取策略结果失败: {e}")
        raise HTTPException(status_code=500, detail="获取策略结果失败")