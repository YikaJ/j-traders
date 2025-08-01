#!/usr/bin/env python3
"""
测试 Tushare 集成
验证所有接口都能正确使用 Tushare 数据
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import get_db
from app.services.tushare_service import tushare_service
from app.api.v1.endpoints.market import get_market_indices, get_stock_quotes, get_stock_history
from app.api.v1.endpoints.watchlist import search_stocks
from app.services.strategy_service import StrategyService
from app.services.factor_service import FactorService
from app.services.stock_sync_service import StockSyncService


async def test_tushare_service():
    """测试 Tushare 服务"""
    print("=== 测试 Tushare 服务 ===")
    
    try:
        # 测试获取股票列表
        print("1. 测试获取股票列表...")
        stock_df = await tushare_service.get_stock_list()
        print(f"   获取到 {len(stock_df)} 只股票")
        
        # 测试获取市场指数
        print("2. 测试获取市场指数...")
        indices_df = await tushare_service.get_market_indices()
        print(f"   获取到 {len(indices_df)} 个指数")
        if not indices_df.empty:
            for _, row in indices_df.iterrows():
                print(f"   {row.get('ts_code', '')}: {row.get('close', 0)}")
        
        # 测试获取实时行情
        print("3. 测试获取实时行情...")
        quotes_df = await tushare_service.get_realtime_quotes(['000001.SZ', '600036.SH'])
        print(f"   获取到 {len(quotes_df)} 只股票的实时行情")
        
        # 测试搜索股票
        print("4. 测试搜索股票...")
        search_results = await tushare_service.search_stocks('茅台', 5)
        print(f"   搜索到 {len(search_results)} 只股票")
        for result in search_results:
            print(f"   {result['symbol']}: {result['name']}")
        
        print("✓ Tushare 服务测试通过")
        
    except Exception as e:
        print(f"✗ Tushare 服务测试失败: {e}")
        return False
    
    return True


async def test_market_endpoints():
    """测试市场数据接口"""
    print("\n=== 测试市场数据接口 ===")
    
    try:
        db = next(get_db())
        
        # 测试获取市场指数
        print("1. 测试 /market/indices 接口...")
        indices = await get_market_indices(db=db)
        print(f"   获取到 {len(indices)} 个指数")
        for index in indices:
            print(f"   {index.symbol}: {index.name} - {index.price}")
        
        # 测试获取股票行情
        print("2. 测试 /market/quotes 接口...")
        quotes = await get_stock_quotes("000001.SZ,600036.SH", db=db)
        print(f"   获取到 {len(quotes)} 只股票的行情")
        for quote in quotes:
            print(f"   {quote.symbol}: {quote.name} - {quote.price}")
        
        # 测试获取历史数据
        print("3. 测试 /market/history/{symbol} 接口...")
        history = await get_stock_history("000001.SZ", 10, db=db)
        print(f"   获取到 {len(history['data'])} 天的历史数据")
        
        print("✓ 市场数据接口测试通过")
        
    except Exception as e:
        print(f"✗ 市场数据接口测试失败: {e}")
        return False
    
    return True


async def test_watchlist_endpoints():
    """测试自选股接口"""
    print("\n=== 测试自选股接口 ===")
    
    try:
        db = next(get_db())
        
        # 测试搜索股票
        print("1. 测试 /watchlist/search 接口...")
        search_results = await search_stocks("茅台", 5, db=db)
        print(f"   搜索到 {len(search_results)} 只股票")
        for result in search_results:
            print(f"   {result.symbol}: {result.name}")
        
        print("✓ 自选股接口测试通过")
        
    except Exception as e:
        print(f"✗ 自选股接口测试失败: {e}")
        return False
    
    return True


async def test_services():
    """测试服务层"""
    print("\n=== 测试服务层 ===")
    
    try:
        db = next(get_db())
        
        # 测试股票同步服务
        print("1. 测试股票同步服务...")
        sync_service = StockSyncService()
        stock_count = await sync_service.get_stock_count(db)
        print(f"   数据库中有 {stock_count['total']} 只股票，{stock_count['active']} 只活跃")
        
        # 测试因子服务
        print("2. 测试因子服务...")
        factor_service = FactorService()
        
        # 简单的因子代码
        factor_code = """
import pandas as pd
import numpy as np

def calculate(data):
    # 计算收益率
    if len(data) < 2:
        return 0.0
    returns = data['close'].pct_change()
    return returns.mean() * 100
"""
        
        validation = await factor_service.validate_factor_code(factor_code)
        print(f"   因子代码验证: {'通过' if validation.is_valid else '失败'}")
        
        print("✓ 服务层测试通过")
        
    except Exception as e:
        print(f"✗ 服务层测试失败: {e}")
        return False
    
    return True


async def main():
    """主测试函数"""
    print("开始测试 Tushare 集成...")
    print("=" * 50)
    
    results = []
    
    # 测试 Tushare 服务
    results.append(await test_tushare_service())
    
    # 测试市场数据接口
    results.append(await test_market_endpoints())
    
    # 测试自选股接口
    results.append(await test_watchlist_endpoints())
    
    # 测试服务层
    results.append(await test_services())
    
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    
    test_names = [
        "Tushare 服务",
        "市场数据接口", 
        "自选股接口",
        "服务层"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{i+1}. {name}: {status}")
    
    all_passed = all(results)
    print(f"\n总体结果: {'✓ 所有测试通过' if all_passed else '✗ 部分测试失败'}")
    
    return all_passed


if __name__ == "__main__":
    asyncio.run(main()) 