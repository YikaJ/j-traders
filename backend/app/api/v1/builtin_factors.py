"""
内置因子库API接口
提供内置因子的查询、预览、计算等功能
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Path, Depends
from pydantic import BaseModel

from app.schemas.builtin_factors import (
    BuiltinFactorResponse, FactorPreviewRequest, FactorPreviewResult,
    ValidationResult, FactorParameters, CalculationMethod, FactorCategory
)
from app.services.builtin_factor_engine import builtin_factor_engine, BuiltinFactorEngine

router = APIRouter(prefix="/builtin-factors", tags=["内置因子库"])


def get_builtin_factor_engine() -> BuiltinFactorEngine:
    """获取内置因子引擎实例"""
    return builtin_factor_engine


# 请求/响应模型
class FactorListQuery(BaseModel):
    """因子列表查询参数"""
    category: Optional[str] = None
    search: Optional[str] = None


class FactorCalculationRequest(BaseModel):
    """因子计算请求"""
    factor_id: str
    parameters: Optional[FactorParameters] = None
    sample_data: List[Dict[str, Any]]  # 样本数据


class FactorCalculationResponse(BaseModel):
    """因子计算响应"""
    factor_id: str
    success: bool
    result_data: Optional[List[Dict[str, Any]]] = None
    statistics: Optional[Dict[str, float]] = None
    error_message: Optional[str] = None
    execution_time: float


class BatchCalculationRequest(BaseModel):
    """批量因子计算请求"""
    factor_configs: List[Dict[str, Any]]
    sample_data: List[Dict[str, Any]]


class BatchCalculationResponse(BaseModel):
    """批量因子计算响应"""
    success_count: int
    failed_count: int
    results: Dict[str, FactorCalculationResponse]
    total_execution_time: float


class FactorFormulaUpdateRequest(BaseModel):
    """因子公式更新请求"""
    formula: str
    description: Optional[str] = None
    
class FactorFormulaResponse(BaseModel):
    """因子公式响应"""
    factor_id: str
    formula: str
    description: str
    updated_at: str
    success: bool


@router.get("/", response_model=List[BuiltinFactorResponse])
async def list_builtin_factors(
    category: Optional[str] = Query(None, description="因子分类筛选"),
    search: Optional[str] = Query(None, description="搜索关键词")
):
    """
    获取内置因子列表
    
    - **category**: 按分类筛选 (trend/momentum/volume/volatility/valuation)
    - **search**: 按名称或描述搜索
    """
    try:
        if category:
            # 验证分类有效性
            try:
                factor_category = FactorCategory(category)
                factors = builtin_factor_engine.list_factors_by_category(factor_category)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的因子分类: {category}")
        else:
            factors = builtin_factor_engine.list_all_factors()
        
        # 应用搜索过滤
        if search:
            search_lower = search.lower()
            factors = [
                factor for factor in factors
                if search_lower in factor['name'].lower() 
                or search_lower in factor['display_name'].lower()
                or search_lower in factor.get('description', '').lower()
            ]
        
        # 转换为响应格式
        response_factors = []
        for factor in factors:
            # 处理默认参数
            default_params = factor.get('default_parameters', {})
            factor_params = FactorParameters()
            if 'period' in default_params:
                period_dict = default_params.get('period')
                if isinstance(period_dict, dict) and 'default' in period_dict:
                    factor_params.period = period_dict['default']
            if 'fast_period' in default_params:
                fast_period_dict = default_params.get('fast_period')
                if isinstance(fast_period_dict, dict) and 'default' in fast_period_dict:
                    factor_params.fast_period = fast_period_dict['default']
            if 'slow_period' in default_params:
                slow_period_dict = default_params.get('slow_period')
                if isinstance(slow_period_dict, dict) and 'default' in slow_period_dict:
                    factor_params.slow_period = slow_period_dict['default']
            if 'signal_period' in default_params:
                signal_period_dict = default_params.get('signal_period')
                if isinstance(signal_period_dict, dict) and 'default' in signal_period_dict:
                    factor_params.signal_period = signal_period_dict['default']
            if 'multiplier' in default_params:
                multiplier_dict = default_params.get('multiplier')
                if isinstance(multiplier_dict, dict) and 'default' in multiplier_dict:
                    factor_params.multiplier = multiplier_dict['default']
            
            # 创建响应对象
            response_factor = BuiltinFactorResponse(
                id=factor['factor_id'],
                name=factor['name'],
                display_name=factor['display_name'],
                description=factor.get('description', ''),
                category=FactorCategory(factor['category']),
                calculation_method=CalculationMethod.CUSTOM,  # 使用枚举值
                formula=factor.get('formula'),
                default_parameters=factor_params,
                parameter_schema=factor.get('parameter_schema', {}),
                input_fields=factor.get('input_fields', []),
                output_type="single",
                is_active=True,
                created_at=datetime.now(),  # 使用当前时间
                updated_at=datetime.now()
            )
            response_factors.append(response_factor)
        
        return response_factors
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取因子列表失败: {str(e)}")


@router.get("/categories")
async def get_factor_categories():
    """获取所有因子分类及统计信息"""
    try:
        categories = {}
        all_factors = builtin_factor_engine.list_all_factors()
        
        # 统计每个分类的因子数量
        for factor in all_factors:
            category = factor['category']
            if category not in categories:
                categories[category] = {
                    'name': category,
                    'display_name': {
                        'trend': '趋势类',
                        'momentum': '动量类', 
                        'volume': '价量类',
                        'volatility': '波动率类',
                        'valuation': '估值类'
                    }.get(category, category),
                    'count': 0,
                    'factors': []
                }
            
            categories[category]['count'] += 1
            categories[category]['factors'].append({
                'factor_id': factor['factor_id'],
                'name': factor['name'],
                'display_name': factor['display_name']
            })
        
        return list(categories.values())
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取因子分类失败: {str(e)}")


@router.get("/{factor_id}", response_model=BuiltinFactorResponse)
async def get_factor_detail(
    factor_id: str = Path(..., description="因子ID")
):
    """获取指定因子的详细信息"""
    try:
        factor_info = builtin_factor_engine.get_factor_info(factor_id)
        
        if not factor_info:
            raise HTTPException(status_code=404, detail=f"因子不存在: {factor_id}")
        
        # 处理默认参数
        default_params = factor_info.get('default_parameters', {})
        factor_params = FactorParameters()
        if 'period' in default_params:
            period_dict = default_params.get('period')
            if isinstance(period_dict, dict) and 'default' in period_dict:
                factor_params.period = period_dict['default']
        if 'fast_period' in default_params:
            fast_period_dict = default_params.get('fast_period')
            if isinstance(fast_period_dict, dict) and 'default' in fast_period_dict:
                factor_params.fast_period = fast_period_dict['default']
        if 'slow_period' in default_params:
            slow_period_dict = default_params.get('slow_period')
            if isinstance(slow_period_dict, dict) and 'default' in slow_period_dict:
                factor_params.slow_period = slow_period_dict['default']
        if 'signal_period' in default_params:
            signal_period_dict = default_params.get('signal_period')
            if isinstance(signal_period_dict, dict) and 'default' in signal_period_dict:
                factor_params.signal_period = signal_period_dict['default']
        if 'multiplier' in default_params:
            multiplier_dict = default_params.get('multiplier')
            if isinstance(multiplier_dict, dict) and 'default' in multiplier_dict:
                factor_params.multiplier = multiplier_dict['default']
        
        return BuiltinFactorResponse(
            id=factor_info['factor_id'],
            name=factor_info['name'],
            display_name=factor_info['display_name'],
            description=factor_info.get('description', ''),
            category=FactorCategory(factor_info['category']),
            calculation_method=CalculationMethod.CUSTOM,  # 使用枚举值
            formula=factor_info.get('formula'),
            default_parameters=factor_params,
            parameter_schema=factor_info.get('parameter_schema', {}),
            input_fields=factor_info.get('input_fields', []),
            output_type="single",
            is_active=True,
            created_at=datetime.now(),  # 使用当前时间
            updated_at=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取因子详情失败: {str(e)}")


@router.post("/{factor_id}/preview", response_model=FactorPreviewResult)
async def preview_factor(
    preview_request: FactorPreviewRequest = None,
    factor_id: str = Path(..., description="因子ID")
):
    """
    预览因子计算结果
    
    需要提供样本数据来计算因子预览
    """
    try:
        if not preview_request:
            preview_request = FactorPreviewRequest(factor_id=factor_id)
        
        # 这里应该使用真实的样本数据，目前返回模拟数据
        # 在实际实现中，需要从数据库获取样本股票数据
        
        factor_info = builtin_factor_engine.get_factor_info(factor_id)
        if not factor_info:
            raise HTTPException(status_code=404, detail=f"因子不存在: {factor_id}")
        
        # 模拟预览数据
        preview_result = FactorPreviewResult(
            factor_id=factor_id,
            parameters=preview_request.parameters,
            sample_data=[
                {"date": "2024-01-01", "value": 1.2},
                {"date": "2024-01-02", "value": 1.3},
                {"date": "2024-01-03", "value": 1.1},
            ],
            statistics={
                "mean": 1.2,
                "std": 0.1,
                "min": 1.1,
                "max": 1.3,
                "count": 3
            },
            chart_data=[
                {"x": "2024-01-01", "y": 1.2},
                {"x": "2024-01-02", "y": 1.3},
                {"x": "2024-01-03", "y": 1.1},
            ],
            calculation_time=0.05
        )
        
        return preview_result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"因子预览失败: {str(e)}")


@router.post("/{factor_id}/validate", response_model=ValidationResult)
async def validate_factor_parameters(
    parameters: FactorParameters,
    factor_id: str = Path(..., description="因子ID")
):
    """验证因子参数配置"""
    try:
        factor_info = builtin_factor_engine.get_factor_info(factor_id)
        if not factor_info:
            raise HTTPException(status_code=404, detail=f"因子不存在: {factor_id}")
        
        # 验证参数
        try:
            # 这里应该使用具体的参数验证逻辑
            # 目前返回基础验证结果
            validation_result = ValidationResult(
                is_valid=True,
                error_message=None,
                warnings=[]
            )
            
            # 检查必要参数
            param_dict = parameters.dict(exclude_unset=True)
            default_params = factor_info.get('default_parameters', {})
            
            warnings = []
            for param_name, param_schema in default_params.items():
                if param_name in param_dict:
                    value = param_dict[param_name]
                    
                    # 类型检查
                    if param_schema.get('type') == 'integer' and not isinstance(value, int):
                        validation_result.is_valid = False
                        validation_result.error_message = f"参数 {param_name} 必须是整数"
                        break
                    
                    # 范围检查
                    if 'minimum' in param_schema and value < param_schema['minimum']:
                        validation_result.is_valid = False
                        validation_result.error_message = f"参数 {param_name} 不能小于 {param_schema['minimum']}"
                        break
                    
                    if 'maximum' in param_schema and value > param_schema['maximum']:
                        validation_result.is_valid = False
                        validation_result.error_message = f"参数 {param_name} 不能大于 {param_schema['maximum']}"
                        break
                else:
                    if 'default' in param_schema:
                        warnings.append(f"参数 {param_name} 未设置，将使用默认值 {param_schema['default']}")
            
            validation_result.warnings = warnings
            
            return validation_result
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                error_message=str(e),
                warnings=[]
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"参数验证失败: {str(e)}")


@router.post("/calculate", response_model=FactorCalculationResponse)
async def calculate_factor(request: FactorCalculationRequest):
    """计算单个因子"""
    try:
        factor_info = builtin_factor_engine.get_factor_info(request.factor_id)
        if not factor_info:
            raise HTTPException(status_code=404, detail=f"因子不存在: {request.factor_id}")
        
        # 这里应该将sample_data转换为pandas DataFrame
        # 并调用因子计算引擎进行计算
        # 目前返回模拟结果
        
        import time
        start_time = time.time()
        
        # 模拟计算过程
        time.sleep(0.1)  # 模拟计算耗时
        
        execution_time = time.time() - start_time
        
        response = FactorCalculationResponse(
            factor_id=request.factor_id,
            success=True,
            result_data=[
                {"symbol": "000001.SZ", "value": 1.2, "rank": 1},
                {"symbol": "000002.SZ", "value": 1.1, "rank": 2},
                {"symbol": "600000.SH", "value": 1.0, "rank": 3},
            ],
            statistics={
                "mean": 1.1,
                "std": 0.1,
                "min": 1.0,
                "max": 1.2,
                "count": 3
            },
            execution_time=execution_time
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        return FactorCalculationResponse(
            factor_id=request.factor_id,
            success=False,
            error_message=str(e),
            execution_time=0.0
        )


@router.post("/batch-calculate", response_model=BatchCalculationResponse)
async def batch_calculate_factors(request: BatchCalculationRequest):
    """批量计算多个因子"""
    try:
        import time
        start_time = time.time()
        
        results = {}
        success_count = 0
        failed_count = 0
        
        for factor_config in request.factor_configs:
            factor_id = factor_config.get('factor_id')
            if not factor_id:
                failed_count += 1
                continue
            
            # 创建单个计算请求
            single_request = FactorCalculationRequest(
                factor_id=factor_id,
                parameters=factor_config.get('parameters'),
                sample_data=request.sample_data
            )
            
            try:
                # 计算单个因子
                result = await calculate_factor(single_request)
                results[factor_id] = result
                
                if result.success:
                    success_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                failed_count += 1
                results[factor_id] = FactorCalculationResponse(
                    factor_id=factor_id,
                    success=False,
                    error_message=str(e),
                    execution_time=0.0
                )
        
        total_execution_time = time.time() - start_time
        
        return BatchCalculationResponse(
            success_count=success_count,
            failed_count=failed_count,
            results=results,
            total_execution_time=total_execution_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量计算失败: {str(e)}")


@router.get("/engine/status")
async def get_engine_status():
    """获取因子计算引擎状态"""
    try:
        status = builtin_factor_engine.get_engine_status()
        return {
            "engine_status": "running",
            "registered_factors": status['registered_factors'],
            "factors_by_category": status['factors_by_category'],
            "cache_enabled": status['cache_enabled'],
            "cached_results": status['cached_results'],
            "cache_expiry_seconds": status['cache_expiry_seconds'],
            "memory_usage": "N/A",  # 可以添加内存使用统计
            "last_updated": "2024-01-01T00:00:00Z"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取引擎状态失败: {str(e)}")


@router.post("/engine/clear-cache")
async def clear_engine_cache():
    """清除因子计算缓存"""
    try:
        builtin_factor_engine.clear_cache()
        return {"message": "缓存已清除", "timestamp": "2024-01-01T00:00:00Z"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清除缓存失败: {str(e)}")


@router.put("/builtin-factors/{factor_id}/formula")
async def update_factor_formula(
    factor_id: str,
    request: FactorFormulaUpdateRequest,
    engine: BuiltinFactorEngine = Depends(get_builtin_factor_engine)
):
    """
    更新因子计算公式
    """
    try:
        # 验证因子是否存在
        factor_info = engine.get_factor_info(factor_id)
        if not factor_info:
            raise HTTPException(status_code=404, detail=f"因子 {factor_id} 不存在")
        
        # 更新公式
        success = engine.update_factor_formula(factor_id, request.formula, request.description)
        
        if not success:
            raise HTTPException(status_code=400, detail="公式更新失败")
        
        # 获取更新后的因子信息
        updated_info = engine.get_factor_info(factor_id)
        
        return FactorFormulaResponse(
            factor_id=factor_id,
            formula=updated_info.get('formula', ''),
            description=updated_info.get('description', ''),
            updated_at=datetime.utcnow().isoformat(),
            success=True
        )
        
    except Exception as e:
        logger.error(f"更新因子公式失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新因子公式失败: {str(e)}")

@router.post("/builtin-factors/{factor_id}/validate-formula")
async def validate_factor_formula(
    factor_id: str,
    request: FactorFormulaUpdateRequest,
    engine: BuiltinFactorEngine = Depends(get_builtin_factor_engine)
):
    """
    验证因子公式的有效性
    """
    try:
        # 验证因子是否存在
        factor_info = engine.get_factor_info(factor_id)
        if not factor_info:
            raise HTTPException(status_code=404, detail=f"因子 {factor_id} 不存在")
        
        # 验证公式语法
        validation_result = engine.validate_factor_formula(factor_id, request.formula)
        
        return {
            "factor_id": factor_id,
            "formula": request.formula,
            "is_valid": validation_result.get('is_valid', False),
            "error_message": validation_result.get('error_message'),
            "warnings": validation_result.get('warnings', [])
        }
        
    except Exception as e:
        logger.error(f"验证因子公式失败: {e}")
        raise HTTPException(status_code=500, detail=f"验证因子公式失败: {str(e)}")

@router.get("/builtin-factors/{factor_id}/formula-history")
async def get_factor_formula_history(
    factor_id: str,
    engine: BuiltinFactorEngine = Depends(get_builtin_factor_engine)
):
    """
    获取因子公式历史记录
    """
    try:
        # 验证因子是否存在
        factor_info = engine.get_factor_info(factor_id)
        if not factor_info:
            raise HTTPException(status_code=404, detail=f"因子 {factor_id} 不存在")
        
        # 获取历史记录
        history = engine.get_factor_formula_history(factor_id)
        
        return {
            "factor_id": factor_id,
            "history": history
        }
        
    except Exception as e:
        logger.error(f"获取因子公式历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取因子公式历史失败: {str(e)}")

@router.post("/builtin-factors/{factor_id}/reset-formula")
async def reset_factor_formula(
    factor_id: str,
    engine: BuiltinFactorEngine = Depends(get_builtin_factor_engine)
):
    """
    重置因子公式到原始状态
    """
    try:
        # 验证因子是否存在
        factor_info = engine.get_factor_info(factor_id)
        if not factor_info:
            raise HTTPException(status_code=404, detail=f"因子 {factor_id} 不存在")
        
        # 重置公式
        success = engine.reset_factor_formula(factor_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="公式重置失败")
        
        return {
            "success": True,
            "message": f"因子 {factor_id} 的公式已重置到原始状态"
        }
        
    except Exception as e:
        logger.error(f"重置因子公式失败: {e}")
        raise HTTPException(status_code=500, detail=f"重置因子公式失败: {str(e)}")