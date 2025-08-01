#!/usr/bin/env python3
"""
API功能测试脚本
"""

import asyncio
import logging
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.api.v1.endpoints.market import get_market_indices, get_stock_quotes
from app.api.v1.endpoints.watchlist import get_watchlist, search_stocks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_market_api():
    """测试市场API"""
    logger.info("测试市场指数API...")
    
    db = SessionLocal()
    try:
        # 测试获取市场指数
        indices = await get_market_indices(db=db)
        logger.info(f"获取到{len(indices)}个市场指数")
        for index in indices:
            logger.info(f"  {index.name}: {index.price} ({index.changePercent:+.2f}%)")
        
        # 测试获取股票行情
        quotes = await get_stock_quotes("000001.SZ,600036.SH", db=db)
        logger.info(f"获取到{len(quotes)}只股票行情")
        for quote in quotes:
            logger.info(f"  {quote.name}({quote.symbol}): {quote.price} ({quote.changePercent:+.2f}%)")
        
    except Exception as e:
        logger.error(f"市场API测试失败: {e}")
    finally:
        db.close()


async def test_watchlist_api():
    """测试自选股API"""
    logger.info("测试自选股API...")
    
    db = SessionLocal()
    try:
        # 测试获取自选股列表
        watchlist = await get_watchlist(db=db)
        logger.info(f"获取到{len(watchlist)}只自选股")
        for item in watchlist:
            logger.info(f"  {item.name}({item.symbol}): {item.notes}")
        
        # 测试股票搜索
        search_results = await search_stocks("银行", db=db)
        logger.info(f"搜索'银行'得到{len(search_results)}个结果")
        for result in search_results:
            logger.info(f"  {result.name}({result.symbol}): {result.industry}")
        
    except Exception as e:
        logger.error(f"自选股API测试失败: {e}")
    finally:
        db.close()


async def main():
    """主测试函数"""
    logger.info("开始API功能测试...")
    
    try:
        await test_market_api()
        await test_watchlist_api()
        logger.info("所有API测试完成！")
    except Exception as e:
        logger.error(f"测试失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())