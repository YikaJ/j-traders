"""
策略管理服务
处理策略的创建、更新、执行等核心功能
"""

from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.db.models.strategy import Strategy, StrategyExecution, StrategyTemplate
from app.db.models.factor import Factor
from app.schemas.strategy import (
    StrategyCreate, StrategyUpdate, StrategyResponse,
    StrategyListRequest, StrategyListResponse,
    StrategyExecutionRequest, StrategyExecutionResult,
    SelectedStock, StrategyExecutionDetail
)
from app.schemas.strategy_execution import ExecutionStatus
from app.services.unified_factor_service import unified_factor_service
from app.services.tushare_service import tushare_service
from app.services.strategy_execution_engine import strategy_execution_engine

logger = logging.getLogger(__name__)


class StrategyManagementService:
    """策略管理服务"""
    
    def __init__(self):
        self.factor_service = unified_factor_service
        self.tushare_service = tushare_service
    
    async def create_strategy(self, db: Session, strategy_data: StrategyCreate, created_by: str = None) -> StrategyResponse:
        """创建新策略"""
        try:
            # 验证因子存在性
            await self._validate_factors(db, strategy_data.factors)
            
            # 创建策略记录
            db_strategy = Strategy(
                name=strategy_data.name,
                description=strategy_data.description,
                factors=[factor.dict() for factor in strategy_data.factors],
                filters=strategy_data.filters.dict() if strategy_data.filters else None,
                config=strategy_data.config.dict() if strategy_data.config else None,
                created_by=created_by
            )
            
            db.add(db_strategy)
            db.commit()
            db.refresh(db_strategy)
            
            logger.info(f"策略创建成功: {db_strategy.strategy_id}")
            return self._strategy_to_response(db_strategy)
            
        except Exception as e:
            logger.error(f"创建策略失败: {e}")
            db.rollback()
            raise
    
    async def get_strategies(self, db: Session, request: StrategyListRequest) -> StrategyListResponse:
        """获取策略列表"""
        try:
            query = db.query(Strategy)
            
            # 应用筛选条件
            if request.is_active is not None:
                query = query.filter(Strategy.is_active == request.is_active)
            
            if request.created_by:
                query = query.filter(Strategy.created_by == request.created_by)
            
            if request.keyword:
                keyword_filter = or_(
                    Strategy.name.contains(request.keyword),
                    Strategy.description.contains(request.keyword)
                )
                query = query.filter(keyword_filter)
            
            # 获取总数
            total = query.count()
            
            # 应用分页和排序
            strategies = query.order_by(desc(Strategy.created_at))\
                            .offset(request.skip)\
                            .limit(request.limit)\
                            .all()
            
            strategy_responses = [self._strategy_to_response(strategy) for strategy in strategies]
            
            return StrategyListResponse(
                strategies=strategy_responses,
                total=total,
                skip=request.skip,
                limit=request.limit
            )
            
        except Exception as e:
            logger.error(f"获取策略列表失败: {e}")
            raise
    
    async def get_strategy(self, db: Session, strategy_id: str) -> Optional[StrategyResponse]:
        """获取单个策略"""
        try:
            strategy = db.query(Strategy).filter(Strategy.strategy_id == strategy_id).first()
            if not strategy:
                return None
            
            return self._strategy_to_response(strategy)
            
        except Exception as e:
            logger.error(f"获取策略失败: {e}")
            raise
    
    async def update_strategy(self, db: Session, strategy_id: str, strategy_data: StrategyUpdate) -> Optional[StrategyResponse]:
        """更新策略"""
        try:
            strategy = db.query(Strategy).filter(Strategy.strategy_id == strategy_id).first()
            if not strategy:
                return None
            
            # 验证因子（如果有更新）
            if strategy_data.factors:
                await self._validate_factors(db, strategy_data.factors)
            
            # 更新字段
            update_data = strategy_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                if field == 'factors' and value:
                    setattr(strategy, field, [factor.dict() for factor in value])
                elif field == 'filters' and value:
                    setattr(strategy, field, value.dict())
                elif field == 'config' and value:
                    setattr(strategy, field, value.dict())
                else:
                    setattr(strategy, field, value)
            
            db.commit()
            db.refresh(strategy)
            
            logger.info(f"策略更新成功: {strategy_id}")
            return self._strategy_to_response(strategy)
            
        except Exception as e:
            logger.error(f"更新策略失败: {e}")
            db.rollback()
            raise
    
    async def delete_strategy(self, db: Session, strategy_id: str) -> bool:
        """删除策略"""
        try:
            strategy = db.query(Strategy).filter(Strategy.strategy_id == strategy_id).first()
            if not strategy:
                return False
            
            db.delete(strategy)
            db.commit()
            
            logger.info(f"策略删除成功: {strategy_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除策略失败: {e}")
            db.rollback()
            raise
    
    async def execute_strategy(self, db: Session, strategy_id: str, request: StrategyExecutionRequest) -> StrategyExecutionResult:
        """执行策略"""
        try:
            strategy = db.query(Strategy).filter(Strategy.strategy_id == strategy_id).first()
            if not strategy:
                raise ValueError(f"策略不存在: {strategy_id}")
            
            if not strategy.is_active:
                raise ValueError(f"策略已禁用: {strategy_id}")
            
            # 使用新的执行引擎
            result = await strategy_execution_engine.execute_strategy(db, strategy, request)
            
            # 如果需要保存结果，更新策略统计
            if request.save_result and result.status == ExecutionStatus.COMPLETED:
                strategy.execution_count = (strategy.execution_count or 0) + 1
                strategy.last_executed_at = datetime.now()
                strategy.last_result_count = result.final_stock_count or 0
                
                # 更新平均执行时间
                if result.total_time:
                    if strategy.avg_execution_time:
                        strategy.avg_execution_time = (strategy.avg_execution_time * (strategy.execution_count - 1) + result.total_time) / strategy.execution_count
                    else:
                        strategy.avg_execution_time = result.total_time
                
                db.commit()
            
            logger.info(f"策略执行完成: {strategy_id}, 状态: {result.status}")
            return result
                
        except Exception as e:
            logger.error(f"执行策略失败: {e}")
            db.rollback()
            raise
    
    async def get_execution_history(self, db: Session, strategy_id: str, limit: int = 20) -> List[StrategyExecutionResult]:
        """获取策略执行历史"""
        try:
            strategy = db.query(Strategy).filter(Strategy.strategy_id == strategy_id).first()
            if not strategy:
                return []
            
            executions = db.query(StrategyExecution)\
                          .filter(StrategyExecution.strategy_id == strategy.id)\
                          .order_by(desc(StrategyExecution.created_at))\
                          .limit(limit)\
                          .all()
            
            return [self._execution_to_result(execution, strategy_id) for execution in executions]
            
        except Exception as e:
            logger.error(f"获取执行历史失败: {e}")
            raise
    
    async def get_execution_detail(self, db: Session, execution_id: str) -> Optional[StrategyExecutionDetail]:
        """获取执行详情"""
        try:
            execution = db.query(StrategyExecution).filter(StrategyExecution.execution_id == execution_id).first()
            if not execution:
                return None
            
            strategy = execution.strategy
            selected_stocks = []
            
            if execution.selected_stocks:
                selected_stocks = [SelectedStock(**stock) for stock in execution.selected_stocks]
            
            return StrategyExecutionDetail(
                execution_id=execution.execution_id,
                strategy_id=strategy.strategy_id,
                execution_date=execution.execution_date,
                execution_time=execution.execution_time or 0,
                stock_count=execution.stock_count or 0,
                is_dry_run=execution.is_dry_run,
                status=execution.status,
                error_message=execution.error_message,
                created_at=execution.created_at,
                selected_stocks=selected_stocks,
                factor_performance=execution.factor_performance or {},
                execution_log=execution.execution_log or []
            )
            
        except Exception as e:
            logger.error(f"获取执行详情失败: {e}")
            raise
    
    async def _validate_factors(self, db: Session, factors: List) -> None:
        """验证因子存在性"""
        factor_ids = [factor.factor_id for factor in factors]
        
        # 尝试通过factor_id查找
        existing_factors = db.query(Factor).filter(Factor.factor_id.in_(factor_ids)).all()
        existing_ids = {factor.factor_id for factor in existing_factors}
        
        # 如果通过factor_id没找到，尝试通过数字ID查找
        if not existing_factors:
            try:
                numeric_ids = [int(fid) for fid in factor_ids if fid.isdigit()]
                if numeric_ids:
                    existing_factors = db.query(Factor).filter(Factor.id.in_(numeric_ids)).all()
                    existing_ids = {str(factor.id) for factor in existing_factors}
            except ValueError:
                pass
        
        missing_ids = set(factor_ids) - existing_ids
        if missing_ids:
            raise ValueError(f"因子不存在: {', '.join(missing_ids)}")
    
    def _strategy_to_response(self, strategy: Strategy) -> StrategyResponse:
        """转换策略模型为响应模型"""
        from app.schemas.strategy import StrategyFactor, StrategyFilter, StrategyConfig
        
        # 转换因子配置
        factors = []
        if strategy.factors:
            for factor_data in strategy.factors:
                factors.append(StrategyFactor(**factor_data))
        
        # 转换筛选条件
        filters = None
        if strategy.filters:
            filters = StrategyFilter(**strategy.filters)
        
        # 转换策略配置
        config = None
        if strategy.config:
            config = StrategyConfig(**strategy.config)
        
        return StrategyResponse(
            strategy_id=strategy.strategy_id,
            name=strategy.name,
            description=strategy.description,
            factors=factors,
            filters=filters,
            config=config,
            is_active=strategy.is_active,
            created_at=strategy.created_at,
            updated_at=strategy.updated_at,
            created_by=strategy.created_by,
            execution_count=strategy.execution_count,
            last_executed_at=strategy.last_executed_at,
            avg_execution_time=strategy.avg_execution_time,
            last_result_count=strategy.last_result_count
        )
    
    def _execution_to_result(self, execution: StrategyExecution, strategy_id: str) -> StrategyExecutionResult:
        """转换执行记录为结果模型"""
        return StrategyExecutionResult(
            execution_id=execution.execution_id,
            strategy_id=strategy_id,
            execution_date=execution.execution_date,
            execution_time=execution.execution_time or 0,
            stock_count=execution.stock_count or 0,
            is_dry_run=execution.is_dry_run,
            status=execution.status,
            error_message=execution.error_message,
            created_at=execution.created_at
        )


# 全局实例
strategy_management_service = StrategyManagementService()