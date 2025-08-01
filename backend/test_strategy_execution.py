#!/usr/bin/env python3
"""
策略执行测试
"""

import asyncio
import logging
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.api.v1.endpoints.strategies import get_strategies, execute_strategy
from app.schemas.factors import StrategyExecutionRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_existing_strategy_execution():
    """测试执行现有策略"""
    logger.info("测试执行现有策略...")
    
    db = SessionLocal()
    try:
        # 获取现有策略
        strategies = await get_strategies(db=db)
        if not strategies:
            logger.warning("没有可用的策略")
            return
        
        # 选择第一个策略进行测试
        strategy = strategies[0]
        logger.info(f"执行策略: {strategy.name}")
        logger.info(f"使用因子: {strategy.factorIds}")
        logger.info(f"因子权重: {strategy.factorWeights}")
        
        # 执行策略
        execution_request = StrategyExecutionRequest(dryRun=True)
        result = await execute_strategy(strategy.id, execution_request, db=db)
        
        logger.info(f"策略执行结果: {result.success}")
        logger.info(f"执行时间: {result.executionTime:.2f}秒")
        logger.info(f"股票池大小: {result.totalStocks}")
        logger.info(f"选股结果: {result.resultCount}只股票")
        
        if result.results:
            logger.info("选股结果TOP10:")
            for i, stock in enumerate(result.results[:10]):
                logger.info(f"  {i+1}. {stock.symbol} ({stock.name})")
                logger.info(f"     综合得分: {stock.totalScore:.4f}")
                logger.info(f"     价格: {stock.price}, 市值: {stock.marketCap}")
                logger.info(f"     因子得分: {stock.factorScores}")
        
        if result.statistics:
            logger.info("执行统计:")
            stats = result.statistics
            if 'scoreStats' in stats:
                score_stats = stats['scoreStats']
                logger.info(f"  得分统计: 均值={score_stats.get('mean', 0):.4f}, 标准差={score_stats.get('std', 0):.4f}")
                logger.info(f"  得分范围: {score_stats.get('min', 0):.4f} ~ {score_stats.get('max', 0):.4f}")
            
            if 'factorContribution' in stats:
                logger.info("  因子贡献度:")
                for factor_id, contribution in stats['factorContribution'].items():
                    logger.info(f"    因子{factor_id}: {contribution:.4f}")
    
    except Exception as e:
        logger.error(f"策略执行测试失败: {e}")
    finally:
        db.close()


async def main():
    """主测试函数"""
    logger.info("开始策略执行测试...")
    
    try:
        await test_existing_strategy_execution()
        logger.info("策略执行测试完成！")
    except Exception as e:
        logger.error(f"测试失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())