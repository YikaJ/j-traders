"""
因子服务
实现因子代码验证、测试和执行功能
"""

import ast
import time
import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.schemas.factors import (
    FactorValidationResult,
    FactorTestResponse,
    FactorTestResult
)
from app.services.tushare_service import tushare_service
from app.db.database import SessionLocal
from app.db.models.stock import Stock, StockDaily

logger = logging.getLogger(__name__)


class FactorService:
    """因子服务类"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=3)
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
            logger.warning(f"获取测试数据失败，使用模拟数据: {e}")
            return self._generate_mock_data(symbols, start_date, end_date)
    
    def _generate_mock_data(self, symbols: List[str], start_date: str, end_date: str) -> pd.DataFrame:
        """生成模拟测试数据"""
        try:
            import random
            
            data = []
            for symbol in symbols:
                # 生成30天的模拟数据
                base_price = random.uniform(10, 100)
                for i in range(30):
                    date = (datetime.strptime(end_date, '%Y%m%d') - timedelta(days=29-i)).strftime('%Y%m%d')
                    
                    # 模拟价格波动
                    change = random.uniform(-0.05, 0.05)
                    base_price *= (1 + change)
                    
                    data.append({
                        'symbol': symbol,
                        'trade_date': date,
                        'open': round(base_price * random.uniform(0.98, 1.02), 2),
                        'high': round(base_price * random.uniform(1.0, 1.05), 2),
                        'low': round(base_price * random.uniform(0.95, 1.0), 2),
                        'close': round(base_price, 2),
                        'volume': random.randint(100000, 5000000),
                        'amount': random.uniform(1000000, 50000000),
                        'pe_ttm': random.uniform(5, 50),
                        'pb': random.uniform(0.5, 5),
                        'total_mv': random.uniform(1000000, 100000000),
                        'circ_mv': random.uniform(500000, 50000000)
                    })
            
            return pd.DataFrame(data)
        
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


# 创建全局实例
factor_service = FactorService()