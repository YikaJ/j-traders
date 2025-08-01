#!/usr/bin/env python3
"""
股票数据同步调试脚本
帮助诊断数据同步问题
"""

import requests
import json
import time

def debug_stock_sync():
    """调试股票数据同步问题"""
    base_url = "http://localhost:8001"
    
    print("🔍 股票数据同步调试工具")
    print("=" * 50)
    
    # 1. 检查同步前的状态
    print("\n📊 步骤1: 检查同步前状态")
    try:
        response = requests.get(f"{base_url}/api/v1/stocks/sync/info")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 同步前股票总数: {data['stock_count']['total']}")
            print(f"✅ 活跃股票: {data['stock_count']['active']}")
            print(f"✅ 上交所: {data['stock_count']['sh_market']}")
            print(f"✅ 深交所: {data['stock_count']['sz_market']}")
            print(f"✅ 最后同步: {data.get('last_sync_time', 'N/A')}")
            before_total = data['stock_count']['total']
        else:
            print(f"❌ 获取同步信息失败: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return
    
    # 2. 执行同步
    print("\n🔄 步骤2: 执行数据同步")
    try:
        print("⏳ 正在同步数据...")
        response = requests.post(f"{base_url}/api/v1/stocks/sync")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 同步成功: {data['message']}")
            print(f"✅ 获取数量: {data['total_fetched']}")
            print(f"✅ 新增股票: {data['new_stocks']}")
            print(f"✅ 更新股票: {data['updated_stocks']}")
            print(f"✅ 错误数量: {data['errors']}")
            print(f"✅ 耗时: {data['duration']}秒")
            
            sync_result = data
        else:
            print(f"❌ 同步失败: {response.status_code}")
            print(f"❌ 响应: {response.text}")
            return
    except Exception as e:
        print(f"❌ 同步请求失败: {e}")
        return
    
    # 3. 立即检查同步后状态
    print("\n📊 步骤3: 检查同步后状态（立即）")
    try:
        # 添加时间戳防止缓存
        params = {"_t": int(time.time())}
        response = requests.get(f"{base_url}/api/v1/stocks/sync/info", params=params)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 同步后股票总数: {data['stock_count']['total']}")
            print(f"✅ 活跃股票: {data['stock_count']['active']}")
            print(f"✅ 上交所: {data['stock_count']['sh_market']}")
            print(f"✅ 深交所: {data['stock_count']['sz_market']}")
            print(f"✅ 最后同步: {data.get('last_sync_time', 'N/A')}")
            
            after_total = data['stock_count']['total']
            
            # 比较数据变化
            if after_total != before_total:
                print(f"✅ 数据已更新: {before_total} → {after_total} (+{after_total - before_total})")
            else:
                print(f"⚠️  数据未变化: 仍为 {after_total}")
        else:
            print(f"❌ 获取同步后信息失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    # 4. 等待后再次检查
    print("\n⏳ 步骤4: 等待3秒后再次检查")
    time.sleep(3)
    
    try:
        params = {"_t": int(time.time())}
        response = requests.get(f"{base_url}/api/v1/stocks/sync/info", params=params)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 延迟检查股票总数: {data['stock_count']['total']}")
            print(f"✅ 活跃股票: {data['stock_count']['active']}")
            print(f"✅ 最后同步: {data.get('last_sync_time', 'N/A')}")
            
            final_total = data['stock_count']['total']
            if final_total != before_total:
                print(f"✅ 最终数据更新: {before_total} → {final_total}")
            else:
                print(f"⚠️  最终数据仍未变化: {final_total}")
        else:
            print(f"❌ 延迟检查失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 延迟检查请求失败: {e}")
    
    # 5. 检查数据库连接和统计API
    print("\n📈 步骤5: 检查统计API")
    try:
        params = {"_t": int(time.time())}
        response = requests.get(f"{base_url}/api/v1/stocks/stats", params=params)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 统计API - 总股票数: {data['total_stocks']}")
            print(f"✅ 统计API - 活跃股票: {data['active_stocks']}")
            print(f"✅ 统计API - 上交所: {data['sh_market_stocks']}")
            print(f"✅ 统计API - 深交所: {data['sz_market_stocks']}")
            print(f"✅ 统计时间: {data['timestamp']}")
        else:
            print(f"❌ 统计API失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 统计API请求失败: {e}")
    
    # 6. 测试搜索功能
    print("\n🔍 步骤6: 测试搜索功能")
    try:
        response = requests.get(f"{base_url}/api/v1/stocks/search", params={"q": "000001"})
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 搜索结果数量: {len(data)}")
            if data:
                print(f"✅ 搜索示例: {data[0]['symbol']} - {data[0]['name']}")
        else:
            print(f"❌ 搜索API失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 搜索API请求失败: {e}")
    
    print("\n" + "=" * 50)
    print("🔍 调试总结")
    print("=" * 50)
    
    print("\n💡 可能的问题和解决方案:")
    print("1. 如果数据未更新:")
    print("   - 检查是否使用了正确的后端服务器")
    print("   - 确认数据库连接正常")
    print("   - 检查Tushare Token配置")
    
    print("\n2. 如果前端显示不正确:")
    print("   - 清除浏览器缓存")
    print("   - 检查前端API调用是否有缓存")
    print("   - 手动点击'刷新数据'按钮")
    
    print("\n3. 如果同步很慢:")
    print("   - 这是正常的，5000+股票需要时间处理")
    print("   - 检查网络连接和API限制")
    print("   - 等待同步完全完成后再检查")
    
    print("\n🔗 有用的链接:")
    print("  - 前端: http://localhost:3000")
    print("  - 后端API: http://localhost:8001")
    print("  - API文档: http://localhost:8001/docs")

if __name__ == "__main__":
    debug_stock_sync()