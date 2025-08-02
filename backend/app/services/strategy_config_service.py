"""
策略配置管理服务
提供策略配置的增删改查、权重验证、导入导出等功能
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import logging

from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, and_, or_

from app.db.database import get_db
from app.db.models.factor import StrategyConfig, StrategyTemplate, FactorCorrelation
from app.schemas.builtin_factors import (
    StrategyConfigCreate, StrategyConfigUpdate, StrategyConfigResponse,
    SelectedFactor, WeightPresetType, PaginatedStrategies,
    BatchOperationResult, StrategyPreviewResult
)
from .builtin_factor_engine import builtin_factor_engine

logger = logging.getLogger(__name__)


class StrategyConfigService:
    """策略配置管理服务"""
    
    def __init__(self):
        self.factor_engine = builtin_factor_engine
    
    def create_strategy_config(self, strategy_data: StrategyConfigCreate, 
                              created_by: str = None, db: Session = None) -> StrategyConfigResponse:
        """创建策略配置"""
        if db is None:
            db = next(get_db())
        
        try:
            # 验证因子配置
            validation_result = self._validate_strategy_factors(strategy_data.factors)
            if not validation_result['is_valid']:
                raise ValueError(f"策略配置验证失败: {', '.join(validation_result['errors'])}")
            
            # 生成配置ID
            config_id = str(uuid.uuid4())
            
            # 准备数据库数据
            factor_configs = []
            weight_config = {}
            
            for factor in strategy_data.factors:
                factor_config = {
                    'factor_id': factor.factor_id,
                    'factor_type': factor.factor_type,
                    'factor_name': factor.factor_name,
                    'parameters': factor.parameters.dict() if factor.parameters else {},
                    'weight': factor.weight,
                    'is_enabled': factor.is_enabled
                }
                factor_configs.append(factor_config)
                weight_config[factor.factor_id] = factor.weight
            
            # 创建数据库记录
            db_strategy = StrategyConfig(
                id=config_id,
                name=strategy_data.name,
                description=strategy_data.description,
                factor_configs=factor_configs,
                weight_config=weight_config,
                filters=strategy_data.filters,
                max_results=strategy_data.max_results,
                created_by=created_by,
                tags=','.join(strategy_data.tags) if strategy_data.tags else '',
                usage_count=0,
                is_template=False
            )
            
            db.add(db_strategy)
            db.commit()
            db.refresh(db_strategy)
            
            logger.info(f"策略配置创建成功: {config_id}")
            
            return self._db_to_response(db_strategy)
            
        except Exception as e:
            db.rollback()
            logger.error(f"创建策略配置失败: {e}")
            raise
    
    def get_strategy_config(self, config_id: str, db: Session = None) -> Optional[StrategyConfigResponse]:
        """获取策略配置"""
        if db is None:
            db = next(get_db())
        
        strategy = db.query(StrategyConfig).filter(StrategyConfig.id == config_id).first()
        
        if not strategy:
            return None
        
        return self._db_to_response(strategy)
    
    def update_strategy_config(self, config_id: str, strategy_data: StrategyConfigUpdate,
                              db: Session = None) -> Optional[StrategyConfigResponse]:
        """更新策略配置"""
        if db is None:
            db = next(get_db())
        
        try:
            strategy = db.query(StrategyConfig).filter(StrategyConfig.id == config_id).first()
            
            if not strategy:
                return None
            
            # 更新字段
            update_data = strategy_data.dict(exclude_unset=True)
            
            for field, value in update_data.items():
                if field == 'factors' and value is not None:
                    # 验证因子配置
                    validation_result = self._validate_strategy_factors(value)
                    if not validation_result['is_valid']:
                        raise ValueError(f"策略配置验证失败: {', '.join(validation_result['errors'])}")
                    
                    # 更新因子配置
                    factor_configs = []
                    weight_config = {}
                    
                    for factor in value:
                        factor_config = {
                            'factor_id': factor.factor_id,
                            'factor_type': factor.factor_type,
                            'factor_name': factor.factor_name,
                            'parameters': factor.parameters.dict() if factor.parameters else {},
                            'weight': factor.weight,
                            'is_enabled': factor.is_enabled
                        }
                        factor_configs.append(factor_config)
                        weight_config[factor.factor_id] = factor.weight
                    
                    strategy.factor_configs = factor_configs
                    strategy.weight_config = weight_config
                
                elif field == 'tags' and value is not None:
                    strategy.tags = ','.join(value) if value else ''
                
                elif field in ['name', 'description', 'filters', 'max_results']:
                    setattr(strategy, field, value)
            
            strategy.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(strategy)
            
            logger.info(f"策略配置更新成功: {config_id}")
            
            return self._db_to_response(strategy)
            
        except Exception as e:
            db.rollback()
            logger.error(f"更新策略配置失败: {e}")
            raise
    
    def delete_strategy_config(self, config_id: str, db: Session = None) -> bool:
        """删除策略配置"""
        if db is None:
            db = next(get_db())
        
        try:
            strategy = db.query(StrategyConfig).filter(StrategyConfig.id == config_id).first()
            
            if not strategy:
                return False
            
            db.delete(strategy)
            db.commit()
            
            logger.info(f"策略配置删除成功: {config_id}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"删除策略配置失败: {e}")
            raise
    
    def list_strategy_configs(self, page: int = 1, size: int = 20, 
                             created_by: str = None, tags: List[str] = None,
                             search: str = None, sort_by: str = "created_at",
                             sort_order: str = "desc", db: Session = None) -> PaginatedStrategies:
        """获取策略配置列表"""
        if db is None:
            db = next(get_db())
        
        query = db.query(StrategyConfig)
        
        # 构建过滤条件
        filters = []
        
        if created_by:
            filters.append(StrategyConfig.created_by == created_by)
        
        if tags:
            for tag in tags:
                filters.append(StrategyConfig.tags.contains(tag))
        
        if search:
            search_filter = or_(
                StrategyConfig.name.contains(search),
                StrategyConfig.description.contains(search)
            )
            filters.append(search_filter)
        
        if filters:
            query = query.filter(and_(*filters))
        
        # 排序
        sort_column = getattr(StrategyConfig, sort_by, StrategyConfig.created_at)
        if sort_order.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # 分页
        total = query.count()
        strategies = query.offset((page - 1) * size).limit(size).all()
        
        # 转换响应
        items = [self._db_to_response(strategy) for strategy in strategies]
        
        return PaginatedStrategies(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size
        )
    
    def record_strategy_usage(self, config_id: str, db: Session = None):
        """记录策略使用"""
        if db is None:
            db = next(get_db())
        
        try:
            strategy = db.query(StrategyConfig).filter(StrategyConfig.id == config_id).first()
            
            if strategy:
                strategy.usage_count = (strategy.usage_count or 0) + 1
                strategy.last_used_at = datetime.utcnow()
                db.commit()
                
        except Exception as e:
            logger.error(f"记录策略使用失败: {e}")
    
    def duplicate_strategy_config(self, config_id: str, new_name: str = None,
                                 created_by: str = None, db: Session = None) -> Optional[StrategyConfigResponse]:
        """复制策略配置"""
        if db is None:
            db = next(get_db())
        
        try:
            original = db.query(StrategyConfig).filter(StrategyConfig.id == config_id).first()
            
            if not original:
                return None
            
            # 创建新的配置ID
            new_config_id = str(uuid.uuid4())
            
            # 生成新名称
            if not new_name:
                new_name = f"{original.name} - 副本"
            
            # 创建新记录
            new_strategy = StrategyConfig(
                id=new_config_id,
                name=new_name,
                description=original.description,
                factor_configs=original.factor_configs,
                weight_config=original.weight_config,
                filters=original.filters,
                max_results=original.max_results,
                created_by=created_by or original.created_by,
                tags=original.tags,
                usage_count=0,
                is_template=False
            )
            
            db.add(new_strategy)
            db.commit()
            db.refresh(new_strategy)
            
            logger.info(f"策略配置复制成功: {config_id} -> {new_config_id}")
            
            return self._db_to_response(new_strategy)
            
        except Exception as e:
            db.rollback()
            logger.error(f"复制策略配置失败: {e}")
            raise
    
    def batch_delete_strategies(self, config_ids: List[str], 
                               db: Session = None) -> BatchOperationResult:
        """批量删除策略配置"""
        if db is None:
            db = next(get_db())
        
        success_count = 0
        failed_count = 0
        failed_items = []
        
        for config_id in config_ids:
            try:
                if self.delete_strategy_config(config_id, db):
                    success_count += 1
                else:
                    failed_count += 1
                    failed_items.append({"id": config_id, "error": "策略配置不存在"})
            except Exception as e:
                failed_count += 1
                failed_items.append({"id": config_id, "error": str(e)})
        
        return BatchOperationResult(
            success_count=success_count,
            failed_count=failed_count,
            failed_items=failed_items
        )
    
    def export_strategy_config(self, config_id: str, db: Session = None) -> Optional[Dict[str, Any]]:
        """导出策略配置为JSON"""
        if db is None:
            db = next(get_db())
        
        strategy = db.query(StrategyConfig).filter(StrategyConfig.id == config_id).first()
        
        if not strategy:
            return None
        
        export_data = {
            'version': '1.0',
            'export_time': datetime.utcnow().isoformat(),
            'strategy': {
                'name': strategy.name,
                'description': strategy.description,
                'factor_configs': strategy.factor_configs,
                'weight_config': strategy.weight_config,
                'filters': strategy.filters,
                'max_results': strategy.max_results,
                'tags': strategy.tags.split(',') if strategy.tags else []
            }
        }
        
        return export_data
    
    def import_strategy_config(self, import_data: Dict[str, Any], created_by: str = None,
                              db: Session = None) -> StrategyConfigResponse:
        """从JSON导入策略配置"""
        if db is None:
            db = next(get_db())
        
        try:
            # 验证导入数据格式
            if 'strategy' not in import_data:
                raise ValueError("导入数据格式错误：缺少strategy字段")
            
            strategy_data = import_data['strategy']
            
            # 创建策略配置对象
            factors = []
            for factor_config in strategy_data.get('factor_configs', []):
                factor = SelectedFactor(
                    factor_id=factor_config['factor_id'],
                    factor_type=factor_config.get('factor_type', 'builtin'),
                    factor_name=factor_config['factor_name'],
                    parameters=factor_config.get('parameters', {}),
                    weight=factor_config['weight'],
                    is_enabled=factor_config.get('is_enabled', True)
                )
                factors.append(factor)
            
            strategy_create = StrategyConfigCreate(
                name=strategy_data['name'],
                description=strategy_data.get('description', ''),
                factors=factors,
                filters=strategy_data.get('filters', {}),
                max_results=strategy_data.get('max_results', 100),
                tags=strategy_data.get('tags', [])
            )
            
            # 创建策略配置
            return self.create_strategy_config(strategy_create, created_by, db)
            
        except Exception as e:
            logger.error(f"导入策略配置失败: {e}")
            raise
    
    def get_strategy_preview(self, factor_configs: List[SelectedFactor]) -> StrategyPreviewResult:
        """获取策略预览"""
        # 验证因子配置
        validation_result = self._validate_strategy_factors(factor_configs)
        
        # 计算配置摘要
        config_summary = {
            'total_factors': len(factor_configs),
            'enabled_factors': len([f for f in factor_configs if f.is_enabled]),
            'categories': self._get_factor_categories(factor_configs),
            'total_weight': sum(f.weight for f in factor_configs if f.is_enabled)
        }
        
        # 因子权重信息
        factor_weights = []
        for factor in factor_configs:
            if factor.is_enabled:
                factor_info = self.factor_engine.get_factor_info(factor.factor_id)
                factor_weights.append({
                    'factor_id': factor.factor_id,
                    'factor_name': factor.factor_name,
                    'category': factor_info['category'] if factor_info else 'unknown',
                    'weight': factor.weight,
                    'weight_percentage': (factor.weight * 100) if factor.weight else 0
                })
        
        # 预期结果数量
        estimated_results = {
            'min_results': 20,
            'max_results': 200,
            'expected_results': 100
        }
        
        # 风险评估
        risk_assessment = self._assess_strategy_risk(factor_configs)
        
        # 建议列表
        recommendations = []
        if validation_result['warnings']:
            recommendations.extend(validation_result['warnings'])
        
        if config_summary['total_weight'] < 0.99:
            recommendations.append("权重总和小于100%，建议调整权重分配")
        
        if config_summary['enabled_factors'] < 3:
            recommendations.append("建议使用3个以上因子以提高策略稳定性")
        
        return StrategyPreviewResult(
            config_summary=config_summary,
            factor_weights=factor_weights,
            estimated_results=estimated_results,
            risk_assessment=risk_assessment,
            recommendations=recommendations
        )
    
    def _validate_strategy_factors(self, factors: List[SelectedFactor]) -> Dict[str, Any]:
        """验证策略因子配置"""
        factor_configs = []
        for factor in factors:
            config = {
                'factor_id': factor.factor_id,
                'weight': factor.weight,
                'parameters': factor.parameters.dict() if factor.parameters else {}
            }
            factor_configs.append(config)
        
        return self.factor_engine.validate_factor_configs(factor_configs)
    
    def _get_factor_categories(self, factors: List[SelectedFactor]) -> Dict[str, int]:
        """获取因子分类统计"""
        categories = {}
        for factor in factors:
            if factor.is_enabled:
                factor_info = self.factor_engine.get_factor_info(factor.factor_id)
                if factor_info:
                    category = factor_info['category']
                    categories[category] = categories.get(category, 0) + 1
        return categories
    
    def _assess_strategy_risk(self, factors: List[SelectedFactor]) -> Dict[str, str]:
        """评估策略风险"""
        categories = self._get_factor_categories(factors)
        enabled_count = len([f for f in factors if f.is_enabled])
        
        # 多样性风险
        if len(categories) == 1:
            diversity_risk = "high"
        elif len(categories) == 2:
            diversity_risk = "medium"
        else:
            diversity_risk = "low"
        
        # 复杂度风险
        if enabled_count > 8:
            complexity_risk = "high"
        elif enabled_count > 5:
            complexity_risk = "medium"
        else:
            complexity_risk = "low"
        
        # 整体风险评级
        risk_levels = [diversity_risk, complexity_risk]
        if "high" in risk_levels:
            overall_risk = "high"
        elif "medium" in risk_levels:
            overall_risk = "medium"
        else:
            overall_risk = "low"
        
        return {
            'overall': overall_risk,
            'diversity': diversity_risk,
            'complexity': complexity_risk,
            'explanation': self._get_risk_explanation(overall_risk)
        }
    
    def _get_risk_explanation(self, risk_level: str) -> str:
        """获取风险等级说明"""
        explanations = {
            'low': '策略风险较低，因子配置合理，多样性良好',
            'medium': '策略风险中等，建议优化因子配置或权重分配',
            'high': '策略风险较高，建议增加因子多样性或减少复杂度'
        }
        return explanations.get(risk_level, '风险评估暂不可用')
    
    def _db_to_response(self, db_strategy: StrategyConfig) -> StrategyConfigResponse:
        """将数据库对象转换为响应对象"""
        # 转换因子配置
        factors = []
        for factor_config in db_strategy.factor_configs or []:
            factor = SelectedFactor(
                factor_id=factor_config['factor_id'],
                factor_type=factor_config.get('factor_type', 'builtin'),
                factor_name=factor_config['factor_name'],
                parameters=factor_config.get('parameters', {}),
                weight=factor_config['weight'],
                is_enabled=factor_config.get('is_enabled', True)
            )
            factors.append(factor)
        
        return StrategyConfigResponse(
            id=db_strategy.id,
            name=db_strategy.name,
            description=db_strategy.description or '',
            factors=factors,
            filters=db_strategy.filters or {},
            max_results=db_strategy.max_results,
            tags=db_strategy.tags.split(',') if db_strategy.tags else [],
            created_by=db_strategy.created_by,
            last_used_at=db_strategy.last_used_at,
            usage_count=db_strategy.usage_count or 0,
            is_template=db_strategy.is_template or False,
            created_at=db_strategy.created_at,
            updated_at=db_strategy.updated_at
        )


# 全局策略配置服务实例
strategy_config_service = StrategyConfigService()