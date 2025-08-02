"""
策略模板和向导API接口
提供策略模板管理、应用、推荐、配置向导等功能
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Path, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.builtin_factors import (
    StrategyTemplateResponse, TemplateCustomizations,
    StrategyTemplateCategory, RiskLevel, StrategyConfigCreate,
    SelectedFactor, FactorParameters
)
from app.services.strategy_template_service import strategy_template_service
from app.services.strategy_config_service import strategy_config_service
from app.services.builtin_factor_engine import builtin_factor_engine

router = APIRouter(prefix="/strategy-templates", tags=["策略模板和向导"])


# 请求/响应模型
class TemplateApplicationRequest(BaseModel):
    """模板应用请求"""
    template_id: str
    customizations: Optional[TemplateCustomizations] = None
    strategy_name: Optional[str] = None
    created_by: Optional[str] = None


class UserProfileRequest(BaseModel):
    """用户画像请求"""
    risk_preference: str = "medium"  # low, medium, high
    investment_horizon: str = "medium"  # short, medium, long
    experience_level: str = "intermediate"  # beginner, intermediate, advanced
    preferred_categories: Optional[List[str]] = None
    investment_amount: Optional[float] = None


class TemplateComparisonRequest(BaseModel):
    """模板对比请求"""
    template_ids: List[str]


class WizardStepRequest(BaseModel):
    """向导步骤请求"""
    step: int
    user_selections: Dict[str, Any]
    user_profile: Optional[UserProfileRequest] = None


class FactorSelectionRequest(BaseModel):
    """因子选择请求"""
    selected_factor_ids: List[str]
    risk_preference: str = "medium"
    strategy_objective: str = "balanced"  # growth, value, balanced, momentum


@router.get("/", response_model=List[StrategyTemplateResponse])
async def list_strategy_templates(
    category: Optional[str] = Query(None, description="模板分类筛选"),
    db: Session = Depends(get_db)
):
    """
    获取策略模板列表
    
    - **category**: 按分类筛选 (value/growth/momentum/technical/quality)
    """
    try:
        if category:
            try:
                template_category = StrategyTemplateCategory(category)
                templates = strategy_template_service.get_templates_by_category(template_category, db)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的模板分类: {category}")
        else:
            templates = strategy_template_service.get_all_templates(db)
        
        return templates
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模板列表失败: {str(e)}")


@router.get("/{template_id}", response_model=StrategyTemplateResponse)
async def get_strategy_template(
    template_id: str = Path(..., description="模板ID"),
    db: Session = Depends(get_db)
):
    """获取指定策略模板详情"""
    try:
        template = strategy_template_service.get_template(template_id, db)
        
        if not template:
            raise HTTPException(status_code=404, detail=f"策略模板不存在: {template_id}")
        
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模板详情失败: {str(e)}")


@router.post("/{template_id}/apply", response_model=StrategyConfigCreate)
async def apply_strategy_template(
    template_id: str = Path(..., description="模板ID"),
    request: TemplateApplicationRequest = None,
    db: Session = Depends(get_db)
):
    """
    应用策略模板生成策略配置
    
    - **template_id**: 模板ID
    - **customizations**: 定制化选项
    - **strategy_name**: 策略名称
    """
    try:
        if not request:
            request = TemplateApplicationRequest(template_id=template_id)
        
        # 应用模板
        strategy_config = strategy_template_service.apply_template(
            template_id, request.customizations, db
        )
        
        # 如果提供了策略名称，更新名称
        if request.strategy_name:
            strategy_config.name = request.strategy_name
        
        return strategy_config
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"应用模板失败: {str(e)}")


@router.post("/{template_id}/apply-and-save")
async def apply_template_and_save(
    template_id: str = Path(..., description="模板ID"),
    request: TemplateApplicationRequest = None,
    db: Session = Depends(get_db)
):
    """应用模板并直接保存为策略配置"""
    try:
        if not request:
            request = TemplateApplicationRequest(template_id=template_id)
        
        # 应用模板
        strategy_config = strategy_template_service.apply_template(
            template_id, request.customizations, db
        )
        
        # 更新策略名称
        if request.strategy_name:
            strategy_config.name = request.strategy_name
        
        # 保存策略配置
        saved_strategy = strategy_config_service.create_strategy_config(
            strategy_config, request.created_by, db
        )
        
        return {
            "message": "模板应用并保存成功",
            "template_id": template_id,
            "strategy_config": saved_strategy
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"应用并保存模板失败: {str(e)}")


@router.post("/recommendations")
async def get_template_recommendations(
    request: UserProfileRequest
):
    """
    根据用户画像推荐策略模板
    
    - **risk_preference**: 风险偏好 (low/medium/high)
    - **investment_horizon**: 投资期限 (short/medium/long)
    - **experience_level**: 经验水平 (beginner/intermediate/advanced)
    """
    try:
        user_profile = {
            "risk_preference": request.risk_preference,
            "investment_horizon": request.investment_horizon,
            "experience_level": request.experience_level,
            "preferred_categories": request.preferred_categories or [],
            "investment_amount": request.investment_amount
        }
        
        recommendations = strategy_template_service.get_template_recommendations(user_profile)
        
        return {
            "user_profile": user_profile,
            "recommendations": recommendations,
            "recommendation_count": len(recommendations)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取推荐失败: {str(e)}")


@router.post("/compare")
async def compare_strategy_templates(
    request: TemplateComparisonRequest,
    db: Session = Depends(get_db)
):
    """
    对比多个策略模板
    
    - **template_ids**: 模板ID列表
    """
    try:
        if len(request.template_ids) < 2:
            raise HTTPException(status_code=400, detail="至少需要2个模板进行对比")
        
        comparison_result = strategy_template_service.compare_templates(
            request.template_ids, db
        )
        
        return {
            "comparison_result": comparison_result,
            "template_count": len(request.template_ids)
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"模板对比失败: {str(e)}")


# 策略配置向导相关API
@router.post("/wizard/start")
async def start_strategy_wizard(request: UserProfileRequest):
    """
    开始策略配置向导
    
    根据用户画像提供初始建议
    """
    try:
        # 获取推荐模板
        user_profile = request.dict()
        recommendations = strategy_template_service.get_template_recommendations(user_profile)
        
        # 获取可用因子分类
        all_factors = builtin_factor_engine.list_all_factors()
        factor_categories = {}
        
        for factor in all_factors:
            category = factor['category']
            if category not in factor_categories:
                factor_categories[category] = {
                    'name': category,
                    'display_name': {
                        'trend': '趋势类',
                        'momentum': '动量类',
                        'volume': '价量类'
                    }.get(category, category),
                    'factor_count': 0,
                    'sample_factors': []
                }
            
            factor_categories[category]['factor_count'] += 1
            if len(factor_categories[category]['sample_factors']) < 3:
                factor_categories[category]['sample_factors'].append({
                    'factor_id': factor['factor_id'],
                    'display_name': factor['display_name'],
                    'description': factor.get('description', '')
                })
        
        return {
            "wizard_step": 1,
            "user_profile": user_profile,
            "recommended_templates": recommendations[:3],  # 前3个推荐
            "factor_categories": list(factor_categories.values()),
            "next_step_instructions": "请选择您感兴趣的因子分类或直接使用推荐模板",
            "wizard_progress": {
                "current_step": 1,
                "total_steps": 4,
                "completed_steps": 0
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动向导失败: {str(e)}")


@router.post("/wizard/step/{step}")
async def process_wizard_step(
    step: int = Path(..., description="向导步骤"),
    request: WizardStepRequest = None
):
    """
    处理向导步骤
    
    - **step**: 当前步骤 (1-4)
    - **user_selections**: 用户选择
    """
    try:
        if not request:
            raise HTTPException(status_code=400, detail="请提供用户选择数据")
        
        user_selections = request.user_selections
        user_profile = request.user_profile.dict() if request.user_profile else {}
        
        if step == 2:
            # 步骤2: 因子分类选择
            return await _process_step_2_factor_categories(user_selections, user_profile)
        elif step == 3:
            # 步骤3: 具体因子选择和权重配置
            return await _process_step_3_factor_selection(user_selections, user_profile)
        elif step == 4:
            # 步骤4: 策略参数配置和生成
            return await _process_step_4_strategy_generation(user_selections, user_profile)
        else:
            raise HTTPException(status_code=400, detail=f"无效的向导步骤: {step}")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理向导步骤失败: {str(e)}")


async def _process_step_2_factor_categories(user_selections: Dict[str, Any], 
                                          user_profile: Dict[str, Any]) -> Dict[str, Any]:
    """处理步骤2: 因子分类选择"""
    selected_categories = user_selections.get('selected_categories', [])
    selected_template = user_selections.get('selected_template')
    
    if selected_template:
        # 用户选择了推荐模板
        template = strategy_template_service.get_template(selected_template)
        if template:
            return {
                "wizard_step": 4,  # 跳到最后一步
                "selected_template": template,
                "next_step_instructions": "确认模板配置并生成策略",
                "wizard_progress": {
                    "current_step": 4,
                    "total_steps": 4,
                    "completed_steps": 3
                }
            }
    
    # 用户选择了因子分类
    if not selected_categories:
        raise HTTPException(status_code=400, detail="请至少选择一个因子分类")
    
    # 获取选定分类下的因子
    available_factors = []
    all_factors = builtin_factor_engine.list_all_factors()
    
    for factor in all_factors:
        if factor['category'] in selected_categories:
            available_factors.append({
                'factor_id': factor['factor_id'],
                'name': factor['name'],
                'display_name': factor['display_name'],
                'category': factor['category'],
                'description': factor.get('description', ''),
                'default_parameters': factor.get('default_parameters', {}),
                'recommended': _is_factor_recommended(factor, user_profile)
            })
    
    return {
        "wizard_step": 3,
        "selected_categories": selected_categories,
        "available_factors": available_factors,
        "next_step_instructions": "请选择具体的因子并配置权重",
        "wizard_progress": {
            "current_step": 3,
            "total_steps": 4,
            "completed_steps": 2
        }
    }


async def _process_step_3_factor_selection(user_selections: Dict[str, Any],
                                         user_profile: Dict[str, Any]) -> Dict[str, Any]:
    """处理步骤3: 具体因子选择"""
    selected_factors = user_selections.get('selected_factors', [])
    
    if not selected_factors or len(selected_factors) < 2:
        raise HTTPException(status_code=400, detail="请至少选择2个因子")
    
    # 构建因子配置
    factor_configs = []
    for factor_selection in selected_factors:
        factor_id = factor_selection.get('factor_id')
        weight = factor_selection.get('weight', 1.0 / len(selected_factors))
        parameters = factor_selection.get('parameters', {})
        
        factor_info = builtin_factor_engine.get_factor_info(factor_id)
        if factor_info:
            factor_config = SelectedFactor(
                factor_id=factor_id,
                factor_type="builtin",
                factor_name=factor_info['display_name'],
                parameters=FactorParameters(**parameters) if parameters else FactorParameters(),
                weight=weight,
                is_enabled=True
            )
            factor_configs.append(factor_config)
    
    # 生成权重建议
    from app.services.weight_optimization_service import weight_optimization_service
    weight_suggestions = weight_optimization_service.generate_weight_suggestions(factor_configs)
    
    return {
        "wizard_step": 4,
        "selected_factors": factor_configs,
        "weight_suggestions": weight_suggestions,
        "next_step_instructions": "确认因子权重配置并生成策略",
        "wizard_progress": {
            "current_step": 4,
            "total_steps": 4,
            "completed_steps": 3
        }
    }


async def _process_step_4_strategy_generation(user_selections: Dict[str, Any],
                                            user_profile: Dict[str, Any]) -> Dict[str, Any]:
    """处理步骤4: 策略生成"""
    strategy_name = user_selections.get('strategy_name', '我的策略')
    selected_factors = user_selections.get('selected_factors', [])
    selected_template = user_selections.get('selected_template')
    
    try:
        if selected_template:
            # 使用模板生成策略
            strategy_config = strategy_template_service.apply_template(selected_template)
            strategy_config.name = strategy_name
        else:
            # 使用自定义因子生成策略
            if not selected_factors:
                raise HTTPException(status_code=400, detail="请提供因子配置")
            
            # 构建因子配置
            factors = []
            for factor_data in selected_factors:
                if isinstance(factor_data, dict):
                    factor = SelectedFactor(
                        factor_id=factor_data['factor_id'],
                        factor_type="builtin",
                        factor_name=factor_data['factor_name'],
                        parameters=FactorParameters(**factor_data.get('parameters', {})),
                        weight=factor_data.get('weight', 0.0),
                        is_enabled=factor_data.get('is_enabled', True)
                    )
                    factors.append(factor)
            
            # 创建策略配置
            strategy_config = StrategyConfigCreate(
                name=strategy_name,
                description="通过策略向导创建的策略",
                factors=factors,
                filters={
                    "exclude_st": True,
                    "exclude_new_stock": True,
                    "min_market_cap": 1000000
                },
                max_results=100,
                tags=["wizard", "custom"]
            )
        
        # 获取策略预览
        strategy_preview = strategy_config_service.get_strategy_preview(strategy_config.factors)
        
        return {
            "wizard_step": 4,
            "wizard_completed": True,
            "strategy_config": strategy_config,
            "strategy_preview": strategy_preview,
            "success_message": "策略配置生成成功！您可以保存此策略或继续调整。",
            "wizard_progress": {
                "current_step": 4,
                "total_steps": 4,
                "completed_steps": 4
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成策略失败: {str(e)}")


def _is_factor_recommended(factor: Dict[str, Any], user_profile: Dict[str, Any]) -> bool:
    """判断因子是否推荐给用户"""
    risk_preference = user_profile.get('risk_preference', 'medium')
    experience_level = user_profile.get('experience_level', 'intermediate')
    
    # 简化的推荐逻辑
    factor_category = factor['category']
    
    # 风险偏好匹配
    if risk_preference == 'low':
        return factor_category in ['trend', 'volume']
    elif risk_preference == 'high':
        return factor_category in ['momentum']
    else:
        return True  # 中等风险偏好接受所有类型
    
    # 经验水平匹配
    if experience_level == 'beginner':
        # 新手推荐简单因子
        simple_factors = ['sma_20', 'sma_50', 'rsi_14', 'volume_ratio_20']
        return factor['factor_id'] in simple_factors
    
    return True


@router.post("/wizard/factor-suggestions")
async def get_factor_suggestions(request: FactorSelectionRequest):
    """
    根据已选因子获取补充建议
    
    - **selected_factor_ids**: 已选因子ID列表
    - **risk_preference**: 风险偏好
    - **strategy_objective**: 策略目标
    """
    try:
        # 分析已选因子的特征
        selected_factors = []
        selected_categories = set()
        
        for factor_id in request.selected_factor_ids:
            factor_info = builtin_factor_engine.get_factor_info(factor_id)
            if factor_info:
                selected_factors.append(factor_info)
                selected_categories.add(factor_info['category'])
        
        # 获取建议因子
        all_factors = builtin_factor_engine.list_all_factors()
        suggestions = []
        
        for factor in all_factors:
            if factor['factor_id'] not in request.selected_factor_ids:
                # 计算推荐分数
                score = 0
                reasons = []
                
                # 分类多样性
                if factor['category'] not in selected_categories:
                    score += 30
                    reasons.append("增加策略多样性")
                
                # 风险匹配
                if _factor_matches_risk_preference(factor, request.risk_preference):
                    score += 20
                    reasons.append("匹配风险偏好")
                
                # 策略目标匹配
                if _factor_matches_objective(factor, request.strategy_objective):
                    score += 25
                    reasons.append("匹配策略目标")
                
                # 与已选因子的互补性
                complementary_score = _calculate_complementary_score(factor, selected_factors)
                score += complementary_score
                if complementary_score > 0:
                    reasons.append("与已选因子互补")
                
                if score > 20:  # 只推荐分数较高的因子
                    suggestions.append({
                        'factor_id': factor['factor_id'],
                        'factor_name': factor['display_name'],
                        'category': factor['category'],
                        'score': score,
                        'reasons': reasons,
                        'description': factor.get('description', '')
                    })
        
        # 按分数排序
        suggestions.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            "suggestions": suggestions[:5],  # 返回前5个建议
            "analysis": {
                "selected_factor_count": len(request.selected_factor_ids),
                "selected_categories": list(selected_categories),
                "diversity_score": len(selected_categories) / 3.0,  # 假设有3个主要分类
                "recommendations": _generate_selection_recommendations(selected_categories, request)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取因子建议失败: {str(e)}")


def _factor_matches_risk_preference(factor: Dict[str, Any], risk_preference: str) -> bool:
    """判断因子是否匹配风险偏好"""
    factor_category = factor['category']
    
    risk_mappings = {
        'low': ['trend', 'volume'],
        'medium': ['trend', 'momentum', 'volume'],
        'high': ['momentum', 'volume']
    }
    
    return factor_category in risk_mappings.get(risk_preference, [])


def _factor_matches_objective(factor: Dict[str, Any], objective: str) -> bool:
    """判断因子是否匹配策略目标"""
    factor_category = factor['category']
    
    objective_mappings = {
        'growth': ['momentum'],
        'value': ['trend', 'volume'],
        'balanced': ['trend', 'momentum', 'volume'],
        'momentum': ['momentum']
    }
    
    return factor_category in objective_mappings.get(objective, [])


def _calculate_complementary_score(factor: Dict[str, Any], selected_factors: List[Dict[str, Any]]) -> int:
    """计算因子与已选因子的互补性分数"""
    # 简化的互补性计算
    factor_category = factor['category']
    selected_categories = [f['category'] for f in selected_factors]
    
    # 如果是不同分类，增加互补性分数
    if factor_category not in selected_categories:
        return 15
    
    # 同分类但可能有不同特征的因子
    return 5


def _generate_selection_recommendations(selected_categories: set, request: FactorSelectionRequest) -> List[str]:
    """生成因子选择建议"""
    recommendations = []
    
    all_categories = {'trend', 'momentum', 'volume'}
    missing_categories = all_categories - selected_categories
    
    if len(selected_categories) < 2:
        recommendations.append("建议选择至少2个不同分类的因子以提高策略稳定性")
    
    if missing_categories:
        missing_names = {
            'trend': '趋势类',
            'momentum': '动量类',
            'volume': '价量类'
        }
        missing_display = [missing_names.get(cat, cat) for cat in missing_categories]
        recommendations.append(f"考虑添加{', '.join(missing_display)}因子以增加策略多样性")
    
    if len(request.selected_factor_ids) > 6:
        recommendations.append("因子数量较多，可能增加策略复杂度，建议精简到3-5个核心因子")
    
    return recommendations