"""
策略执行API端点
提供策略执行的完整控制接口
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.db.database import get_db
from app.schemas.strategy_execution import (
    StrategyExecutionRequest, StrategyExecutionResult, StrategyExecutionDetailResult,
    StockFilter, AvailableScope, ExecutionProgress, CancelExecutionRequest
)
from app.services.strategy_execution_engine import strategy_execution_engine
from app.services.strategy_management_service import strategy_management_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/scopes", response_model=AvailableScope)
async def get_available_scopes(db: Session = Depends(get_db)):
    """
    获取可用的股票范围选项
    
    返回可用的行业、概念、指数、市场等筛选选项
    """
    try:
        return await strategy_execution_engine.get_available_scopes(db)
    except Exception as e:
        logger.error(f"获取股票范围选项失败: {e}")
        raise HTTPException(status_code=500, detail="获取股票范围选项失败")


@router.post("/{strategy_id}/execute", response_model=StrategyExecutionResult)
async def execute_strategy_advanced(
    strategy_id: str,
    request: StrategyExecutionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    执行策略（高级版本）
    
    支持：
    - 自定义股票筛选条件
    - 实时日志记录
    - 进度追踪
    - 数据缓存控制
    - 执行时间限制
    """
    try:
        # 获取策略信息
        strategy = await strategy_management_service.get_strategy(db, strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail=f"策略不存在: {strategy_id}")
        
        if not strategy.is_active:
            raise HTTPException(status_code=400, detail=f"策略已禁用: {strategy_id}")
        
        # 验证请求参数
        if not request.stock_filter:
            raise HTTPException(status_code=400, detail="必须指定股票筛选条件")
        
        logger.info(f"开始执行策略: {strategy_id}, 股票范围: {request.stock_filter.scope}")
        
        # 异步执行策略
        def execute_in_background():
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    strategy_execution_engine.execute_strategy(db, strategy, request)
                )
                return result
            finally:
                loop.close()
        
        # 后台执行
        background_tasks.add_task(execute_in_background)
        
        # 立即返回执行开始的响应
        from app.schemas.strategy_execution import ExecutionStatus
        from datetime import datetime
        import uuid
        
        execution_id = str(uuid.uuid4())
        initial_result = StrategyExecutionResult(
            execution_id=execution_id,
            strategy_id=strategy_id,
            execution_date=request.execution_date or datetime.now().strftime("%Y-%m-%d"),
            status=ExecutionStatus.PENDING,
            start_time=datetime.now(),
            stock_filter=request.stock_filter,
            is_dry_run=request.dry_run
        )
        
        return initial_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"执行策略失败: {e}")
        raise HTTPException(status_code=500, detail=f"执行策略失败: {str(e)}")


@router.get("/{strategy_id}/execute-sync", response_model=StrategyExecutionDetailResult)
async def execute_strategy_sync(
    strategy_id: str,
    request: StrategyExecutionRequest,
    db: Session = Depends(get_db)
):
    """
    同步执行策略
    
    等待执行完成后返回完整结果，适用于较小的股票池
    """
    try:
        # 获取策略信息
        strategy = await strategy_management_service.get_strategy(db, strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail=f"策略不存在: {strategy_id}")
        
        if not strategy.is_active:
            raise HTTPException(status_code=400, detail=f"策略已禁用: {strategy_id}")
        
        logger.info(f"同步执行策略: {strategy_id}")
        
        # 同步执行策略
        result = await strategy_execution_engine.execute_strategy(db, strategy, request)
        
        # 返回详细结果（包含选中的股票）
        # 这里需要从执行结果中获取选中的股票
        # 目前返回基础结果
        return StrategyExecutionDetailResult(**result.dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"同步执行策略失败: {e}")
        raise HTTPException(status_code=500, detail=f"同步执行策略失败: {str(e)}")


@router.get("/executions/{execution_id}/progress")
async def get_execution_progress(execution_id: str):
    """
    获取策略执行进度
    
    返回实时的执行进度和日志信息
    """
    try:
        progress = strategy_execution_engine.get_execution_progress(execution_id)
        if not progress:
            raise HTTPException(status_code=404, detail=f"执行记录不存在: {execution_id}")
        
        # 构造进度响应
        from app.schemas.strategy_execution import ExecutionProgress
        
        latest_log = progress.logs[-1] if progress.logs else None
        
        progress_response = ExecutionProgress(
            execution_id=execution_id,
            status=progress.status,
            current_stage=progress.current_stage or "unknown",
            overall_progress=progress.overall_progress,
            stage_progress=0.0,  # 需要从当前阶段获取
            latest_log=latest_log
        )
        
        return progress_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取执行进度失败: {e}")
        raise HTTPException(status_code=500, detail="获取执行进度失败")


@router.get("/executions/{execution_id}/logs")
async def get_execution_logs(
    execution_id: str,
    level: Optional[str] = None,
    stage: Optional[str] = None,
    limit: int = 100
):
    """
    获取策略执行日志
    
    支持按级别和阶段筛选日志
    """
    try:
        execution = strategy_execution_engine.get_execution_progress(execution_id)
        if not execution:
            raise HTTPException(status_code=404, detail=f"执行记录不存在: {execution_id}")
        
        logs = execution.logs
        
        # 应用筛选条件
        if level:
            logs = [log for log in logs if log.level.value == level]
        
        if stage:
            logs = [log for log in logs if log.stage == stage]
        
        # 限制返回数量
        if limit > 0:
            logs = logs[-limit:]
        
        return {
            "execution_id": execution_id,
            "total_logs": len(execution.logs),
            "filtered_logs": len(logs),
            "logs": logs
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取执行日志失败: {e}")
        raise HTTPException(status_code=500, detail="获取执行日志失败")


@router.post("/executions/{execution_id}/cancel")
async def cancel_execution(
    execution_id: str,
    request: CancelExecutionRequest
):
    """
    取消正在执行的策略
    """
    try:
        success = await strategy_execution_engine.cancel_execution(
            execution_id, request.reason
        )
        
        if not success:
            raise HTTPException(status_code=404, detail=f"执行记录不存在或已完成: {execution_id}")
        
        return {"message": "策略执行已取消", "execution_id": execution_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消执行失败: {e}")
        raise HTTPException(status_code=500, detail="取消执行失败")


@router.get("/running")
async def get_running_executions():
    """
    获取当前正在执行的策略列表
    """
    try:
        running_executions = []
        
        for execution_id, execution in strategy_execution_engine.running_executions.items():
            running_executions.append({
                "execution_id": execution_id,
                "strategy_id": execution.strategy_id,
                "status": execution.status,
                "current_stage": execution.current_stage,
                "overall_progress": execution.overall_progress,
                "start_time": execution.start_time,
                "execution_date": execution.execution_date
            })
        
        return {
            "running_count": len(running_executions),
            "executions": running_executions
        }
        
    except Exception as e:
        logger.error(f"获取运行中执行列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取运行中执行列表失败")


@router.post("/validate-filter")
async def validate_stock_filter(stock_filter: StockFilter):
    """
    验证股票筛选条件
    
    检查筛选条件的有效性和预估结果数量
    """
    try:
        # 这里应该验证筛选条件的有效性
        # 目前返回模拟验证结果
        
        estimated_count = 0
        warnings = []
        
        # 根据筛选范围估算股票数量
        if stock_filter.scope.value == "all":
            estimated_count = 4800
        elif stock_filter.scope.value == "industry":
            estimated_count = 200 if stock_filter.industries else 0
            if not stock_filter.industries:
                warnings.append("未指定具体行业")
        elif stock_filter.scope.value == "concept":
            estimated_count = 100 if stock_filter.concepts else 0
            if not stock_filter.concepts:
                warnings.append("未指定具体概念")
        elif stock_filter.scope.value == "custom":
            estimated_count = len(stock_filter.custom_stocks) if stock_filter.custom_stocks else 0
            if not stock_filter.custom_stocks:
                warnings.append("未指定自定义股票列表")
        
        # 应用基础筛选条件的影响
        if stock_filter.exclude_st:
            estimated_count = int(estimated_count * 0.95)  # 估算95%非ST
        
        if stock_filter.exclude_new_stock:
            estimated_count = int(estimated_count * 0.98)  # 估算98%非新股
        
        if stock_filter.min_market_cap or stock_filter.max_market_cap:
            estimated_count = int(estimated_count * 0.7)  # 市值筛选估算保留70%
        
        return {
            "is_valid": len(warnings) == 0,
            "estimated_stock_count": estimated_count,
            "warnings": warnings,
            "estimated_execution_time": estimated_count / 100 * 2,  # 估算执行时间（秒）
            "scope_summary": {
                "scope_type": stock_filter.scope.value,
                "has_market_filter": bool(stock_filter.markets),
                "has_industry_filter": bool(stock_filter.industries),
                "has_concept_filter": bool(stock_filter.concepts),
                "has_custom_stocks": bool(stock_filter.custom_stocks),
                "basic_filters_count": sum([
                    stock_filter.exclude_st,
                    stock_filter.exclude_new_stock,
                    stock_filter.exclude_suspend,
                    bool(stock_filter.min_market_cap),
                    bool(stock_filter.max_market_cap)
                ])
            }
        }
        
    except Exception as e:
        logger.error(f"验证股票筛选条件失败: {e}")
        raise HTTPException(status_code=500, detail="验证股票筛选条件失败")


@router.get("/stats")
async def get_execution_stats():
    """
    获取策略执行统计信息
    """
    try:
        # 这里应该从数据库获取实际统计信息
        # 目前返回模拟数据
        
        return {
            "total_executions": 156,
            "successful_executions": 142,
            "failed_executions": 14,
            "average_execution_time": 45.2,
            "most_used_scope": "industry",
            "cache_hit_rate": 0.68,
            "last_24h_executions": 23,
            "active_strategies": 8
        }
        
    except Exception as e:
        logger.error(f"获取执行统计失败: {e}")
        raise HTTPException(status_code=500, detail="获取执行统计失败")