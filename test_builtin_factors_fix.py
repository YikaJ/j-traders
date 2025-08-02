#!/usr/bin/env python3
"""
测试内置因子API修复
"""

import requests
import json

def test_builtin_factors_api():
    """测试内置因子API"""
    base_url = "http://localhost:8000"
    
    print("测试内置因子API...")
    
    # 测试获取所有因子
    try:
        response = requests.get(f"{base_url}/api/v1/builtin-factors/")
        print(f"获取所有因子 - 状态码: {response.status_code}")
        if response.status_code == 200:
            factors = response.json()
            print(f"成功获取 {len(factors)} 个因子")
            
            # 检查是否有alpha101_extended分类的因子
            alpha101_extended_factors = [f for f in factors if f.get('category') == 'alpha101_extended']
            print(f"找到 {len(alpha101_extended_factors)} 个alpha101_extended分类的因子")
            
            if alpha101_extended_factors:
                print("示例因子:")
                for factor in alpha101_extended_factors[:3]:
                    print(f"  - {factor.get('display_name')} ({factor.get('factor_id')})")
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 测试按分类获取因子
    try:
        response = requests.get(f"{base_url}/api/v1/builtin-factors/?category=alpha101_extended")
        print(f"\n按分类获取因子 - 状态码: {response.status_code}")
        if response.status_code == 200:
            factors = response.json()
            print(f"成功获取 {len(factors)} 个alpha101_extended分类的因子")
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 测试获取分类列表
    try:
        response = requests.get(f"{base_url}/api/v1/builtin-factors/categories")
        print(f"\n获取分类列表 - 状态码: {response.status_code}")
        if response.status_code == 200:
            categories = response.json()
            print(f"可用分类: {categories}")
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == "__main__":
    test_builtin_factors_api() 