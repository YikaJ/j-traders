"""
统一因子服务
支持从数据库读取因子公式并动态执行
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union
import logging
from datetime import datetime
import traceback
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models.factor import Factor, FactorFormulaHistory

logger = logging.getLogger(__name__)


class UnifiedFactorService:
    """统一因子服务"""
    
    def __init__(self):
        self.execution_cache = {}
        self.cache_expiry = 3600  # 1小时过期
    
    def get_all_factors(self, db: Session) -> List[Dict[str, Any]]:
        """获取所有因子"""
        try:
            factors = db.query(Factor).filter(Factor.is_active == True).all()
            return [self._factor_to_dict(factor) for factor in factors]
        except Exception as e:
            logger.error(f"获取因子列表失败: {e}")
            return []
    
    def get_factor_by_id(self, factor_id: str, db: Session) -> Optional[Dict[str, Any]]:
        """根据ID获取因子"""
        try:
            factor = db.query(Factor).filter(Factor.factor_id == factor_id).first()
            if factor:
                return self._factor_to_dict(factor)
            return None
        except Exception as e:
            logger.error(f"获取因子 {factor_id} 失败: {e}")
            return None
    
    def create_factor(self, factor_data: Dict[str, Any], db: Session) -> Optional[Dict[str, Any]]:
        """创建新因子"""
        try:
            # 检查因子ID是否已存在
            existing = db.query(Factor).filter(Factor.factor_id == factor_data['factor_id']).first()
            if existing:
                raise ValueError(f"因子ID {factor_data['factor_id']} 已存在")
            
            # 验证公式
            validation_result = self.validate_formula(factor_data['formula'])
            if not validation_result['is_valid']:
                raise ValueError(f"公式验证失败: {validation_result['error_message']}")
            
            # 创建因子
            new_factor = Factor(**factor_data)
            db.add(new_factor)
            db.commit()
            db.refresh(new_factor)
            
            logger.info(f"创建因子成功: {new_factor.factor_id}")
            return self._factor_to_dict(new_factor)
            
        except Exception as e:
            logger.error(f"创建因子失败: {e}")
            db.rollback()
            raise
    
    def update_factor(self, factor_id: str, update_data: Dict[str, Any], db: Session) -> Optional[Dict[str, Any]]:
        """更新因子"""
        try:
            factor = db.query(Factor).filter(Factor.factor_id == factor_id).first()
            if not factor:
                raise ValueError(f"因子 {factor_id} 不存在")
            
            # 如果更新了公式，验证语法
            if 'formula' in update_data:
                validation_result = self.validate_formula(update_data['formula'])
                if not validation_result['is_valid']:
                    raise ValueError(f"公式验证失败: {validation_result['error_message']}")
                
                # 记录历史
                history = FactorFormulaHistory(
                    factor_id=factor_id,
                    old_formula=factor.formula,
                    new_formula=update_data['formula'],
                    old_description=factor.description,
                    new_description=update_data.get('description', factor.description)
                )
                db.add(history)
            
            # 更新字段
            for key, value in update_data.items():
                if hasattr(factor, key):
                    setattr(factor, key, value)
            
            factor.updated_at = datetime.now()
            db.commit()
            db.refresh(factor)
            
            logger.info(f"更新因子成功: {factor_id}")
            return self._factor_to_dict(factor)
            
        except Exception as e:
            logger.error(f"更新因子失败: {e}")
            db.rollback()
            raise
    
    def delete_factor(self, factor_id: str, db: Session) -> bool:
        """删除因子"""
        try:
            factor = db.query(Factor).filter(Factor.factor_id == factor_id).first()
            if not factor:
                raise ValueError(f"因子 {factor_id} 不存在")
            
            # 不允许删除内置因子
            if factor.is_builtin:
                raise ValueError("不能删除内置因子")
            
            db.delete(factor)
            db.commit()
            
            logger.info(f"删除因子成功: {factor_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除因子失败: {e}")
            db.rollback()
            raise
    
    def calculate_factor(self, factor_id: str, data: pd.DataFrame, parameters: Dict[str, Any] = None, db: Session = None) -> Union[pd.Series, pd.DataFrame]:
        """计算因子值"""
        try:
            # 获取因子信息
            if db is None:
                db = next(get_db())
            
            factor_info = self.get_factor_by_id(factor_id, db)
            if not factor_info:
                raise ValueError(f"因子 {factor_id} 不存在")
            
            # 检查缓存
            cache_key = self._get_cache_key(factor_id, data, parameters)
            if cache_key in self.execution_cache:
                cache_entry = self.execution_cache[cache_key]
                if datetime.now().timestamp() - cache_entry['timestamp'] < self.cache_expiry:
                    logger.debug(f"使用缓存结果: {factor_id}")
                    return cache_entry['result']
            
            # 动态执行公式
            result = self._execute_formula(factor_info['formula'], data, parameters)
            
            # 缓存结果
            self.execution_cache[cache_key] = {
                'result': result,
                'timestamp': datetime.now().timestamp()
            }
            
            # 更新使用统计
            self._update_usage_stats(factor_id, db)
            
            return result
            
        except Exception as e:
            logger.error(f"计算因子 {factor_id} 失败: {e}")
            raise
    
    def validate_formula(self, formula: str) -> Dict[str, Any]:
        """验证因子公式"""
        try:
            warnings = []
            
            # 基本语法检查
            if not formula or not formula.strip():
                return {
                    'is_valid': False,
                    'error_message': "公式不能为空"
                }
            
            # 检查是否包含危险操作
            dangerous_keywords = ['exec', 'eval', '__', 'delete', 'rm ', 'os.']
            for keyword in dangerous_keywords:
                if keyword in formula.lower():
                    return {
                        'is_valid': False,
                        'error_message': f"公式包含不安全的关键词: {keyword}"
                    }
            
            # 检查括号匹配
            open_parens = formula.count('(')
            close_parens = formula.count(')')
            if open_parens != close_parens:
                return {
                    'is_valid': False,
                    'error_message': f"括号不匹配：开括号 {open_parens} 个，闭括号 {close_parens} 个"
                }
            
            # 检查是否包含常用变量
            common_variables = ['open', 'close', 'high', 'low', 'volume', 'vwap', 'returns']
            has_variable = any(var in formula.lower() for var in common_variables)
            
            if not has_variable:
                warnings.append("公式中似乎没有包含常用的价格或成交量变量")
            
            # 尝试编译（但不执行）
            try:
                # 直接编译公式代码
                compile(formula, '<string>', 'exec')
                
            except SyntaxError as e:
                return {
                    'is_valid': False,
                    'error_message': f"语法错误: {str(e)}"
                }
            except Exception as e:
                return {
                    'is_valid': False,
                    'error_message': f"编译错误: {str(e)}"
                }
            
            return {
                'is_valid': True,
                'error_message': None,
                'warnings': warnings
            }
            
        except Exception as e:
            logger.error(f"验证公式失败: {e}")
            return {
                'is_valid': False,
                'error_message': f"验证过程出错: {str(e)}"
            }
    
    def get_formula_history(self, factor_id: str, db: Session) -> List[Dict[str, Any]]:
        """获取因子公式历史"""
        try:
            history = db.query(FactorFormulaHistory).filter(
                FactorFormulaHistory.factor_id == factor_id
            ).order_by(FactorFormulaHistory.created_at.desc()).all()
            
            return [
                {
                    'id': h.id,
                    'factor_id': h.factor_id,
                    'old_formula': h.old_formula,
                    'new_formula': h.new_formula,
                    'old_description': h.old_description,
                    'new_description': h.new_description,
                    'changed_by': h.changed_by,
                    'change_reason': h.change_reason,
                    'created_at': h.created_at.isoformat() if h.created_at else None
                }
                for h in history
            ]
        except Exception as e:
            logger.error(f"获取因子公式历史失败: {e}")
            return []
    
    def _execute_formula(self, formula: str, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> Union[pd.Series, pd.DataFrame]:
        """动态执行因子公式"""
        try:
            # 创建执行环境
            exec_globals = {
                'pd': pd,
                'np': np,
                'data': data,
                'parameters': parameters or {}
            }
            
            # 构建完整的执行代码
            exec_code = f"""
def calculate_factor(data, parameters):
{formula}
    return result

result = calculate_factor(data, parameters)
"""
            
            # 执行代码
            exec(exec_code, exec_globals)
            result = exec_globals['result']
            
            # 确保结果是pandas Series或DataFrame
            if not isinstance(result, (pd.Series, pd.DataFrame)):
                if isinstance(result, (list, np.ndarray)):
                    result = pd.Series(result, index=data.index)
                else:
                    result = pd.Series(result, index=data.index)
            
            return result
            
        except Exception as e:
            logger.error(f"执行公式失败: {e}")
            logger.error(f"公式内容: {formula}")
            logger.error(f"错误详情: {traceback.format_exc()}")
            raise ValueError(f"公式执行失败: {str(e)}")
    
    def _factor_to_dict(self, factor: Factor) -> Dict[str, Any]:
        """将因子对象转换为字典"""
        return {
            'id': factor.id,
            'factor_id': factor.factor_id,
            'name': factor.name,
            'display_name': factor.display_name,
            'description': factor.description,
            'category': factor.category,
            'formula': factor.formula,
            'input_fields': factor.input_fields,
            'default_parameters': factor.default_parameters,
            'parameter_schema': factor.parameter_schema,
            'calculation_method': factor.calculation_method,
            'is_active': factor.is_active,
            'is_builtin': factor.is_builtin,
            'usage_count': factor.usage_count,
            'last_used_at': factor.last_used_at.isoformat() if factor.last_used_at else None,
            'created_at': factor.created_at.isoformat() if factor.created_at else None,
            'updated_at': factor.updated_at.isoformat() if factor.updated_at else None,
            'version': factor.version
        }
    
    def _get_cache_key(self, factor_id: str, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> str:
        """生成缓存键"""
        data_hash = pd.util.hash_pandas_object(data).sum()
        param_str = str(sorted(parameters.items()) if parameters else "")
        return f"{factor_id}_{data_hash}_{hash(param_str)}"
    
    def _update_usage_stats(self, factor_id: str, db: Session):
        """更新因子使用统计"""
        try:
            factor = db.query(Factor).filter(Factor.factor_id == factor_id).first()
            if factor:
                factor.usage_count = (factor.usage_count or 0) + 1
                factor.last_used_at = datetime.now()
                db.commit()
        except Exception as e:
            logger.error(f"更新因子使用统计失败: {e}")


# 全局统一因子服务实例
unified_factor_service = UnifiedFactorService() 