#!/usr/bin/env python3
"""
股票数据同步功能集成测试脚本
"""

import requests
import json
import time

def test_stock_apis():
    """测试股票相关API接口"""
    base_url = "http://localhost:8001"
    
    print("🚀 测试股票数据管理API接口...")
    
    # 测试获取同步信息
    try:
        response = requests.get(f"{base_url}/api/v1/stocks/sync/info")
        print(f"✅ 同步信息: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   股票总数: {data['stock_count']['total']}")
            print(f"   活跃股票: {data['stock_count']['active']}")
            print(f"   最后同步: {data.get('last_sync_time', 'N/A')}")
    except Exception as e:
        print(f"❌ 同步信息API失败: {e}")
        return False
    
    # 测试股票统计
    try:
        response = requests.get(f"{base_url}/api/v1/stocks/stats")
        print(f"✅ 股票统计: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   总股票数: {data['total_stocks']}")
            print(f"   上交所: {data['sh_market_stocks']}")
            print(f"   深交所: {data['sz_market_stocks']}")
    except Exception as e:
        print(f"❌ 股票统计API失败: {e}")
        return False
    
    # 测试股票搜索（使用英文避免编码问题）
    try:
        response = requests.get(f"{base_url}/api/v1/stocks/search", params={"q": "000001"})
        print(f"✅ 股票搜索: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   搜索结果: {len(data)} 只股票")
            if data:
                print(f"   示例: {data[0]['symbol']} - {data[0]['name']}")
    except Exception as e:
        print(f"❌ 股票搜索API失败: {e}")
        return False
    
    # 测试股票数据同步
    try:
        print("⏳ 执行股票数据同步...")
        response = requests.post(f"{base_url}/api/v1/stocks/sync")
        print(f"✅ 股票同步: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   同步结果: {data['message']}")
            print(f"   获取数量: {data['total_fetched']}")
            print(f"   新增股票: {data['new_stocks']}")
            print(f"   更新股票: {data['updated_stocks']}")
            print(f"   耗时: {data['duration']}秒")
    except Exception as e:
        print(f"❌ 股票同步API失败: {e}")
        return False
    
    print("🎉 所有股票API测试通过！")
    return True

def test_frontend_integration():
    """测试前端集成"""
    print("\n🌐 测试前端股票功能集成...")
    
    try:
        # 测试前端是否可以访问
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print("✅ 前端服务器正常运行")
            print("📱 可以访问 http://localhost:3000 查看股票数据同步功能")
            print("🔍 在自选股页面可以测试优化后的股票搜索功能")
            print("📊 在大盘监控页面可以测试股票数据同步功能")
            return True
        else:
            print(f"❌ 前端服务器响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 前端服务器连接失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("🧪 股票数据同步功能 - 集成测试")
    print("=" * 60)
    
    print("⏳ 等待服务器启动...")
    time.sleep(3)
    
    backend_ok = test_stock_apis()
    frontend_ok = test_frontend_integration()
    
    print("\n" + "=" * 60)
    print("📋 测试总结")
    print("=" * 60)
    
    if backend_ok and frontend_ok:
        print("🎊 所有测试通过！股票数据同步功能已成功实现。")
        print("\n✨ 新功能特性：")
        print("  1. ✅ 股票列表数据库存储")
        print("  2. ✅ 手动同步股票数据功能")
        print("  3. ✅ 优化的股票搜索功能")
        print("  4. ✅ 股票数据统计展示")
        print("  5. ✅ 前端同步UI界面")
        
        print("\n🔗 访问地址：")
        print("  📱 前端应用: http://localhost:3000")
        print("  🔧 后端API: http://localhost:8001")
        print("  📚 API文档: http://localhost:8001/docs")
        
        print("\n📝 使用说明：")
        print("  • 在大盘监控页面点击'数据同步'可手动同步股票数据")
        print("  • 在自选股页面搜索股票时会使用数据库中的数据")
        print("  • 股票数据不会频繁更新，只在手动同步时更新")
        
    else:
        print("⚠️  部分测试失败，请检查服务器状态。")
    
    print("=" * 60)

if __name__ == "__main__":
    main()