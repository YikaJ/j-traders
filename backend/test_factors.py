#!/usr/bin/env python3
"""
因子API功能测试脚本
"""

import asyncio
import logging
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.api.v1.endpoints.factors import (
    get_factors, 
    create_factor, 
    test_factor,
    get_factor_categories
)
from app.schemas.factors import FactorCreate, FactorTestRequest
from app.services.factor_service import factor_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_factor_management():
    """测试因子管理功能"""
    logger.info("测试因子管理API...")
    
    db = SessionLocal()
    try:
        # 测试获取因子列表
        factors = await get_factors(db=db)
        logger.info(f"获取到{len(factors)}个因子")
        for factor in factors:
            logger.info(f"  {factor.name}: {factor.category} (使用次数: {factor.usageCount})")
        
        # 测试获取因子分类
        categories = await get_factor_categories(db=db)
        logger.info(f"因子分类: {categories}")
        
        # 测试创建新因子
        new_factor_data = FactorCreate(
            name="测试RSI因子",
            description="基于RSI技术指标的动量因子",
            category="技术",
            code="""def calculate(data):
    # 计算RSI指标
    close_prices = data['close']
    delta = close_prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)""",
            isActive=True
        )
        
        try:
            new_factor = await create_factor(new_factor_data, db=db)
            logger.info(f"创建新因子成功: {new_factor.name} (ID: {new_factor.id})")
            
            # 测试因子代码
            test_request = FactorTestRequest(
                symbols=["000001.SZ", "600036.SH", "000002.SZ"],
                startDate="20240101",
                endDate="20241201"
            )
            
            test_result = await test_factor(new_factor.id, test_request, db=db)
            logger.info(f"因子测试结果: {test_result.success}")
            logger.info(f"执行时间: {test_result.executionTime:.2f}秒")
            
            if test_result.results:
                logger.info("测试结果:")
                for result in test_result.results:
                    logger.info(f"  {result.symbol}: 值={result.value:.4f}, 排名={result.rank}, 百分位={result.percentile:.1f}%")
            
            if test_result.statistics:
                stats = test_result.statistics
                logger.info(f"统计信息: 均值={stats.get('mean', 0):.4f}, 标准差={stats.get('std', 0):.4f}")
        
        except Exception as e:
            logger.warning(f"创建或测试因子失败: {e}")
        
    except Exception as e:
        logger.error(f"因子管理API测试失败: {e}")
    finally:
        db.close()


async def test_factor_validation():
    """测试因子代码验证功能"""
    logger.info("测试因子代码验证...")
    
    # 测试有效的因子代码
    valid_code = """def calculate(data):
    return data['close'].pct_change(20).fillna(0)"""
    
    result = await factor_service.validate_factor_code(valid_code)
    logger.info(f"有效代码验证结果: {result.is_valid}")
    
    # 测试无效的因子代码
    invalid_code = """def calculate(data):
    import os
    return os.system('ls')"""
    
    result = await factor_service.validate_factor_code(invalid_code)
    logger.info(f"无效代码验证结果: {result.is_valid}, 错误: {result.error_message}")
    
    # 测试语法错误的代码
    syntax_error_code = """def calculate(data):
    return data['close'].pct_change(20).fillna(0"""
    
    result = await factor_service.validate_factor_code(syntax_error_code)
    logger.info(f"语法错误代码验证结果: {result.is_valid}, 错误: {result.error_message}")


async def test_factor_execution():
    """测试因子执行功能"""
    logger.info("测试因子执行引擎...")
    
    # 测试简单的PE因子
    pe_factor_code = """def calculate(data):
    pe_values = data['pe_ttm'].fillna(0)
    # PE倍数越低，得分越高
    scores = 1 / (pe_values + 1)
    return scores.fillna(0)"""
    
    test_result = await factor_service.test_factor(
        factor_code=pe_factor_code,
        test_symbols=["000001.SZ", "600036.SH", "000002.SZ"]
    )
    
    logger.info(f"PE因子测试: {test_result.success}")
    logger.info(f"执行时间: {test_result.executionTime:.2f}秒")
    
    if test_result.results:
        for result in test_result.results:
            logger.info(f"  {result.symbol}: PE因子值={result.value:.4f}")


async def main():
    """主测试函数"""
    logger.info("开始因子系统测试...")
    
    try:
        await test_factor_validation()
        await test_factor_execution()
        await test_factor_management()
        logger.info("所有因子系统测试完成！")
    except Exception as e:
        logger.error(f"测试失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())