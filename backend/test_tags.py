#!/usr/bin/env python3
"""
测试因子标签功能
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_factor_tags():
    """测试因子标签相关功能"""
    
    print("=== 测试因子标签功能 ===\n")
    
    # 1. 创建标签
    print("1. 创建标签...")
    tag_data = {
        "name": "momentum_test",
        "display_name": "动量类测试",
        "description": "基于价格动量的因子标签测试",
        "color": "#3B82F6"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/factors/tags/", json=tag_data)
        if response.status_code == 200:
            tag = response.json()
            print(f"✓ 标签创建成功: {tag['display_name']} (ID: {tag['id']})")
            tag_id = tag['id']
        else:
            print(f"✗ 标签创建失败: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"✗ 请求失败: {e}")
        return
    
    # 2. 获取所有标签
    print("\n2. 获取所有标签...")
    try:
        response = requests.get(f"{BASE_URL}/factors/tags/")
        if response.status_code == 200:
            tags = response.json()
            print(f"✓ 获取到 {len(tags)} 个标签:")
            for tag in tags:
                print(f"  - {tag['display_name']} ({tag['name']})")
        else:
            print(f"✗ 获取标签失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"✗ 请求失败: {e}")
    
    # 3. 创建测试因子
    print("\n3. 创建测试因子...")
    factor_data = {
        "name": "test_momentum_factor",
        "display_name": "测试动量因子",
        "description": "这是一个测试动量因子",
        "tags": ["momentum"],
        "code": "def calculate(data):\n    return data['close'].pct_change()",
        "input_fields": ["close"],
        "default_parameters": {},
        "calculation_method": "formula"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/factors/", json=factor_data)
        if response.status_code == 200:
            factor = response.json()
            print(f"✓ 因子创建成功: {factor['display_name']} (ID: {factor['id']})")
            factor_id = factor['id']
        else:
            print(f"✗ 因子创建失败: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"✗ 请求失败: {e}")
        return
    
    # 4. 为因子添加标签
    print("\n4. 为因子添加标签...")
    relation_data = {
        "factor_id": factor_id,
        "tag_ids": [tag_id]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/factors/tags/relations/", json=relation_data)
        if response.status_code == 200:
            relation = response.json()
            print(f"✓ 标签关联创建成功")
            print(f"  因子ID: {relation['factor_id']}")
            print(f"  标签数量: {len(relation['tags'])}")
        else:
            print(f"✗ 标签关联创建失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"✗ 请求失败: {e}")
    
    # 5. 获取因子的标签
    print("\n5. 获取因子的标签...")
    try:
        response = requests.get(f"{BASE_URL}/factors/{factor_id}/tags/")
        if response.status_code == 200:
            tags = response.json()
            print(f"✓ 因子标签获取成功:")
            for tag in tags:
                print(f"  - {tag['display_name']} ({tag['name']})")
        else:
            print(f"✗ 获取因子标签失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"✗ 请求失败: {e}")
    
    # 6. 获取带标签的因子列表
    print("\n6. 获取带标签的因子列表...")
    try:
        response = requests.get(f"{BASE_URL}/factors/")
        if response.status_code == 200:
            factors = response.json()
            print(f"✓ 获取到 {len(factors)} 个因子:")
            for factor in factors:
                tags_text = ', '.join([tag['display_name'] for tag in factor.get('tags', [])]) if factor.get('tags') else '无'
                print(f"  - {factor['display_name']} (标签: {tags_text})")
                if factor.get('tags'):
                    print(f"    标签: {', '.join([tag['display_name'] for tag in factor['tags']])}")
                else:
                    print(f"    标签: 无")
        else:
            print(f"✗ 获取因子列表失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"✗ 请求失败: {e}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_factor_tags() 