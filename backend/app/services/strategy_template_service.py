"""
策略模板管理服务
提供预设策略模板和模板应用功能
"""

import uuid
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.database import get_db
from app.db.models.factor import StrategyTemplate
from app.schemas.builtin_factors import (
    StrategyTemplateResponse, TemplateCustomizations,
    StrategyTemplateCategory, RiskLevel, SelectedFactor,
    StrategyConfigCreate, FactorParameters
)
from .builtin_factor_engine import builtin_factor_engine

logger = logging.getLogger(__name__)


class StrategyTemplateService:
    """策略模板管理服务"""
    
    def __init__(self):
        self.factor_engine = builtin_factor_engine
        self._initialize_default_templates()
    
    def _initialize_default_templates(self):
        """初始化默认策略模板"""
        # 这些模板会在数据库初始化时创建
        self.default_templates = [
            {
                "id": "value_investing",
                "name": "value_investing",
                "display_name": "价值投资策略",
                "description": "基于估值因子的价值投资策略，适合长期持有",
                "category": StrategyTemplateCategory.VALUE,
                "factor_configs": [
                    {"factor_id": "sma_50", "weight": 0.3},
                    {"factor_id": "sma_200", "weight": 0.2},
                    {"factor_id": "bollinger_bands", "weight": 0.3},
                    {"factor_id": "volume_ratio_20", "weight": 0.2}
                ],
                "risk_level": RiskLevel.LOW,
                "expected_return_range": "5-15%",
                "usage_scenarios": "适合风险偏好较低的投资者，看重基本面价值"
            },
            {
                "id": "growth_momentum",
                "name": "growth_momentum", 
                "display_name": "成长动量策略",
                "description": "结合成长和动量因子，捕捉快速成长的股票",
                "category": StrategyTemplateCategory.GROWTH,
                "factor_configs": [
                    {"factor_id": "rsi_14", "weight": 0.25},
                    {"factor_id": "macd", "weight": 0.25},
                    {"factor_id": "sma_20", "weight": 0.2},
                    {"factor_id": "momentum_10", "weight": 0.3}
                ],
                "risk_level": RiskLevel.MEDIUM,
                "expected_return_range": "10-25%",
                "usage_scenarios": "适合追求较高收益的投资者，能承受一定波动"
            },
            {
                "id": "technical_analysis",
                "name": "technical_analysis",
                "display_name": "技术分析策略", 
                "description": "基于技术指标的短期交易策略",
                "category": StrategyTemplateCategory.TECHNICAL,
                "factor_configs": [
                    {"factor_id": "rsi_14", "weight": 0.2},
                    {"factor_id": "macd", "weight": 0.2},
                    {"factor_id": "kdj", "weight": 0.2},
                    {"factor_id": "bollinger_bands", "weight": 0.2},
                    {"factor_id": "williams_r_14", "weight": 0.2}
                ],
                "risk_level": RiskLevel.HIGH,
                "expected_return_range": "15-35%",
                "usage_scenarios": "适合技术分析爱好者，关注短期价格走势"
            },
            {
                "id": "momentum_strategy",
                "name": "momentum_strategy",
                "display_name": "动量策略",
                "description": "纯动量因子策略，追踪市场趋势",
                "category": StrategyTemplateCategory.MOMENTUM,
                "factor_configs": [
                    {"factor_id": "momentum_5", "weight": 0.3},
                    {"factor_id": "momentum_10", "weight": 0.25},
                    {"factor_id": "roc_12", "weight": 0.25},
                    {"factor_id": "ma_crossover", "weight": 0.2}
                ],
                "risk_level": RiskLevel.HIGH,
                "expected_return_range": "12-30%",
                "usage_scenarios": "适合趋势跟踪者，在明确趋势中获取收益"
            },
            {
                "id": "quality_factor",
                "name": "quality_factor",
                "display_name": "质量因子策略",
                "description": "注重股票质量的综合策略",
                "category": StrategyTemplateCategory.QUALITY,
                "factor_configs": [
                    {"factor_id": "sma_50", "weight": 0.25},
                    {"factor_id": "obv", "weight": 0.2},
                    {"factor_id": "mfi_14", "weight": 0.2},
                    {"factor_id": "vwap_20", "weight": 0.2},
                    {"factor_id": "ad_line", "weight": 0.15}
                ],
                "risk_level": RiskLevel.LOW,
                "expected_return_range": "8-18%",
                "usage_scenarios": "适合注重企业质量的长期投资者"
            }
        ]
    
    def get_all_templates(self, db: Session = None) -> List[StrategyTemplateResponse]:
        """获取所有策略模板"""
        if db is None:
            db = next(get_db())
        
        templates = db.query(StrategyTemplate).filter(
            StrategyTemplate.is_active == True
        ).order_by(desc(StrategyTemplate.created_at)).all()
        
        return [self._db_to_response(template) for template in templates]
    
    def get_templates_by_category(self, category: StrategyTemplateCategory, 
                                 db: Session = None) -> List[StrategyTemplateResponse]:
        """按分类获取策略模板"""
        if db is None:
            db = next(get_db())
        
        templates = db.query(StrategyTemplate).filter(
            StrategyTemplate.category == category.value,
            StrategyTemplate.is_active == True
        ).all()
        
        return [self._db_to_response(template) for template in templates]
    
    def get_template(self, template_id: str, db: Session = None) -> Optional[StrategyTemplateResponse]:
        """获取指定策略模板"""
        if db is None:
            db = next(get_db())
        
        template = db.query(StrategyTemplate).filter(
            StrategyTemplate.id == template_id,
            StrategyTemplate.is_active == True
        ).first()
        
        if not template:
            return None
        
        return self._db_to_response(template)
    
    def apply_template(self, template_id: str, 
                      customizations: TemplateCustomizations = None,
                      db: Session = None) -> StrategyConfigCreate:
        """应用策略模板生成策略配置"""
        template = self.get_template(template_id, db)
        
        if not template:
            raise ValueError(f"策略模板不存在: {template_id}")
        
        # 构建因子配置
        factors = []
        weights = customizations.custom_weights if customizations and customizations.custom_weights else template.default_weights
        
        for factor_config in template.factor_configs:
            factor_id = factor_config.get("factor_id")
            if not factor_id:
                continue
            
            # 获取因子信息
            factor_info = self.factor_engine.get_factor_info(factor_id)
            if not factor_info:
                logger.warning(f"因子不存在: {factor_id}")
                continue
            
            # 获取权重
            weight = weights.get(factor_id, factor_config.get("weight", 0.0))
            
            # 获取参数
            parameters = factor_config.get("parameters", {})
            
            factor = SelectedFactor(
                factor_id=factor_id,
                factor_type="builtin",
                factor_name=factor_info["display_name"],
                parameters=FactorParameters(**parameters) if parameters else FactorParameters(),
                weight=weight,
                is_enabled=True
            )
            factors.append(factor)
        
        # 构建筛选条件
        filters = {}
        if customizations and customizations.additional_filters:
            filters.update(customizations.additional_filters)
        
        # 默认筛选条件
        default_filters = {
            "exclude_st": True,
            "exclude_new_stock": True,
            "min_market_cap": 1000000  # 最小市值100万
        }
        
        for key, value in default_filters.items():
            if key not in filters:
                filters[key] = value
        
        # 最大结果数量
        max_results = 100
        if customizations and customizations.max_results:
            max_results = customizations.max_results
        
        # 创建策略配置
        strategy_config = StrategyConfigCreate(
            name=f"{template.display_name} - 自定义",
            description=f"基于{template.display_name}模板创建的策略配置",
            factors=factors,
            filters=filters,
            max_results=max_results,
            tags=[template.category.lower(), "template"]
        )
        
        return strategy_config
    
    def create_template(self, template_data: Dict[str, Any], db: Session = None) -> StrategyTemplateResponse:
        """创建新的策略模板"""
        if db is None:
            db = next(get_db())
        
        try:
            template_id = str(uuid.uuid4())
            
            db_template = StrategyTemplate(
                id=template_id,
                name=template_data["name"],
                display_name=template_data["display_name"],
                description=template_data.get("description", ""),
                category=template_data["category"],
                factor_configs=template_data["factor_configs"],
                default_weights=template_data["default_weights"],
                applicable_markets=template_data.get("applicable_markets", ["A股"]),
                risk_level=template_data.get("risk_level", "medium"),
                expected_return_range=template_data.get("expected_return_range", ""),
                usage_scenarios=template_data.get("usage_scenarios", ""),
                is_active=True
            )
            
            db.add(db_template)
            db.commit()
            db.refresh(db_template)
            
            logger.info(f"策略模板创建成功: {template_id}")
            
            return self._db_to_response(db_template)
            
        except Exception as e:
            db.rollback()
            logger.error(f"创建策略模板失败: {e}")
            raise
    
    def initialize_default_templates(self, db: Session = None):
        """初始化默认策略模板到数据库"""
        if db is None:
            db = next(get_db())
        
        for template_data in self.default_templates:
            # 检查模板是否已存在
            existing = db.query(StrategyTemplate).filter(
                StrategyTemplate.id == template_data["id"]
            ).first()
            
            if existing:
                logger.info(f"策略模板已存在: {template_data['id']}")
                continue
            
            try:
                # 构建默认权重
                default_weights = {}
                for factor_config in template_data["factor_configs"]:
                    default_weights[factor_config["factor_id"]] = factor_config["weight"]
                
                db_template = StrategyTemplate(
                    id=template_data["id"],
                    name=template_data["name"],
                    display_name=template_data["display_name"],
                    description=template_data["description"],
                    category=template_data["category"].value,
                    factor_configs=template_data["factor_configs"],
                    default_weights=default_weights,
                    applicable_markets=["A股", "港股"],
                    risk_level=template_data["risk_level"].value,
                    expected_return_range=template_data["expected_return_range"],
                    usage_scenarios=template_data["usage_scenarios"],
                    is_active=True
                )
                
                db.add(db_template)
                logger.info(f"初始化策略模板: {template_data['display_name']}")
                
            except Exception as e:
                logger.error(f"初始化模板失败 {template_data['id']}: {e}")
        
        try:
            db.commit()
            logger.info("默认策略模板初始化完成")
        except Exception as e:
            db.rollback()
            logger.error(f"提交默认模板失败: {e}")
            raise
    
    def get_template_recommendations(self, user_profile: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """根据用户画像推荐策略模板"""
        recommendations = []
        
        # 简化的推荐逻辑
        risk_preference = user_profile.get("risk_preference", "medium") if user_profile else "medium"
        investment_horizon = user_profile.get("investment_horizon", "medium") if user_profile else "medium"
        
        for template_data in self.default_templates:
            score = 0
            reasons = []
            
            # 风险偏好匹配
            template_risk = template_data["risk_level"].value
            if risk_preference == "low" and template_risk == "low":
                score += 30
                reasons.append("风险偏好匹配")
            elif risk_preference == "medium" and template_risk in ["low", "medium"]:
                score += 20
                reasons.append("风险偏好适中")
            elif risk_preference == "high" and template_risk in ["medium", "high"]:
                score += 25
                reasons.append("风险偏好匹配")
            
            # 投资期限匹配
            if investment_horizon == "long" and template_data["category"] in [StrategyTemplateCategory.VALUE, StrategyTemplateCategory.QUALITY]:
                score += 20
                reasons.append("适合长期投资")
            elif investment_horizon == "short" and template_data["category"] in [StrategyTemplateCategory.TECHNICAL, StrategyTemplateCategory.MOMENTUM]:
                score += 25
                reasons.append("适合短期操作")
            elif investment_horizon == "medium":
                score += 15
                reasons.append("投资期限适中")
            
            # 策略类型多样性
            if template_data["category"] == StrategyTemplateCategory.GROWTH:
                score += 10
                reasons.append("成长策略受欢迎")
            
            recommendation = {
                "template_id": template_data["id"],
                "template_name": template_data["display_name"],
                "score": score,
                "reasons": reasons,
                "category": template_data["category"].value,
                "risk_level": template_data["risk_level"].value,
                "expected_return": template_data["expected_return_range"]
            }
            
            recommendations.append(recommendation)
        
        # 按分数排序
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        
        return recommendations[:3]  # 返回前3个推荐
    
    def compare_templates(self, template_ids: List[str], db: Session = None) -> Dict[str, Any]:
        """对比多个策略模板"""
        if len(template_ids) < 2:
            raise ValueError("至少需要2个模板进行对比")
        
        templates = []
        for template_id in template_ids:
            template = self.get_template(template_id, db)
            if template:
                templates.append(template)
        
        if len(templates) < 2:
            raise ValueError("找不到足够的有效模板")
        
        comparison = {
            "templates": [],
            "comparison_matrix": self._build_comparison_matrix(templates),
            "recommendations": self._generate_comparison_recommendations(templates)
        }
        
        for template in templates:
            template_info = {
                "id": template.id,
                "name": template.display_name,
                "category": template.category,
                "risk_level": template.risk_level,
                "expected_return": template.expected_return_range,
                "factor_count": len(template.factor_configs),
                "factor_categories": self._get_template_factor_categories(template)
            }
            comparison["templates"].append(template_info)
        
        return comparison
    
    def _build_comparison_matrix(self, templates: List[StrategyTemplateResponse]) -> Dict[str, List[str]]:
        """构建对比矩阵"""
        matrix = {
            "categories": [t.category for t in templates],
            "risk_levels": [t.risk_level for t in templates],
            "factor_counts": [len(t.factor_configs) for t in templates],
            "expected_returns": [t.expected_return_range for t in templates]
        }
        return matrix
    
    def _generate_comparison_recommendations(self, templates: List[StrategyTemplateResponse]) -> List[str]:
        """生成对比建议"""
        recommendations = []
        
        # 分析风险分布
        risk_levels = [t.risk_level for t in templates]
        if len(set(risk_levels)) > 1:
            recommendations.append("模板风险等级不同，可根据风险偏好选择")
        
        # 分析分类分布
        categories = [t.category for t in templates]
        if len(set(categories)) > 1:
            recommendations.append("模板投资风格不同，建议根据市场环境选择")
        
        # 分析因子数量
        factor_counts = [len(t.factor_configs) for t in templates]
        if max(factor_counts) - min(factor_counts) > 2:
            recommendations.append("模板复杂度不同，因子数量多的策略可能更稳定但也更复杂")
        
        return recommendations
    
    def _get_template_factor_categories(self, template: StrategyTemplateResponse) -> Dict[str, int]:
        """获取模板的因子分类统计"""
        categories = {}
        for factor_config in template.factor_configs:
            factor_id = factor_config.get("factor_id")
            if factor_id:
                factor_info = self.factor_engine.get_factor_info(factor_id)
                if factor_info:
                    category = factor_info["category"]
                    categories[category] = categories.get(category, 0) + 1
        return categories
    
    def _db_to_response(self, db_template: StrategyTemplate) -> StrategyTemplateResponse:
        """将数据库对象转换为响应对象"""
        return StrategyTemplateResponse(
            id=db_template.id,
            name=db_template.name,
            display_name=db_template.display_name,
            description=db_template.description or "",
            category=StrategyTemplateCategory(db_template.category),
            factor_configs=db_template.factor_configs or [],
            default_weights=db_template.default_weights or {},
            applicable_markets=db_template.applicable_markets or [],
            risk_level=RiskLevel(db_template.risk_level),
            expected_return_range=db_template.expected_return_range or "",
            usage_scenarios=db_template.usage_scenarios or "",
            is_active=db_template.is_active,
            created_at=db_template.created_at,
            updated_at=db_template.updated_at
        )


# 全局策略模板服务实例
strategy_template_service = StrategyTemplateService()