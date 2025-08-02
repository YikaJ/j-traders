#!/usr/bin/env python3
"""
Alpha101 Phase3 & Phase4 因子测试脚本
测试 Alpha041-101 因子（筛选适合A股市场的因子）
"""

import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def create_sample_data(n_days=100, n_stocks=50):
    """创建模拟股票数据"""
    dates = pd.date_range(start='2023-01-01', periods=n_days, freq='D')
    stocks = [f'stock_{i:03d}' for i in range(1, n_stocks+1)]
    
    data = []
    for stock in stocks:
        # 基础价格
        base_price = np.random.uniform(10, 100)
        
        # 生成价格序列
        returns = np.random.normal(0, 0.02, n_days)
        prices = [base_price]
        for i in range(1, n_days):
            prices.append(prices[-1] * (1 + returns[i]))
        
        close_prices = np.array(prices)
        
        for i, date in enumerate(dates):
            # 基于收盘价生成其他价格
            close = close_prices[i]
            high = close * np.random.uniform(1.0, 1.05)
            low = close * np.random.uniform(0.95, 1.0)
            open_price = np.random.uniform(low, high)
            
            # 成交量和成交额
            volume = np.random.uniform(1000000, 10000000)
            amount = volume * close * np.random.uniform(0.9, 1.1)
            
            data.append({
                'date': date,
                'symbol': stock,
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume,
                'amount': amount
            })
    
    return pd.DataFrame(data)

def test_alpha101_phase3_factors():
    """测试Alpha101 Phase3因子 (Alpha041-080中适合A股的因子)"""
    print("🧪 测试Alpha101 Phase3因子...")
    
    try:
        from app.services.alpha101_phase3 import alpha101_phase3_service
        
        # 创建测试数据
        data = create_sample_data(n_days=60, n_stocks=20)
        
        # 获取所有Phase3因子
        available_factors = alpha101_phase3_service.get_available_factors()
        print(f"✅ 找到 {len(available_factors)} 个Phase3因子")
        
        success_count = 0
        error_count = 0
        
        for factor in available_factors[:5]:  # 测试前5个因子
            factor_id = factor['factor_id']
            try:
                result = alpha101_phase3_service.calculate_single_factor(factor_id, data)
                
                if result is not None and not result.empty:
                    non_null_count = result.count()
                    print(f"  ✅ {factor_id} ({factor['display_name']}): {non_null_count} 个有效值")
                    success_count += 1
                else:
                    print(f"  ❌ {factor_id}: 结果为空")
                    error_count += 1
                    
            except Exception as e:
                print(f"  ❌ {factor_id}: 计算失败 - {e}")
                error_count += 1
        
        print(f"Phase3测试结果: {success_count} 成功, {error_count} 失败")
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Phase3因子测试失败: {e}")
        return False

def test_alpha101_phase4_factors():
    """测试Alpha101 Phase4因子 (Alpha061-101中适合A股的因子)"""
    print("\n🧪 测试Alpha101 Phase4因子...")
    
    try:
        from app.services.alpha101_phase4 import alpha101_phase4_service
        
        # 创建测试数据
        data = create_sample_data(n_days=60, n_stocks=20)
        
        # 获取所有Phase4因子
        available_factors = alpha101_phase4_service.get_available_factors()
        print(f"✅ 找到 {len(available_factors)} 个Phase4因子")
        
        success_count = 0
        error_count = 0
        
        for factor in available_factors[:5]:  # 测试前5个因子
            factor_id = factor['factor_id']
            try:
                result = alpha101_phase4_service.calculate_single_factor(factor_id, data)
                
                if result is not None and not result.empty:
                    non_null_count = result.count()
                    print(f"  ✅ {factor_id} ({factor['display_name']}): {non_null_count} 个有效值")
                    success_count += 1
                else:
                    print(f"  ❌ {factor_id}: 结果为空")
                    error_count += 1
                    
            except Exception as e:
                print(f"  ❌ {factor_id}: 计算失败 - {e}")
                error_count += 1
        
        print(f"Phase4测试结果: {success_count} 成功, {error_count} 失败")
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Phase4因子测试失败: {e}")
        return False

def test_builtin_factor_engine_integration():
    """测试内置因子引擎集成"""
    print("\n🧪 测试内置因子引擎集成...")
    
    try:
        from app.services.builtin_factor_engine import BuiltinFactorEngine
        
        # 创建引擎实例
        engine = BuiltinFactorEngine()
        
        # 获取所有因子
        all_factors = engine.list_all_factors()
        
        # 统计各类型因子数量
        category_counts = {}
        for factor in all_factors:
            category = factor.get('category', 'unknown')
            category_counts[category] = category_counts.get(category, 0) + 1
        
        print("📊 因子分类统计:")
        for category, count in category_counts.items():
            print(f"  {category}: {count} 个因子")
        
        # 测试Phase3和Phase4因子
        phase3_factors = [f for f in all_factors if f.get('category') == 'alpha101_phase3']
        phase4_factors = [f for f in all_factors if f.get('category') == 'alpha101_phase4']
        
        print(f"\n✅ Phase3因子: {len(phase3_factors)} 个")
        print(f"✅ Phase4因子: {len(phase4_factors)} 个")
        
        # 测试引擎计算功能
        if phase3_factors:
            test_factor = phase3_factors[0]
            data = create_sample_data(n_days=50, n_stocks=10)
            try:
                result = engine.calculate_factor(test_factor['factor_id'], data)
                print(f"✅ 引擎计算测试成功: {test_factor['factor_id']}")
            except Exception as e:
                print(f"❌ 引擎计算测试失败: {e}")
        
        return len(phase3_factors) > 0 and len(phase4_factors) > 0
        
    except Exception as e:
        print(f"❌ 引擎集成测试失败: {e}")
        return False

def test_alpha101_tools():
    """测试Alpha101Tools工具函数"""
    print("\n🧪 测试Alpha101Tools工具函数...")
    
    try:
        from app.services.alpha101_extended import Alpha101Tools
        
        # 创建测试数据
        tools = Alpha101Tools()
        test_series = pd.Series([1, 2, 3, 4, 5, 4, 3, 2, 1] * 10)
        
        # 测试各种工具函数
        tests = [
            ('rank', lambda: tools.rank(test_series)),
            ('delay', lambda: tools.delay(test_series, 3)),
            ('delta', lambda: tools.delta(test_series, 2)),
            ('ts_rank', lambda: tools.ts_rank(test_series, 5)),
            ('ts_min', lambda: tools.ts_min(test_series, 5)),
            ('ts_max', lambda: tools.ts_max(test_series, 5)),
            ('correlation', lambda: tools.correlation(test_series, test_series * 2, 5)),
            ('decay_linear', lambda: tools.decay_linear(test_series, 5)),
            ('sum_series', lambda: tools.sum_series(test_series, 5)),
            ('stddev', lambda: tools.stddev(test_series, 5)),
        ]
        
        success_count = 0
        for name, test_func in tests:
            try:
                result = test_func()
                if result is not None:
                    print(f"  ✅ {name}: OK")
                    success_count += 1
                else:
                    print(f"  ❌ {name}: 返回None")
            except Exception as e:
                print(f"  ❌ {name}: {e}")
        
        print(f"工具函数测试: {success_count}/{len(tests)} 通过")
        return success_count == len(tests)
        
    except Exception as e:
        print(f"❌ 工具函数测试失败: {e}")
        return False

def test_specific_alpha_factors():
    """测试特定的Alpha因子"""
    print("\n🧪 测试特定Alpha因子...")
    
    try:
        from app.services.alpha101_phase3 import alpha101_phase3_service
        from app.services.alpha101_phase4 import alpha101_phase4_service
        
        # 创建更大的测试数据集
        data = create_sample_data(n_days=100, n_stocks=30)
        
        # 测试一些关键因子
        test_factors = [
            ('041', alpha101_phase3_service, 'Alpha041-几何均价差'),
            ('050', alpha101_phase3_service, 'Alpha050-量价相关性极值'),
            ('061', alpha101_phase4_service, 'Alpha061-VWAP位置相关性'),
            ('101', alpha101_phase4_service, 'Alpha101-日内动量'),
        ]
        
        success_count = 0
        for factor_id, service, description in test_factors:
            try:
                result = service.calculate_single_factor(factor_id, data)
                if result is not None and not result.empty:
                    valid_count = result.count()
                    mean_val = result.mean()
                    std_val = result.std()
                    print(f"  ✅ {factor_id} ({description})")
                    print(f"     有效值: {valid_count}, 均值: {mean_val:.4f}, 标准差: {std_val:.4f}")
                    success_count += 1
                else:
                    print(f"  ❌ {factor_id}: 无有效结果")
            except Exception as e:
                print(f"  ❌ {factor_id}: {e}")
        
        print(f"特定因子测试: {success_count}/{len(test_factors)} 通过")
        return success_count > 0
        
    except Exception as e:
        print(f"❌ 特定因子测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始Alpha101 Phase3 & Phase4 测试")
    print("=" * 50)
    
    # 运行所有测试
    test_results = []
    
    test_results.append(("Alpha101 Tools", test_alpha101_tools()))
    test_results.append(("Phase3 因子", test_alpha101_phase3_factors()))
    test_results.append(("Phase4 因子", test_alpha101_phase4_factors()))
    test_results.append(("引擎集成", test_builtin_factor_engine_integration()))
    test_results.append(("特定因子", test_specific_alpha_factors()))
    
    # 汇总结果
    print("\n" + "=" * 50)
    print("📊 测试结果汇总:")
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🏆 总体结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！Alpha101 Phase3 & Phase4 实现成功！")
        
        # 输出因子统计信息
        try:
            from app.services.alpha101_phase3 import alpha101_phase3_service
            from app.services.alpha101_phase4 import alpha101_phase4_service
            
            phase3_count = len(alpha101_phase3_service.get_available_factors())
            phase4_count = len(alpha101_phase4_service.get_available_factors())
            
            print(f"\n📈 已实现因子统计:")
            print(f"  Phase3 (Alpha041-080筛选): {phase3_count} 个因子")
            print(f"  Phase4 (Alpha061-101筛选): {phase4_count} 个因子")
            print(f"  总计新增: {phase3_count + phase4_count} 个A股适配因子")
            
        except Exception as e:
            print(f"统计信息获取失败: {e}")
    else:
        print("⚠️  部分测试失败，请检查实现")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)