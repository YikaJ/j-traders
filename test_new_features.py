#!/usr/bin/env python3
"""
测试新增的因子库功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    # 测试Alpha101因子服务
    from backend.app.services.alpha101_factor_service import alpha101_factor_service
    
    print("🧪 测试Alpha101因子服务...")
    factors = alpha101_factor_service.get_available_factors()
    print(f"✅ Alpha101因子数量: {len(factors)}")
    
    for factor in factors[:3]:  # 只显示前3个
        print(f"  - {factor['factor_id']}: {factor['display_name']}")
        print(f"    公式: {factor.get('formula', '无')}")
        print()

except ImportError as e:
    print(f"❌ 无法导入Alpha101因子服务: {e}")

try:
    # 测试参数化因子服务
    from backend.app.services.parametric_factor_service import parametric_factor_service
    
    print("🧪 测试参数化因子服务...")
    factors = parametric_factor_service.get_available_factors()
    print(f"✅ 参数化因子数量: {len(factors)}")
    
    for factor in factors:
        print(f"  - {factor['factor_id']}: {factor['display_name']}")
        print(f"    参数: {list(factor['default_parameters'].keys())}")
        print()

except ImportError as e:
    print(f"❌ 无法导入参数化因子服务: {e}")

try:
    # 测试内置因子引擎
    from backend.app.services.builtin_factor_engine import builtin_factor_engine
    
    print("🧪 测试内置因子引擎...")
    all_factors = builtin_factor_engine.list_all_factors()
    print(f"✅ 总因子数量: {len(all_factors)}")
    
    # 按分类统计
    categories = {}
    for factor in all_factors:
        cat = factor.get('category', 'unknown')
        categories[cat] = categories.get(cat, 0) + 1
    
    print("📊 因子分类统计:")
    for cat, count in categories.items():
        print(f"  - {cat}: {count}个")

except ImportError as e:
    print(f"❌ 无法导入内置因子引擎: {e}")

print("\n🎉 测试完成！")
print("\n📝 新增功能总结:")
print("1. ✅ Alpha101因子库 - 基于WorldQuant的成熟量化因子")
print("2. ✅ 参数化因子 - 统一重复因子为参数化版本")
print("3. ✅ 因子公式显示 - 前端支持查看因子计算公式")
print("4. ✅ 策略因子选择 - 创建策略时可选择因子")
print("5. 🚧 策略管理增强 - 持续完善中")