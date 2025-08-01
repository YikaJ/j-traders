#!/usr/bin/env python3
"""
前后端集成测试脚本
"""

import requests
import json
import time

def test_backend_apis():
    """测试后端API接口"""
    base_url = "http://localhost:8001"
    
    print("🚀 测试后端API接口...")
    
    # 测试健康检查
    try:
        response = requests.get(f"{base_url}/health")
        print(f"✅ 健康检查: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return False
    
    # 测试API v1
    try:
        response = requests.get(f"{base_url}/api/v1/test")
        print(f"✅ API测试: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ API测试失败: {e}")
        return False
    
    # 测试市场指数
    try:
        response = requests.get(f"{base_url}/api/v1/market/indices")
        data = response.json()
        print(f"✅ 市场指数: {response.status_code} - 获取到 {len(data)} 个指数")
        if data:
            print(f"   示例: {data[0]['name']} - {data[0]['price']:.2f}")
    except Exception as e:
        print(f"❌ 市场指数API失败: {e}")
        return False
    
    # 测试因子管理
    try:
        response = requests.get(f"{base_url}/api/v1/factors")
        data = response.json()
        print(f"✅ 因子列表: {response.status_code} - 获取到 {len(data)} 个因子")
        if data:
            print(f"   示例: {data[0]['name']} - {data[0]['category']}")
    except Exception as e:
        print(f"❌ 因子API失败: {e}")
        return False
    
    # 测试自选股
    try:
        response = requests.get(f"{base_url}/api/v1/watchlist")
        data = response.json()
        print(f"✅ 自选股列表: {response.status_code} - 获取到 {len(data)} 只股票")
        if data:
            print(f"   示例: {data[0]['name']} - {data[0]['price']:.2f}")
    except Exception as e:
        print(f"❌ 自选股API失败: {e}")
        return False
    
    # 测试策略执行
    try:
        payload = {"factors": ["1", "2"], "maxResults": 5}
        response = requests.post(f"{base_url}/api/v1/strategies/execute", json=payload)
        data = response.json()
        print(f"✅ 策略执行: {response.status_code} - 选出 {len(data)} 只股票")
        if data:
            print(f"   第一名: {data[0]['name']} - 得分: {data[0]['score']:.3f}")
    except Exception as e:
        print(f"❌ 策略执行API失败: {e}")
        return False
    
    print("🎉 所有后端API测试通过！")
    return True

def test_frontend():
    """测试前端服务器"""
    print("\n🌐 测试前端服务器...")
    
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print(f"✅ 前端服务器: {response.status_code} - 正常运行")
            return True
        else:
            print(f"❌ 前端服务器响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 前端服务器连接失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 50)
    print("🧪 量化选股系统 - 前后端集成测试")
    print("=" * 50)
    
    # 等待服务器启动
    print("⏳ 等待服务器启动...")
    time.sleep(3)
    
    backend_ok = test_backend_apis()
    frontend_ok = test_frontend()
    
    print("\n" + "=" * 50)
    if backend_ok and frontend_ok:
        print("🎊 集成测试全部通过！前后端已成功对接真实数据。")
        print("📱 前端地址: http://localhost:3000")
        print("🔗 后端API: http://localhost:8001")
        print("📚 API文档: http://localhost:8001/docs")
    else:
        print("⚠️  部分测试失败，请检查服务器状态。")
    print("=" * 50)

if __name__ == "__main__":
    main()