"""
统一数据服务使用示例
演示如何使用UnifiedDataService获取不同类型的数据
"""

import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.services.unified_data_service import (
    UnifiedDataService, 
    DataType, 
    CacheStrategy
)
from app.db.database import SessionLocal

logger = logging.getLogger(__name__)


async def example_usage():
    """使用示例"""
    
    # 创建数据服务实例
    data_service = UnifiedDataService()
    db = SessionLocal()
    
    try:
        # 示例1: 获取股票基础信息（智能缓存）
        logger.info("=== 获取股票基础信息 ===")
        stock_basic_data = await data_service.get_data(
            data_type=DataType.STOCK_BASIC,
            cache_strategy=CacheStrategy.SMART_CACHE,
            db=db
        )
        logger.info(f"获取到 {len(stock_basic_data)} 只股票的基础信息")
        
        # 示例2: 获取特定股票的日线数据
        logger.info("=== 获取股票日线数据 ===")
        symbols = ['000001.SZ', '600036.SH']
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        
        daily_data = await data_service.get_data(
            data_type=DataType.STOCK_DAILY,
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            cache_strategy=CacheStrategy.SMART_CACHE,
            db=db
        )
        logger.info(f"获取到 {len(daily_data)} 条日线数据")
        
        # 示例3: 获取市场指数数据（API优先）
        logger.info("=== 获取市场指数数据 ===")
        index_data = await data_service.get_data(
            data_type=DataType.MARKET_INDEX,
            start_date=start_date,
            end_date=end_date,
            cache_strategy=CacheStrategy.API_FIRST,
            db=db
        )
        logger.info(f"获取到 {len(index_data)} 条指数数据")
        
        # 示例4: 查看缓存统计
        logger.info("=== 缓存统计 ===")
        cache_stats = data_service.get_cache_stats()
        logger.info(f"内存缓存大小: {cache_stats['memory_cache_size']}")
        logger.info(f"缓存键: {cache_stats['cache_keys']}")
        
        # 示例5: 清理缓存
        logger.info("=== 清理缓存 ===")
        data_service.clear_memory_cache(DataType.STOCK_DAILY)
        logger.info("已清理股票日线数据的内存缓存")
        
    except Exception as e:
        logger.error(f"示例执行失败: {e}")
    finally:
        db.close()


async def performance_test():
    """性能测试"""
    logger.info("=== 性能测试 ===")
    
    data_service = UnifiedDataService()
    db = SessionLocal()
    
    try:
        # 测试不同缓存策略的性能
        symbols = ['000001.SZ']
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
        
        # 测试1: 无缓存策略
        start_time = datetime.now()
        await data_service.get_data(
            data_type=DataType.STOCK_DAILY,
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            cache_strategy=CacheStrategy.NO_CACHE,
            db=db
        )
        no_cache_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"无缓存策略耗时: {no_cache_time:.2f}秒")
        
        # 测试2: 智能缓存策略（第二次调用应该更快）
        start_time = datetime.now()
        await data_service.get_data(
            data_type=DataType.STOCK_DAILY,
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            cache_strategy=CacheStrategy.SMART_CACHE,
            db=db
        )
        smart_cache_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"智能缓存策略耗时: {smart_cache_time:.2f}秒")
        
        # 测试3: 缓存优先策略
        start_time = datetime.now()
        await data_service.get_data(
            data_type=DataType.STOCK_DAILY,
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            cache_strategy=CacheStrategy.CACHE_FIRST,
            db=db
        )
        cache_first_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"缓存优先策略耗时: {cache_first_time:.2f}秒")
        
    except Exception as e:
        logger.error(f"性能测试失败: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行示例
    asyncio.run(example_usage())
    
    # 运行性能测试
    asyncio.run(performance_test()) 