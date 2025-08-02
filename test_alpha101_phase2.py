#!/usr/bin/env python3
"""
Alpha101 Phase2 因子测试脚本
测试新实现的Alpha031-040因子
"""

import sys
import os
import numpy as np
import pandas as pd

# 添加项目路径
sys.path.append('/workspace/backend')

def create_sample_data(n_days=100):
    """创建样本数据用于测试"""
    dates = pd.date_range('2023-01-01', periods=n_days, freq='D')
    
    # 生成随机价格数据
    np.random.seed(42)
    base_price = 100
    
    # 模拟股价走势
    returns = np.random.normal(0.001, 0.02, n_days)  # 日收益率
    prices = base_price * np.cumprod(1 + returns)
    
    # 创建OHLC数据
    highs = prices * (1 + np.abs(np.random.normal(0, 0.01, n_days)))
    lows = prices * (1 - np.abs(np.random.normal(0, 0.01, n_days)))
    
    # 成交量数据
    volumes = np.random.lognormal(10, 0.5, n_days)
    amounts = volumes * prices
    
    data = pd.DataFrame({
        'date': dates,
        'open': prices,
        'high': highs,
        'low': lows,
        'close': prices,
        'volume': volumes,
        'amount': amounts
    })
    
    return data

def test_alpha101_phase2_factors():
    """测试Alpha101 Phase2因子"""
    print("=" * 60)
    print("Alpha101 Phase2 因子测试")
    print("=" * 60)
    
    try:
        # 导入服务
        from app.services.alpha101_phase2 import alpha101_phase2_service
        
        # 创建测试数据
        data = create_sample_data(250)  # 250日数据，满足长期因子需求
        print(f"✓ 成功创建 {len(data)} 日测试数据")
        
        # 获取所有Phase2因子
        factors = alpha101_phase2_service.get_all_factors()
        print(f"✓ 发现 {len(factors)} 个Alpha101 Phase2因子")
        
        print("\n可用因子列表:")
        for factor_id, factor_info in factors.items():
            print(f"  - {factor_id}: {factor_info['display_name']}")
        
        # 测试几个关键因子
        test_factors = ['alpha101_031', 'alpha101_032', 'alpha101_033', 'alpha101_035']
        
        print(f"\n开始测试因子计算...")
        for factor_id in test_factors:
            if factor_id in factors:
                try:
                    result = alpha101_phase2_service.calculate_factor(factor_id, data)
                    valid_values = result.dropna()
                    
                    print(f"  ✓ {factor_id}: 计算成功")
                    print(f"    - 有效值: {len(valid_values)}/{len(result)}")
                    print(f"    - 值范围: [{valid_values.min():.4f}, {valid_values.max():.4f}]")
                    print(f"    - 均值: {valid_values.mean():.4f}")
                    
                except Exception as e:
                    print(f"  ✗ {factor_id}: 计算失败 - {e}")
            else:
                print(f"  ? {factor_id}: 因子不存在")
                
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

def test_builtin_factor_engine_integration():
    """测试内置因子引擎集成"""
    print("\n" + "=" * 60)
    print("内置因子引擎集成测试")
    print("=" * 60)
    
    try:
        # 导入内置因子引擎
        from app.services.builtin_factor_engine import builtin_factor_engine
        
        # 获取所有因子
        all_factors = builtin_factor_engine.list_all_factors()
        print(f"✓ 内置因子引擎中共有 {len(all_factors)} 个因子")
        
        # 统计各类别因子数量
        category_counts = {}
        for factor in all_factors:
            category = factor.get('category', 'unknown')
            category_counts[category] = category_counts.get(category, 0) + 1
        
        print("\n因子分类统计:")
        for category, count in category_counts.items():
            print(f"  - {category}: {count} 个因子")
        
        # 检查Alpha101 Phase2因子是否成功注册
        phase2_factors = [f for f in all_factors if f.get('category') == 'alpha101_phase2']
        print(f"\n✓ Alpha101 Phase2 因子已注册: {len(phase2_factors)} 个")
        
        # 测试通过引擎计算因子
        data = create_sample_data(150)
        
        if phase2_factors:
            test_factor = phase2_factors[0]
            factor_id = test_factor['factor_id']
            
            try:
                result = builtin_factor_engine.calculate_single_factor(factor_id, data)
                print(f"✓ 通过内置因子引擎成功计算 {factor_id}")
                print(f"  - 结果长度: {len(result)}")
                print(f"  - 有效值: {len(result.dropna())}")
                
            except Exception as e:
                print(f"✗ 通过内置因子引擎计算失败: {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ 集成测试失败: {e}")
        return False

def test_alpha101_tools():
    """测试Alpha101计算工具"""
    print("\n" + "=" * 60)
    print("Alpha101 计算工具测试")
    print("=" * 60)
    
    try:
        from app.services.alpha101_extended import Alpha101Tools
        
        # 创建测试数据
        data = create_sample_data(50)
        test_series = data['close']
        
        print("测试基础计算函数:")
        
        # 测试rank函数
        rank_result = Alpha101Tools.rank(test_series)
        print(f"  ✓ rank: 值范围 [{rank_result.min():.4f}, {rank_result.max():.4f}]")
        
        # 测试delta函数
        delta_result = Alpha101Tools.delta(test_series, 5)
        print(f"  ✓ delta(5): 有效值 {len(delta_result.dropna())}/{len(delta_result)}")
        
        # 测试correlation函数
        corr_result = Alpha101Tools.correlation(data['close'], data['volume'], 10)
        print(f"  ✓ correlation(10): 有效值 {len(corr_result.dropna())}/{len(corr_result)}")
        
        # 测试ts_rank函数
        ts_rank_result = Alpha101Tools.ts_rank(test_series, 10)
        print(f"  ✓ ts_rank(10): 有效值 {len(ts_rank_result.dropna())}/{len(ts_rank_result)}")
        
        # 测试decay_linear函数
        decay_result = Alpha101Tools.decay_linear(test_series, 10)
        print(f"  ✓ decay_linear(10): 有效值 {len(decay_result.dropna())}/{len(decay_result)}")
        
        return True
        
    except Exception as e:
        print(f"✗ 工具测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("Alpha101 Phase2 扩展因子库测试")
    print("测试时间:", pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    # 运行所有测试
    test_results = []
    
    test_results.append(test_alpha101_tools())
    test_results.append(test_alpha101_phase2_factors())
    test_results.append(test_builtin_factor_engine_integration())
    
    # 总结测试结果
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"总测试: {total}")
    print(f"通过: {passed}")
    print(f"失败: {total - passed}")
    
    if passed == total:
        print("🎉 所有测试通过!")
        return True
    else:
        print("❌ 部分测试失败，请检查日志")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)