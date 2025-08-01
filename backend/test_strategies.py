#!/usr/bin/env python3
"""
策略系统功能测试脚本
"""

import asyncio
import logging
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.api.v1.endpoints.strategies import (
    get_strategies,
    create_strategy,
    execute_strategy,
    get_strategy_results
)
from app.api.v1.endpoints.factors import get_factors
from app.schemas.factors import StrategyCreate, StrategyExecutionRequest
from app.services.strategy_service import strategy_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_strategy_management():
    """测试策略管理功能"""
    logger.info("测试策略管理API...")
    
    db = SessionLocal()
    try:
        # 获取现有策略
        strategies = await get_strategies(db=db)
        logger.info(f"获取到{len(strategies)}个策略")
        for strategy in strategies:
            logger.info(f"  {strategy.name}: 因子{strategy.factorIds} (执行次数: {strategy.executionCount})")
        
        # 获取可用因子
        factors = await get_factors(db=db)
        if not factors:
            logger.warning("没有可用的因子，无法创建策略")
            return
        
        factor_ids = [factor.id for factor in factors[:3]]  # 使用前3个因子
        logger.info(f"使用因子ID: {factor_ids}")
        
        # 创建新策略
        new_strategy_data = StrategyCreate(
            name="多因子价值策略",
            description="结合PE、PB和市值因子的价值投资策略",
            factorIds=factor_ids,
            factorWeights={
                str(factor_ids[0]): 0.4,  # PE因子权重40%
                str(factor_ids[1]): 0.3,  # 其他因子权重30%
                str(factor_ids[2]): 0.3   # 其他因子权重30%
            },
            maxResults=20,
            minMarketCap=5000000,  # 最小市值50亿
            excludeSt=True,
            excludeNewStock=True
        )
        
        try:
            new_strategy = await create_strategy(new_strategy_data, db=db)
            logger.info(f"创建新策略成功: {new_strategy.name} (ID: {new_strategy.id})")
            
            # 执行策略测试
            execution_request = StrategyExecutionRequest(
                dryRun=True  # 测试运行，不保存结果
            )
            
            execution_result = await execute_strategy(
                new_strategy.id, execution_request, db=db
            )
            
            logger.info(f"策略执行结果: {execution_result.success}")
            logger.info(f"执行时间: {execution_result.executionTime:.2f}秒")
            logger.info(f"股票池大小: {execution_result.totalStocks}")
            logger.info(f"选股结果: {execution_result.resultCount}只股票")
            
            if execution_result.results:
                logger.info("前10名选股结果:")
                for i, result in enumerate(execution_result.results[:10]):
                    logger.info(f"  {i+1}. {result.symbol} ({result.name}): 得分={result.totalScore:.4f}")
            
            if execution_result.statistics:
                stats = execution_result.statistics
                if 'scoreStats' in stats:
                    score_stats = stats['scoreStats']
                    logger.info(f"得分统计: 均值={score_stats.get('mean', 0):.4f}, 标准差={score_stats.get('std', 0):.4f}")
        
        except Exception as e:
            logger.warning(f"创建或执行策略失败: {e}")
        
    except Exception as e:
        logger.error(f"策略管理API测试失败: {e}")
    finally:
        db.close()


async def test_multi_factor_combination():
    """测试多因子组合计算"""
    logger.info("测试多因子组合计算...")
    
    db = SessionLocal()
    try:
        # 获取因子
        factors = await get_factors(db=db)
        if len(factors) < 2:
            logger.warning("因子数量不足，无法测试多因子组合")
            return
        
        # 创建多因子策略
        strategy_data = StrategyCreate(
            name="测试多因子组合",
            description="测试多个因子的权重组合计算",
            factorIds=[factors[0].id, factors[1].id],
            factorWeights={
                str(factors[0].id): 0.6,
                str(factors[1].id): 0.4
            },
            maxResults=10
        )
        
        strategy = await create_strategy(strategy_data, db=db)
        logger.info(f"创建测试策略: {strategy.name}")
        
        # 执行策略
        execution_request = StrategyExecutionRequest(dryRun=True)
        result = await execute_strategy(strategy.id, execution_request, db=db)
        
        logger.info(f"多因子组合计算完成: {result.success}")
        logger.info(f"组合得分范围: {result.statistics.get('scoreStats', {}).get('min', 0):.4f} ~ {result.statistics.get('scoreStats', {}).get('max', 0):.4f}")
        
        # 分析因子贡献度
        if 'factorContribution' in result.statistics:
            logger.info("因子贡献度:")
            for factor_id, contribution in result.statistics['factorContribution'].items():
                factor_name = next((f.name for f in factors if str(f.id) == factor_id), f"因子{factor_id}")
                logger.info(f"  {factor_name}: {contribution:.4f}")
    
    except Exception as e:
        logger.error(f"多因子组合测试失败: {e}")
    finally:
        db.close()


async def test_strategy_filters():
    """测试策略筛选条件"""
    logger.info("测试策略筛选条件...")
    
    db = SessionLocal()
    try:
        factors = await get_factors(db=db)
        if not factors:
            logger.warning("没有可用因子")
            return
        
        # 创建带筛选条件的策略
        strategy_data = StrategyCreate(
            name="筛选条件测试策略",
            description="测试各种筛选条件的效果",
            factorIds=[factors[0].id],
            maxResults=15,
            minMarketCap=1000000,    # 最小市值10亿
            maxMarketCap=100000000,  # 最大市值1000亿
            excludeSt=True,
            excludeNewStock=True,
            minTurnover=0.5  # 最小换手率0.5%
        )
        
        strategy = await create_strategy(strategy_data, db=db)
        logger.info(f"创建筛选策略: {strategy.name}")
        
        # 执行策略
        execution_request = StrategyExecutionRequest(dryRun=True)
        result = await execute_strategy(strategy.id, execution_request, db=db)
        
        logger.info(f"筛选策略执行: {result.success}")
        logger.info(f"筛选后股票池: {result.totalStocks}只股票")
        logger.info(f"最终选股: {result.resultCount}只股票")
        
        if result.results:
            logger.info("筛选结果样本:")
            for i, stock in enumerate(result.results[:5]):
                logger.info(f"  {stock.symbol}: 市值={stock.marketCap}, PE={stock.peRatio}, PB={stock.pbRatio}")
    
    except Exception as e:
        logger.error(f"筛选条件测试失败: {e}")
    finally:
        db.close()


async def test_strategy_execution_performance():
    """测试策略执行性能"""
    logger.info("测试策略执行性能...")
    
    db = SessionLocal()
    try:
        factors = await get_factors(db=db)
        if not factors:
            logger.warning("没有可用因子")
            return
        
        # 创建性能测试策略
        strategy_data = StrategyCreate(
            name="性能测试策略",
            description="测试大规模计算的性能表现",
            factorIds=[f.id for f in factors[:3]],  # 使用多个因子
            maxResults=50
        )
        
        strategy = await create_strategy(strategy_data, db=db)
        logger.info(f"创建性能测试策略: {strategy.name}")
        
        # 执行多次测试
        execution_times = []
        for i in range(3):
            logger.info(f"执行第{i+1}次性能测试...")
            
            execution_request = StrategyExecutionRequest(dryRun=True)
            result = await execute_strategy(strategy.id, execution_request, db=db)
            
            if result.success:
                execution_times.append(result.executionTime)
                logger.info(f"  执行时间: {result.executionTime:.2f}秒")
            else:
                logger.warning(f"  执行失败: {result.message}")
        
        if execution_times:
            avg_time = sum(execution_times) / len(execution_times)
            logger.info(f"平均执行时间: {avg_time:.2f}秒")
            logger.info(f"性能测试完成，共执行{len(execution_times)}次成功")
    
    except Exception as e:
        logger.error(f"性能测试失败: {e}")
    finally:
        db.close()


async def main():
    """主测试函数"""
    logger.info("开始策略系统测试...")
    
    try:
        await test_strategy_management()
        await test_multi_factor_combination()
        await test_strategy_filters()
        await test_strategy_execution_performance()
        logger.info("所有策略系统测试完成！")
    except Exception as e:
        logger.error(f"测试失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())