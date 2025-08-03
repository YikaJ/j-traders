"""
统一因子服务
整合因子管理、验证、测试和执行功能
"""

import ast
import time
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor
import traceback
from sqlalchemy.orm import Session
import uuid

from app.db.database import get_db, SessionLocal
from app.db.models.factor import Factor, FactorHistory
from app.db.models.stock import Stock, StockDaily
from app.schemas.factors import (
    FactorValidationResult,
    FactorTestResponse,
    FactorTestResult
)
from app.services.tushare_service import tushare_service

logger = logging.getLogger(__name__)


class UnifiedFactorService:
    """统一因子服务 - 整合管理、验证、测试和执行功能"""
    
    def __init__(self):
        self.execution_cache = {}
        self.cache_expiry = 3600  # 1小时过期
        self.executor = ThreadPoolExecutor(max_workers=3)
        
        # 安全的内置函数和模块
        self.safe_builtins = {
            # 安全的内置函数
            'abs', 'all', 'any', 'bool', 'dict', 'enumerate', 'filter',
            'float', 'int', 'len', 'list', 'map', 'max', 'min', 'range',
            'round', 'set', 'sorted', 'str', 'sum', 'tuple', 'zip',
            # 数学函数
            'pow',
        }
        self.safe_modules = {
            'pandas': 'pd',
            'numpy': 'np',
            'math': 'math'
        }
    
    # ==================== 因子管理功能 ====================
    
    def get_all_factors(self, db: Session) -> List[Dict[str, Any]]:
        """获取所有因子"""
        try:
            # 获取所有因子，不过滤is_active
            factors = db.query(Factor).all()
            logger.info(f"从数据库获取到 {len(factors)} 个因子")
            
            result = [self._factor_to_dict(factor) for factor in factors]
            logger.info(f"转换后返回 {len(result)} 个因子")
            
            return result
        except Exception as e:
            logger.error(f"获取因子列表失败: {e}")
            return []
    
    def get_factor_by_id(self, id: str, db: Session) -> Optional[Dict[str, Any]]:
        """根据ID获取因子"""
        try:
            factor = db.query(Factor).filter(Factor.id == id).first()
            if factor:
                return self._factor_to_dict(factor)
            return None
        except Exception as e:
            logger.error(f"获取因子 {id} 失败: {e}")
            return None
    
    def create_factor(self, factor_data: Dict[str, Any], db: Session) -> Optional[Dict[str, Any]]:
        """创建新因子"""
        try:
            # 字段映射：将前端字段映射到数据库字段
            db_factor_data = {}
            
            # 自动生成因子ID
            factor_id = str(uuid.uuid4())
            db_factor_data['factor_id'] = factor_id
            
            # 映射其他字段
            if 'name' in factor_data:
                db_factor_data['name'] = factor_data['name']
            if 'display_name' in factor_data:
                db_factor_data['display_name'] = factor_data['display_name']
            if 'description' in factor_data:
                db_factor_data['description'] = factor_data['description']
            if 'category' in factor_data:
                db_factor_data['category'] = factor_data['category']
            if 'formula' in factor_data:
                db_factor_data['formula'] = factor_data['formula']
            elif 'code' in factor_data:
                db_factor_data['formula'] = factor_data['code']
            if 'input_fields' in factor_data:
                db_factor_data['input_fields'] = factor_data['input_fields']
            if 'default_parameters' in factor_data:
                db_factor_data['default_parameters'] = factor_data['default_parameters']
            if 'calculation_method' in factor_data:
                db_factor_data['calculation_method'] = factor_data['calculation_method']
            
            # 验证公式
            validation_result = self.validate_formula(db_factor_data['formula'])
            if not validation_result['is_valid']:
                raise ValueError(f"公式验证失败: {validation_result['errors']}")
            
            # 创建因子
            new_factor = Factor(**db_factor_data)
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
            
            # 字段映射：将前端字段映射到数据库字段
            db_update_data = {}
            for key, value in update_data.items():
                if key == 'code':
                    db_update_data['formula'] = value
                elif hasattr(factor, key):
                    db_update_data[key] = value
            
            # 如果更新了公式，验证语法
            if 'formula' in db_update_data:
                validation_result = self.validate_formula(db_update_data['formula'])
                if not validation_result['is_valid']:
                    raise ValueError(f"公式验证失败: {validation_result['errors']}")
                
                # 记录公式变更历史
                history = FactorHistory(
                    factor_id=factor.id,
                    old_code=factor.formula,
                    new_code=db_update_data['formula'],
                    old_description=factor.description,
                    new_description=db_update_data.get('description', factor.description),
                    changed_by=db_update_data.get('changed_by', 'system'),
                    change_reason=db_update_data.get('change_reason', '公式更新')
                )
                db.add(history)
            
            # 更新字段
            for key, value in db_update_data.items():
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
    
    # ==================== 因子验证功能 ====================
    
    async def validate_factor_code(self, code: str) -> FactorValidationResult:
        """
        验证因子代码语法和安全性
        
        Args:
            code: 因子代码
        
        Returns:
            验证结果
        """
        try:
            # 基本语法检查
            try:
                tree = ast.parse(code)
            except SyntaxError as e:
                return FactorValidationResult(
                    is_valid=False,
                    error_message=f"语法错误: {str(e)}"
                )
            
            # 安全性检查
            security_check = self._check_code_security(tree)
            if not security_check.is_valid:
                return security_check
            
            # 检查是否有calculate函数
            has_calculate = False
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == 'calculate':
                    has_calculate = True
                    # 检查函数参数
                    if len(node.args.args) != 1:
                        return FactorValidationResult(
                            is_valid=False,
                            error_message="calculate函数必须有且仅有一个参数(data)"
                        )
                    break
            
            if not has_calculate:
                return FactorValidationResult(
                    is_valid=False,
                    error_message="代码必须包含calculate(data)函数"
                )
            
            # 尝试编译代码
            try:
                compile(code, '<factor_code>', 'exec')
            except Exception as e:
                return FactorValidationResult(
                    is_valid=False,
                    error_message=f"编译错误: {str(e)}"
                )
            
            return FactorValidationResult(is_valid=True)
        
        except Exception as e:
            logger.error(f"验证因子代码失败: {e}")
            return FactorValidationResult(
                is_valid=False,
                error_message=f"验证失败: {str(e)}"
            )
    
    def _check_code_security(self, tree: ast.AST) -> FactorValidationResult:
        """
        检查代码安全性
        
        Args:
            tree: AST语法树
        
        Returns:
            安全性检查结果
        """
        dangerous_nodes = []
        
        for node in ast.walk(tree):
            # 检查导入语句
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name not in self.safe_modules:
                        dangerous_nodes.append(f"不允许导入模块: {alias.name}")
            
            elif isinstance(node, ast.ImportFrom):
                if node.module not in self.safe_modules:
                    dangerous_nodes.append(f"不允许从模块导入: {node.module}")
            
            # 检查属性访问
            elif isinstance(node, ast.Attribute):
                # 禁止访问私有属性
                if node.attr.startswith('_'):
                    dangerous_nodes.append(f"不允许访问私有属性: {node.attr}")
            
            # 检查函数调用
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    # 检查是否为危险函数
                    dangerous_funcs = {'exec', 'eval', 'compile', 'open', '__import__'}
                    if func_name in dangerous_funcs:
                        dangerous_nodes.append(f"不允许调用函数: {func_name}")
        
        if dangerous_nodes:
            return FactorValidationResult(
                is_valid=False,
                error_message="代码包含不安全的操作: " + "; ".join(dangerous_nodes[:3])
            )
        
        return FactorValidationResult(is_valid=True)
    
    def validate_formula(self, code: str) -> Dict[str, Any]:
        """验证因子公式语法"""
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        if not code or not code.strip():
            result['is_valid'] = False
            result['errors'].append('公式不能为空')
            return result
        
        # 检查危险关键字
        dangerous_keywords = ['import', 'exec', 'eval', 'open', 'file', '__']
        for keyword in dangerous_keywords:
            if keyword in code.lower():
                result['is_valid'] = False
                result['errors'].append(f'公式包含危险关键字: {keyword}')
        
        # 检查括号匹配
        open_parens = code.count('(')
        close_parens = code.count(')')
        if open_parens != close_parens:
            result['is_valid'] = False
            result['errors'].append('括号不匹配')
        
        # 检查基本语法
        try:
            # 检查是否有常用变量
            common_variables = ['data', 'result', 'close', 'open', 'high', 'low', 'volume']
            has_variable = any(var in code.lower() for var in common_variables)
            
            # 尝试编译代码
            compile(code, '<string>', 'exec')
            
            if not has_variable:
                result['warnings'].append('公式中未发现常用变量，请检查是否正确')
                
        except SyntaxError as e:
            result['is_valid'] = False
            result['errors'].append(f'语法错误: {str(e)}')
        except Exception as e:
            result['is_valid'] = False
            result['errors'].append(f'验证失败: {str(e)}')
        
        return result
    
    # ==================== 因子测试功能 ====================
    
    async def test_factor(
        self,
        factor_code: str,
        test_symbols: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> FactorTestResponse:
        """
        测试因子代码
        
        Args:
            factor_code: 因子代码
            test_symbols: 测试股票代码列表
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            测试结果
        """
        start_time = time.time()
        
        try:
            # 首先验证代码
            validation = await self.validate_factor_code(factor_code)
            if not validation.is_valid:
                return FactorTestResponse(
                    success=False,
                    message=f"代码验证失败: {validation.error_message}",
                    executionTime=time.time() - start_time,
                    results=[],
                    statistics={}
                )
            
            # 获取测试数据
            test_data = await self._get_test_data(test_symbols, start_date, end_date)
            if test_data.empty:
                return FactorTestResponse(
                    success=False,
                    message="无法获取测试数据",
                    executionTime=time.time() - start_time,
                    results=[],
                    statistics={}
                )
            
            # 执行因子计算
            results = await self._execute_factor_code(factor_code, test_data, test_symbols)
            
            execution_time = time.time() - start_time
            
            return FactorTestResponse(
                success=True,
                message="测试完成",
                executionTime=execution_time,
                results=results,
                statistics=self._calculate_statistics(results)
            )
        
        except Exception as e:
            logger.error(f"测试因子失败: {e}")
            return FactorTestResponse(
                success=False,
                message=f"测试失败: {str(e)}",
                executionTime=time.time() - start_time,
                results=[],
                statistics={}
            )
    
    async def _get_test_data(
        self,
        symbols: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        获取测试数据
        
        Args:
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            测试数据DataFrame
        """
        try:
            # 设置默认日期范围
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
            
            db = SessionLocal()
            try:
                # 从数据库获取历史数据
                all_data = []
                for symbol in symbols:
                    stock_data = db.query(StockDaily).filter(
                        StockDaily.symbol == symbol,
                        StockDaily.trade_date >= start_date,
                        StockDaily.trade_date <= end_date
                    ).order_by(StockDaily.trade_date).all()
                    
                    if stock_data:
                        # 转换为DataFrame格式
                        data_dict = []
                        for record in stock_data:
                            data_dict.append({
                                'symbol': record.symbol,
                                'trade_date': record.trade_date,
                                'open': record.open,
                                'high': record.high,
                                'low': record.low,
                                'close': record.close,
                                'volume': record.vol,
                                'amount': record.amount,
                                'pe_ttm': record.pe_ttm,
                                'pb': record.pb,
                                'total_mv': record.total_mv,
                                'circ_mv': record.circ_mv
                            })
                        
                        if data_dict:
                            df = pd.DataFrame(data_dict)
                            all_data.append(df)
                
                if all_data:
                    return pd.concat(all_data, ignore_index=True)
                else:
                    # 如果数据库没有数据，生成模拟数据
                    return self._generate_mock_data(symbols, start_date, end_date)
            
            finally:
                db.close()
        
        except Exception as e:
            logger.warning(f"获取测试数据失败: {e}")
            return pd.DataFrame()
    
    def _generate_mock_data(self, symbols: List[str], start_date: str, end_date: str) -> pd.DataFrame:
        """生成模拟测试数据"""
        try:
            start_dt = datetime.strptime(start_date, '%Y%m%d')
            end_dt = datetime.strptime(end_date, '%Y%m%d')
            date_range = pd.date_range(start=start_dt, end=end_dt, freq='D')
            
            all_data = []
            for symbol in symbols:
                # 生成模拟价格数据
                base_price = 10 + hash(symbol) % 50  # 基于股票代码生成基础价格
                prices = []
                current_price = base_price
                
                for date in date_range:
                    # 简单的随机价格变动
                    change = np.random.normal(0, 0.02) * current_price
                    current_price = max(0.1, current_price + change)
                    
                    open_price = current_price * (1 + np.random.normal(0, 0.01))
                    high_price = max(open_price, current_price) * (1 + abs(np.random.normal(0, 0.02)))
                    low_price = min(open_price, current_price) * (1 - abs(np.random.normal(0, 0.02)))
                    volume = int(np.random.uniform(1000000, 10000000))
                    
                    all_data.append({
                        'symbol': symbol,
                        'trade_date': date.strftime('%Y%m%d'),
                        'open': round(open_price, 2),
                        'high': round(high_price, 2),
                        'low': round(low_price, 2),
                        'close': round(current_price, 2),
                        'volume': volume,
                        'amount': round(volume * current_price, 2),
                        'pe_ttm': np.random.uniform(5, 50),
                        'pb': np.random.uniform(0.5, 5),
                        'total_mv': volume * current_price * np.random.uniform(0.8, 1.2),
                        'circ_mv': volume * current_price * np.random.uniform(0.6, 1.0)
                    })
            
            return pd.DataFrame(all_data)
        
        except Exception as e:
            logger.error(f"生成模拟数据失败: {e}")
            return pd.DataFrame()
    
    async def _execute_factor_code(
        self,
        factor_code: str,
        test_data: pd.DataFrame,
        symbols: List[str]
    ) -> List[FactorTestResult]:
        """
        执行因子代码
        
        Args:
            factor_code: 因子代码
            test_data: 测试数据
            symbols: 股票代码列表
        
        Returns:
            测试结果列表
        """
        def _run_factor():
            # 准备安全的执行环境
            safe_globals = {
                '__builtins__': {name: getattr(__builtins__, name) for name in self.safe_builtins if hasattr(__builtins__, name)},
                'pd': pd,
                'np': np,
            }
            
            # 执行因子代码
            exec(factor_code, safe_globals)
            
            # 获取calculate函数
            calculate_func = safe_globals.get('calculate')
            if not calculate_func:
                raise ValueError("未找到calculate函数")
            
            results = []
            
            # 为每个股票计算因子值
            for symbol in symbols:
                try:
                    # 获取该股票的数据
                    symbol_data = test_data[test_data['symbol'] == symbol].copy()
                    if symbol_data.empty:
                        continue
                    
                    # 设置索引为日期
                    symbol_data['trade_date'] = pd.to_datetime(symbol_data['trade_date'])
                    symbol_data = symbol_data.set_index('trade_date').sort_index()
                    
                    # 执行因子计算
                    factor_value = calculate_func(symbol_data)
                    
                    # 处理结果
                    if isinstance(factor_value, pd.Series):
                        # 如果返回Series，取最后一个值
                        final_value = factor_value.iloc[-1] if len(factor_value) > 0 else 0
                    elif isinstance(factor_value, (int, float)):
                        final_value = float(factor_value)
                    else:
                        final_value = 0
                    
                    # 处理NaN值
                    if pd.isna(final_value):
                        final_value = 0
                    
                    results.append({
                        'symbol': symbol,
                        'value': final_value
                    })
                
                except Exception as e:
                    logger.warning(f"计算{symbol}因子值失败: {e}")
                    results.append({
                        'symbol': symbol,
                        'value': 0
                    })
            
            return results
        
        # 在线程池中执行
        loop = asyncio.get_event_loop()
        raw_results = await loop.run_in_executor(self.executor, _run_factor)
        
        # 处理结果并添加排名和百分位数
        if raw_results:
            # 计算排名和百分位数
            values = [r['value'] for r in raw_results]
            sorted_values = sorted(values, reverse=True)
            
            results = []
            for i, result in enumerate(raw_results):
                value = result['value']
                rank = sorted_values.index(value) + 1
                percentile = (len(sorted_values) - rank + 1) / len(sorted_values) * 100
                
                results.append(FactorTestResult(
                    symbol=result['symbol'],
                    name=f"股票{result['symbol']}",  # 这里可以从数据库获取真实名称
                    value=value,
                    rank=rank,
                    percentile=percentile
                ))
            
            return results
        
        return []
    
    def _calculate_statistics(self, results: List[FactorTestResult]) -> Dict[str, Any]:
        """
        计算统计信息
        
        Args:
            results: 测试结果列表
        
        Returns:
            统计信息
        """
        if not results:
            return {}
        
        values = [r.value for r in results]
        
        return {
            'count': len(values),
            'mean': float(np.mean(values)),
            'std': float(np.std(values)),
            'min': float(np.min(values)),
            'max': float(np.max(values)),
            'median': float(np.median(values)),
            'q25': float(np.percentile(values, 25)),
            'q75': float(np.percentile(values, 75))
        }
    
    # ==================== 因子执行功能 ====================
    
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
            result = self._execute_formula(factor_info['code'], data, parameters)
            
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
    
    def _execute_formula(self, code: str, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> Union[pd.Series, pd.DataFrame]:
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
{code}
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
            logger.error(f"公式内容: {code}")
            logger.error(f"错误详情: {traceback.format_exc()}")
            raise ValueError(f"公式执行失败: {str(e)}")
    
    # ==================== 辅助功能 ====================
    
    def get_formula_history(self, factor_id: str, db: Session) -> List[Dict[str, Any]]:
        """获取因子公式历史记录"""
        try:
            history = db.query(FactorHistory).filter(
                FactorHistory.factor_id == factor_id
            ).order_by(FactorHistory.created_at.desc()).all()
            
            return [{
                'id': h.id,
                'factor_id': h.factor_id,
                'old_code': h.old_code,
                'new_code': h.new_code,
                'old_description': h.old_description,
                'new_description': h.new_description,
                'changed_by': h.changed_by,
                'change_reason': h.change_reason,
                'created_at': h.created_at.isoformat() if h.created_at else None
            } for h in history]
        except Exception as e:
            logger.error(f"获取公式历史失败: {e}")
            return []
    
    def _factor_to_dict(self, factor: Factor) -> Dict[str, Any]:
        """将因子对象转换为字典"""
        return {
            'id': str(factor.id),  # 转换为字符串
            'name': factor.name,
            'display_name': factor.display_name,
            'description': factor.description,
            'category': factor.category,
            'code': factor.formula,  # 使用formula字段作为code
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
            'version': factor.version,
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