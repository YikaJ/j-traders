"""
内置因子计算引擎
统一管理和调度所有内置因子的计算
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from .builtin_factor_service import FactorCategory
from .builtin_factor_service import TrendFactorService
from .momentum_factor_service import MomentumFactorService
from .volume_factor_service import VolumeFactorService
from .alpha101_factor_service import alpha101_factor_service
from .parametric_factor_service import parametric_factor_service
from .alpha101_extended import alpha101_extended_service
from .alpha101_more_factors import alpha101_more_factors_service
from .alpha101_phase2 import alpha101_phase2_service
from .alpha101_phase3 import alpha101_phase3_service
from .alpha101_phase4 import alpha101_phase4_service

logger = logging.getLogger(__name__)


class BuiltinFactorEngine:
    """
    内置因子计算引擎
    统一管理所有类别的内置因子计算
    """
    
    def __init__(self):
        # 初始化各类因子服务
        self.trend_service = TrendFactorService()
        self.momentum_service = MomentumFactorService()
        self.volume_service = VolumeFactorService()
        self.alpha101_service = alpha101_factor_service
        self.parametric_service = parametric_factor_service
        # 添加扩展的Alpha101服务
        self.alpha101_extended_service = alpha101_extended_service
        self.alpha101_more_factors_service = alpha101_more_factors_service
        self.alpha101_phase2_service = alpha101_phase2_service
        self.alpha101_phase3_service = alpha101_phase3_service
        self.alpha101_phase4_service = alpha101_phase4_service
        
        # 创建统一的因子注册表
        self.factor_registry = {}
        self._build_unified_registry()
        
        # 缓存设置
        self.cache_enabled = True
        self.calculation_cache = {}
        self.cache_expiry = 3600  # 1小时过期
    
    def _build_unified_registry(self):
        """构建统一的因子注册表"""
        # 注册趋势类因子
        for factor in self.trend_service.get_available_factors():
            self.factor_registry[factor['factor_id']] = {
                **factor,
                'service': self.trend_service,
                'category': FactorCategory.TREND
            }
        
        # 注册动量类因子
        for factor in self.momentum_service.get_available_factors():
            self.factor_registry[factor['factor_id']] = {
                **factor,
                'service': self.momentum_service,
                'category': FactorCategory.MOMENTUM
            }
        
        # 注册价量类因子
        for factor in self.volume_service.get_available_factors():
            self.factor_registry[factor['factor_id']] = {
                **factor,
                'service': self.volume_service,
                'category': FactorCategory.VOLUME
            }
        
        # 注册Alpha101因子
        for factor in self.alpha101_service.get_available_factors():
            self.factor_registry[factor['factor_id']] = {
                **factor,
                'service': self.alpha101_service,
                'category': 'alpha101'
            }
        
        # 注册参数化因子
        for factor in self.parametric_service.get_available_factors():
            self.factor_registry[factor['factor_id']] = {
                **factor,
                'service': self.parametric_service,
                'category': factor['category']
            }
        
        # 注册扩展的Alpha101因子
        for factor in self.alpha101_extended_service.get_available_factors():
            self.factor_registry[factor['factor_id']] = {
                **factor,
                'service': self.alpha101_extended_service,
                'category': 'alpha101_extended'
            }
        
        # 注册更多Alpha101因子
        for factor in self.alpha101_more_factors_service.get_available_factors():
            self.factor_registry[factor['factor_id']] = {
                **factor,
                'service': self.alpha101_more_factors_service,
                'category': 'alpha101_more_factors'
            }
        
        # 注册Alpha101 Phase2因子 (Alpha031-050)
        for factor in self.alpha101_phase2_service.get_available_factors():
            self.factor_registry[factor['factor_id']] = {
                **factor,
                'service': self.alpha101_phase2_service,
                'category': 'alpha101_phase2'
            }
        
        # 注册Alpha101 Phase3因子 (Alpha041-080，适合A股)
        for factor in self.alpha101_phase3_service.get_available_factors():
            self.factor_registry[factor['factor_id']] = {
                **factor,
                'service': self.alpha101_phase3_service,
                'category': 'alpha101_phase3'
            }
        
        # 注册Alpha101 Phase4因子 (Alpha061-101，适合A股)
        for factor in self.alpha101_phase4_service.get_available_factors():
            self.factor_registry[factor['factor_id']] = {
                **factor,
                'service': self.alpha101_phase4_service,
                'category': 'alpha101_phase4'
            }
        
        logger.info(f"已注册 {len(self.factor_registry)} 个内置因子")
    
    def list_all_factors(self) -> List[Dict[str, Any]]:
        """获取所有可用因子列表"""
        factors = []
        
        for factor_id, factor_info in self.factor_registry.items():
            # 处理类别，可能是枚举或字符串
            category = factor_info['category']
            if hasattr(category, 'value'):
                category_value = category.value
            else:
                category_value = category
            
            factors.append({
                'factor_id': factor_id,
                'name': factor_info['name'],
                'display_name': factor_info['display_name'],
                'category': category_value,
                'description': factor_info['description'],
                'input_fields': factor_info['input_fields'],
                'default_parameters': factor_info['default_parameters']
            })
        
        return factors
    
    def list_factors_by_category(self, category: Union[str, FactorCategory]) -> List[Dict[str, Any]]:
        """按分类获取因子列表"""
        if isinstance(category, str):
            category = FactorCategory(category)
        
        return [factor for factor in self.list_all_factors() 
                if factor['category'] == category.value]
    
    def get_factor_info(self, factor_id: str) -> Optional[Dict[str, Any]]:
        """获取指定因子的详细信息"""
        if factor_id not in self.factor_registry:
            return None
        
        factor_info = self.factor_registry[factor_id]
        service = factor_info['service']
        
        return service.get_factor_info(factor_id)
    
    def calculate_single_factor(self, factor_id: str, data: pd.DataFrame, 
                               parameters: Dict[str, Any] = None) -> Union[pd.Series, pd.DataFrame]:
        """计算单个因子"""
        if factor_id not in self.factor_registry:
            raise ValueError(f"未找到因子: {factor_id}")
        
        # 检查缓存
        cache_key = self._get_cache_key(factor_id, data, parameters)
        if self.cache_enabled and cache_key in self.calculation_cache:
            cache_entry = self.calculation_cache[cache_key]
            if time.time() - cache_entry['timestamp'] < self.cache_expiry:
                logger.debug(f"使用缓存结果: {factor_id}")
                return cache_entry['result']
        
        # 获取对应的服务并计算
        factor_info = self.factor_registry[factor_id]
        service = factor_info['service']
        
        start_time = time.time()
        try:
            result = service.calculate_single_factor(factor_id, data, parameters)
            
            # 缓存结果
            if self.cache_enabled:
                self.calculation_cache[cache_key] = {
                    'result': result,
                    'timestamp': time.time()
                }
            
            execution_time = time.time() - start_time
            logger.debug(f"因子 {factor_id} 计算完成，耗时: {execution_time:.3f}秒")
            
            return result
            
        except Exception as e:
            logger.error(f"计算因子 {factor_id} 时出错: {e}")
            raise
    
    def calculate_multiple_factors(self, factor_configs: List[Dict[str, Any]], 
                                  data: pd.DataFrame, 
                                  parallel: bool = True) -> Dict[str, Union[pd.Series, pd.DataFrame]]:
        """批量计算多个因子"""
        results = {}
        
        if not parallel or len(factor_configs) == 1:
            # 串行计算
            for config in factor_configs:
                factor_id = config.get('factor_id')
                parameters = config.get('parameters', {})
                
                try:
                    result = self.calculate_single_factor(factor_id, data, parameters)
                    results[factor_id] = result
                except Exception as e:
                    logger.error(f"计算因子 {factor_id} 失败: {e}")
                    results[factor_id] = None
        else:
            # 并行计算
            results = self._calculate_factors_parallel(factor_configs, data)
        
        return results
    
    def _calculate_factors_parallel(self, factor_configs: List[Dict[str, Any]], 
                                   data: pd.DataFrame) -> Dict[str, Union[pd.Series, pd.DataFrame]]:
        """并行计算因子"""
        results = {}
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            # 提交所有计算任务
            future_to_factor = {}
            for config in factor_configs:
                factor_id = config.get('factor_id')
                parameters = config.get('parameters', {})
                
                future = executor.submit(self.calculate_single_factor, factor_id, data, parameters)
                future_to_factor[future] = factor_id
            
            # 收集结果
            for future in as_completed(future_to_factor):
                factor_id = future_to_factor[future]
                
                try:
                    result = future.result()
                    results[factor_id] = result
                except Exception as e:
                    logger.error(f"并行计算因子 {factor_id} 失败: {e}")
                    results[factor_id] = None
        
        return results
    
    def calculate_strategy_factors(self, strategy_config: Dict[str, Any], 
                                  data: pd.DataFrame) -> Dict[str, Any]:
        """计算策略所需的所有因子"""
        factor_configs = strategy_config.get('factors', [])
        
        if not factor_configs:
            raise ValueError("策略配置中没有因子")
        
        start_time = time.time()
        
        # 批量计算因子
        factor_results = self.calculate_multiple_factors(factor_configs, data, parallel=True)
        
        # 计算加权得分
        weighted_scores = self._calculate_weighted_scores(factor_results, factor_configs)
        
        execution_time = time.time() - start_time
        
        return {
            'factor_results': factor_results,
            'weighted_scores': weighted_scores,
            'execution_time': execution_time,
            'calculated_factors': len([r for r in factor_results.values() if r is not None]),
            'failed_factors': len([r for r in factor_results.values() if r is None])
        }
    
    def _calculate_weighted_scores(self, factor_results: Dict[str, Union[pd.Series, pd.DataFrame]], 
                                  factor_configs: List[Dict[str, Any]]) -> pd.Series:
        """计算加权综合得分"""
        # 创建权重映射
        weight_map = {}
        for config in factor_configs:
            factor_id = config.get('factor_id')
            weight = config.get('weight', 0.0)
            weight_map[factor_id] = weight
        
        # 存储标准化后的因子值
        normalized_factors = {}
        
        for factor_id, result in factor_results.items():
            if result is None:
                continue
            
            weight = weight_map.get(factor_id, 0.0)
            if weight == 0.0:
                continue
            
            # 对于多列结果，取主要列
            if isinstance(result, pd.DataFrame):
                if 'value' in result.columns:
                    factor_values = result['value']
                elif 'position' in result.columns:  # 布林带位置
                    factor_values = result['position']
                elif 'macd' in result.columns:  # MACD
                    factor_values = result['macd']
                elif 'k' in result.columns:  # KDJ
                    factor_values = result['k']
                else:
                    # 取第一列
                    factor_values = result.iloc[:, 0]
            else:
                factor_values = result
            
            # 标准化因子值（0-1范围）
            normalized_values = self._normalize_factor_values(factor_values)
            normalized_factors[factor_id] = normalized_values * weight
        
        # 计算加权总分
        if not normalized_factors:
            return pd.Series(0.0, index=factor_results[list(factor_results.keys())[0]].index)
        
        weighted_scores = sum(normalized_factors.values())
        
        return weighted_scores
    
    def _normalize_factor_values(self, values: pd.Series) -> pd.Series:
        """标准化因子值到0-1范围"""
        if values.empty:
            return values
        
        # 去除无穷大和NaN值
        clean_values = values.replace([np.inf, -np.inf], np.nan).dropna()
        
        if clean_values.empty:
            return pd.Series(0.5, index=values.index)  # 返回中性值
        
        # 使用分位数标准化，避免极值影响
        q1 = clean_values.quantile(0.25)
        q3 = clean_values.quantile(0.75)
        
        if q3 == q1:
            return pd.Series(0.5, index=values.index)
        
        # 线性映射到0-1范围
        normalized = (values - q1) / (q3 - q1)
        
        # 限制在0-1范围内
        normalized = normalized.clip(0, 1)
        
        # 填充NaN值为中性值0.5
        normalized = normalized.fillna(0.5)
        
        return normalized
    
    def validate_factor_configs(self, factor_configs: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """验证因子配置"""
        errors = []
        warnings = []
        
        total_weight = 0.0
        factor_ids = []
        
        for i, config in enumerate(factor_configs):
            factor_id = config.get('factor_id')
            weight = config.get('weight', 0.0)
            parameters = config.get('parameters', {})
            
            # 检查因子ID
            if not factor_id:
                errors.append(f"配置 {i+1}: 缺少因子ID")
                continue
            
            if factor_id in factor_ids:
                warnings.append(f"因子 {factor_id} 重复配置")
            factor_ids.append(factor_id)
            
            # 检查因子是否存在
            if factor_id not in self.factor_registry:
                errors.append(f"因子 {factor_id} 不存在")
                continue
            
            # 检查权重
            if not isinstance(weight, (int, float)) or weight < 0:
                errors.append(f"因子 {factor_id}: 权重必须为非负数")
            else:
                total_weight += weight
            
            # 验证参数
            try:
                factor_info = self.factor_registry[factor_id]
                service = factor_info['service']
                if hasattr(service, 'validate_parameters'):
                    service.validate_parameters(factor_id, parameters)
            except Exception as e:
                errors.append(f"因子 {factor_id} 参数验证失败: {str(e)}")
        
        # 检查权重总和
        if abs(total_weight - 1.0) > 0.01:  # 允许1%误差
            if total_weight == 0:
                errors.append("因子权重总和不能为0")
            else:
                warnings.append(f"因子权重总和为 {total_weight:.3f}，建议为1.0")
        
        return {
            'errors': errors,
            'warnings': warnings,
            'is_valid': len(errors) == 0
        }
    
    def get_factor_preview(self, factor_id: str, data: pd.DataFrame, 
                          parameters: Dict[str, Any] = None, 
                          sample_size: int = 100) -> Dict[str, Any]:
        """获取因子预览数据"""
        if len(data) > sample_size:
            preview_data = data.tail(sample_size)
        else:
            preview_data = data
        
        try:
            result = self.calculate_single_factor(factor_id, preview_data, parameters)
            
            # 生成预览信息
            if isinstance(result, pd.Series):
                preview_info = self._generate_series_preview(result)
            else:
                preview_info = self._generate_dataframe_preview(result)
            
            return {
                'factor_id': factor_id,
                'success': True,
                'preview_data': preview_info,
                'data_points': len(result),
                'latest_date': preview_data.index[-1] if len(preview_data) > 0 else None
            }
            
        except Exception as e:
            return {
                'factor_id': factor_id,
                'success': False,
                'error': str(e)
            }
    
    def _generate_series_preview(self, series: pd.Series) -> Dict[str, Any]:
        """生成Series预览信息"""
        return {
            'type': 'series',
            'latest_value': series.iloc[-1] if len(series) > 0 else None,
            'mean': series.mean(),
            'std': series.std(),
            'min': series.min(),
            'max': series.max(),
            'null_count': series.isnull().sum(),
            'sample_values': series.tail(10).to_dict()
        }
    
    def _generate_dataframe_preview(self, df: pd.DataFrame) -> Dict[str, Any]:
        """生成DataFrame预览信息"""
        preview = {'type': 'dataframe', 'columns': {}}
        
        for col in df.columns:
            series = df[col]
            preview['columns'][col] = {
                'latest_value': series.iloc[-1] if len(series) > 0 else None,
                'mean': series.mean(),
                'std': series.std(),
                'min': series.min(),
                'max': series.max(),
                'null_count': series.isnull().sum(),
                'sample_values': series.tail(5).to_dict()
            }
        
        return preview
    
    def _get_cache_key(self, factor_id: str, data: pd.DataFrame, 
                      parameters: Dict[str, Any] = None) -> str:
        """生成缓存键"""
        # 使用数据的hash和参数生成缓存键
        data_hash = pd.util.hash_pandas_object(data).sum()
        param_str = str(sorted(parameters.items()) if parameters else "")
        
        return f"{factor_id}_{data_hash}_{hash(param_str)}"
    
    def clear_cache(self):
        """清除计算缓存"""
        self.calculation_cache.clear()
        logger.info("计算缓存已清除")
    
    def get_engine_status(self) -> Dict[str, Any]:
        """获取引擎状态"""
        return {
            'registered_factors': len(self.factor_registry),
            'factors_by_category': {
                'trend': len(self.list_factors_by_category(FactorCategory.TREND)),
                'momentum': len(self.list_factors_by_category(FactorCategory.MOMENTUM)),
                'volume': len(self.list_factors_by_category(FactorCategory.VOLUME))
            },
            'cache_enabled': self.cache_enabled,
            'cached_results': len(self.calculation_cache),
            'cache_expiry_seconds': self.cache_expiry
        }


# 全局内置因子引擎实例
builtin_factor_engine = BuiltinFactorEngine()