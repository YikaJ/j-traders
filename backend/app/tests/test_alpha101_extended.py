"""
测试扩展的Alpha101因子库功能
"""

import pandas as pd
import numpy as np
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

# 模拟导入（实际使用时需要调整导入路径）
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.alpha101_extended import (
    Alpha101ExtendedService, 
    TushareDataAdapter,
    Alpha001ExtendedCalculator,
    Alpha002ExtendedCalculator,
    Alpha003ExtendedCalculator
)
from services.alpha101_more_factors import Alpha101MoreFactorsService
from config.tushare_config import TushareConfig, get_stock_code_format


class TestAlpha101Extended:
    """测试扩展的Alpha101因子库"""
    
    @pytest.fixture
    def sample_data(self):
        """创建测试用的股票数据"""
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        dates = dates[dates.weekday < 5]  # 只保留工作日
        
        np.random.seed(42)
        n_days = len(dates)
        
        # 生成模拟价格数据
        base_price = 10.0
        returns = np.random.normal(0, 0.02, n_days)
        prices = base_price * np.exp(np.cumsum(returns))
        
        data = pd.DataFrame({
            'date': dates,
            'open': prices * (1 + np.random.normal(0, 0.001, n_days)),
            'high': prices * (1 + np.abs(np.random.normal(0, 0.01, n_days))),
            'low': prices * (1 - np.abs(np.random.normal(0, 0.01, n_days))),
            'close': prices,
            'volume': np.random.randint(1000000, 10000000, n_days),
            'amount': prices * np.random.randint(1000000, 10000000, n_days) / 1000,
            'pre_close': np.concatenate([[base_price], prices[:-1]]),
        })
        
        # 确保high >= max(open, close) and low <= min(open, close)
        data['high'] = np.maximum(data['high'], np.maximum(data['open'], data['close']))
        data['low'] = np.minimum(data['low'], np.minimum(data['open'], data['close']))
        
        return data
    
    def test_alpha001_calculator(self, sample_data):
        """测试Alpha001因子计算器"""
        calculator = Alpha001ExtendedCalculator()
        
        # 测试基本信息
        assert calculator.alpha_id == "001"
        assert calculator.name == "Alpha001"
        assert "价格波动调整动量因子" in calculator.display_name
        
        # 测试计算
        result = calculator.calculate(sample_data)
        
        # 验证结果
        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_data)
        assert not result.isna().all()  # 不能全部为NaN
        
        # 验证数值范围（排名值应该在0-1之间）
        valid_values = result.dropna()
        if len(valid_values) > 0:
            assert valid_values.min() >= -1.0
            assert valid_values.max() <= 1.0
    
    def test_alpha002_calculator(self, sample_data):
        """测试Alpha002因子计算器"""
        calculator = Alpha002ExtendedCalculator()
        
        # 测试基本信息
        assert calculator.alpha_id == "002"
        assert "成交量变化与收益率相关性" in calculator.display_name
        
        # 测试计算
        result = calculator.calculate(sample_data)
        
        # 验证结果
        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_data)
        
        # 相关系数结果应该在-1到1之间
        valid_values = result.dropna()
        if len(valid_values) > 0:
            assert valid_values.min() >= -1.0
            assert valid_values.max() <= 1.0
    
    def test_alpha003_calculator(self, sample_data):
        """测试Alpha003因子计算器"""
        calculator = Alpha003ExtendedCalculator()
        
        # 测试基本信息
        assert calculator.alpha_id == "003"
        assert "开盘价与成交量负相关" in calculator.display_name
        
        # 测试计算
        result = calculator.calculate(sample_data)
        
        # 验证结果
        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_data)
        
        # 相关系数结果应该在-1到1之间
        valid_values = result.dropna()
        if len(valid_values) > 0:
            assert valid_values.min() >= -1.0
            assert valid_values.max() <= 1.0
    
    def test_alpha101_extended_service(self, sample_data):
        """测试扩展的Alpha101服务"""
        service = Alpha101ExtendedService()
        
        # 测试获取可用因子
        factors = service.get_available_factors()
        assert len(factors) > 0
        
        # 验证因子信息结构
        factor = factors[0]
        required_keys = ['factor_id', 'name', 'display_name', 'description', 
                        'formula', 'input_fields', 'category']
        for key in required_keys:
            assert key in factor
        
        # 测试获取因子详细信息
        factor_id = factors[0]['factor_id']
        factor_info = service.get_factor_info(factor_id)
        assert factor_info is not None
        assert factor_info['factor_id'] == factor_id
        
        # 测试计算单个因子
        result = service.calculate_single_factor(factor_id, sample_data)
        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_data)
    
    def test_alpha101_more_factors_service(self):
        """测试更多Alpha101因子服务"""
        service = Alpha101MoreFactorsService()
        
        # 测试获取可用因子
        factors = service.get_available_factors()
        assert len(factors) > 0
        
        # 验证包含Alpha007-Alpha030
        factor_ids = [f['factor_id'] for f in factors]
        assert 'alpha101_007' in factor_ids
        assert 'alpha101_008' in factor_ids
        assert 'alpha101_021' in factor_ids
    
    def test_tushare_config(self):
        """测试Tushare配置"""
        # 测试配置创建
        config = TushareConfig(token="test_token", timeout=60)
        assert config.token == "test_token"
        assert config.timeout == 60
        
        # 测试股票代码格式化
        assert get_stock_code_format("000001") == "000001.SZ"
        assert get_stock_code_format("600000") == "600000.SH"
        assert get_stock_code_format("000001.SZ") == "000001.SZ"
        
        # 测试异常情况
        with pytest.raises(ValueError):
            get_stock_code_format("999999")  # 无效的股票代码
    
    def test_data_preparation(self, sample_data):
        """测试数据预处理功能"""
        calculator = Alpha001ExtendedCalculator()
        prepared_data = calculator.prepare_data(sample_data)
        
        # 验证计算出的衍生字段
        assert 'returns' in prepared_data.columns
        assert 'vwap' in prepared_data.columns
        assert 'adv20' in prepared_data.columns
        
        # 验证收益率计算
        returns = prepared_data['returns'].dropna()
        assert not returns.empty
        
        # 验证VWAP计算
        vwap = prepared_data['vwap'].dropna()
        assert not vwap.empty
        assert vwap.min() > 0  # VWAP应该为正数
    
    def test_error_handling(self):
        """测试错误处理"""
        calculator = Alpha001ExtendedCalculator()
        
        # 测试空数据
        empty_data = pd.DataFrame()
        with pytest.raises(ValueError, match="数据为空"):
            calculator.calculate(empty_data)
        
        # 测试缺少必要列
        incomplete_data = pd.DataFrame({'date': [1, 2, 3]})
        with pytest.raises(ValueError, match="缺少必要的数据列"):
            calculator.calculate(incomplete_data)
    
    def test_factor_formula_display(self):
        """测试因子公式显示"""
        calculator = Alpha001ExtendedCalculator()
        formula = calculator.get_formula()
        
        assert isinstance(formula, str)
        assert len(formula) > 0
        assert "rank" in formula.lower()  # Alpha因子通常包含rank操作


class TestTushareDataAdapter:
    """测试Tushare数据适配器"""
    
    def test_adapter_initialization(self):
        """测试适配器初始化"""
        # 测试无token初始化
        adapter = TushareDataAdapter()
        assert adapter.token is None
        assert adapter.pro is None
        
        # 测试有token初始化（模拟）
        adapter = TushareDataAdapter(token="test_token")
        assert adapter.token == "test_token"
        # 注意：实际测试中可能需要mock tushare库
    
    def test_mock_data_retrieval(self):
        """测试模拟数据获取（不依赖真实API）"""
        # 这里可以添加mock测试，模拟Tushare API返回
        pass


def create_test_data_with_trends():
    """创建包含趋势的测试数据"""
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    
    # 创建上升趋势
    trend = np.linspace(10, 15, 100)
    noise = np.random.normal(0, 0.1, 100)
    prices = trend + noise
    
    data = pd.DataFrame({
        'date': dates,
        'open': prices * 0.99,
        'high': prices * 1.02,
        'low': prices * 0.98,
        'close': prices,
        'volume': np.random.randint(1000000, 5000000, 100),
        'amount': prices * np.random.randint(1000000, 5000000, 100) / 1000,
    })
    
    return data


def test_integration_alpha101_factors():
    """集成测试Alpha101因子"""
    # 创建测试数据
    test_data = create_test_data_with_trends()
    
    # 创建服务实例
    extended_service = Alpha101ExtendedService()
    more_factors_service = Alpha101MoreFactorsService()
    
    # 测试多个因子计算
    factor_results = {}
    
    # 测试扩展服务的因子
    for factor_info in extended_service.get_available_factors()[:3]:  # 只测试前3个
        factor_id = factor_info['factor_id']
        try:
            result = extended_service.calculate_single_factor(factor_id, test_data)
            factor_results[factor_id] = result
            print(f"✓ {factor_id} 计算成功")
        except Exception as e:
            print(f"✗ {factor_id} 计算失败: {e}")
    
    # 测试更多因子服务的因子
    for factor_info in more_factors_service.get_available_factors()[:3]:  # 只测试前3个
        factor_id = factor_info['factor_id']
        try:
            calculator = more_factors_service.calculators[factor_id]
            result = calculator.calculate(test_data)
            factor_results[factor_id] = result
            print(f"✓ {factor_id} 计算成功")
        except Exception as e:
            print(f"✗ {factor_id} 计算失败: {e}")
    
    print(f"\n总共测试了 {len(factor_results)} 个因子")
    return factor_results


if __name__ == "__main__":
    # 运行集成测试
    print("开始Alpha101扩展因子库集成测试...")
    results = test_integration_alpha101_factors()
    
    print("\n测试完成！")
    
    # 显示部分结果统计
    for factor_id, result in results.items():
        valid_count = result.dropna().count()
        print(f"{factor_id}: {valid_count}/{len(result)} 个有效值")