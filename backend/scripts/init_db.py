#!/usr/bin/env python3
"""
数据库初始化脚本
"""

import asyncio
import logging
from datetime import datetime

from app.db.database import init_db, check_db_connection
from app.services.tushare_service import tushare_service
from app.db.models.stock import Stock, StockDaily, MarketIndex
from app.db.models.factor import Factor
from app.db.models.watchlist import Watchlist
from app.db.database import SessionLocal

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_sample_data():
    """创建示例数据"""
    db = SessionLocal()
    try:
        # 创建示例因子
        sample_factors = [
            Factor(
                factor_id="pe_factor",
                name="PE倍数因子",
                display_name="PE倍数因子",
                description="基于市盈率的估值因子，PE倍数越低得分越高",
                category="估值",
                formula="""import numpy as np
import pandas as pd

# data是包含股票数据的DataFrame
# 必须包含pe_ttm列
pe_values = data['pe_ttm'].fillna(0)
# PE倍数越低，得分越高
scores = 1 / (pe_values + 1)  # 避免除零
result = scores.fillna(0)""",
                input_fields=["pe_ttm"],
                default_parameters={},
                parameter_schema={},
                calculation_method="custom",
                is_active=True,
                is_builtin=False,
                version="1.0.0"
            ),
            Factor(
                factor_id="momentum_factor",
                name="动量因子",
                display_name="动量因子",
                description="基于20日价格动量的技术因子",
                category="技术",
                formula="""import numpy as np
import pandas as pd

# 计算20日收益率
returns = data['close'].pct_change(20).fillna(0)
result = returns""",
                input_fields=["close"],
                default_parameters={},
                parameter_schema={},
                calculation_method="custom",
                is_active=True,
                is_builtin=False,
                version="1.0.0"
            ),
            Factor(
                factor_id="market_cap_factor",
                name="市值因子",
                display_name="市值因子",
                description="基于总市值的规模因子，小市值得分更高",
                category="基本面",
                formula="""import numpy as np
import pandas as pd

# 总市值越小，得分越高
market_cap = data['total_mv'].fillna(0)
scores = 1 / (market_cap / 10000 + 1)  # 转换为亿元并避免除零
result = scores""",
                input_fields=["total_mv"],
                default_parameters={},
                parameter_schema={},
                calculation_method="custom",
                is_active=True,
                is_builtin=False,
                version="1.0.0"
            )
        ]
        
        for factor in sample_factors:
            existing = db.query(Factor).filter(Factor.factor_id == factor.factor_id).first()
            if not existing:
                db.add(factor)
                logger.info(f"创建示例因子: {factor.name}")
        
        # 创建示例自选股
        sample_watchlist = [
            Watchlist(symbol="000001.SZ", name="平安银行", notes="银行股龙头"),
            Watchlist(symbol="000002.SZ", name="万科A", notes="房地产龙头"),
            Watchlist(symbol="600036.SH", name="招商银行", notes="优质银行股"),
        ]
        
        for stock in sample_watchlist:
            existing = db.query(Watchlist).filter(Watchlist.symbol == stock.symbol).first()
            if not existing:
                db.add(stock)
                logger.info(f"创建示例自选股: {stock.name}")
        
        db.commit()
        logger.info("示例数据创建完成")
        
    except Exception as e:
        logger.error(f"创建示例数据失败: {e}")
        db.rollback()
    finally:
        db.close()


async def fetch_initial_data():
    """获取初始股票数据"""
    try:
        logger.info("开始获取初始股票数据...")
        
        # 获取股票列表
        stocks_df = await tushare_service.get_stock_list()
        if not stocks_df.empty:
            logger.info(f"获取到{len(stocks_df)}只股票基础信息")
            
            # 保存股票基础信息到数据库
            db = SessionLocal()
            try:
                count = 0
                for _, row in stocks_df.head(100).iterrows():  # 限制前100只股票
                    existing = db.query(Stock).filter(Stock.symbol == row.get('ts_code')).first()
                    if not existing:
                        stock = Stock(
                            symbol=row.get('ts_code', ''),
                            name=row.get('name', ''),
                            industry=row.get('industry', ''),
                            area=row.get('area', ''),
                            market=row.get('market', ''),
                            list_date=row.get('list_date', '')
                        )
                        db.add(stock)
                        count += 1
                
                db.commit()
                logger.info(f"保存了{count}只股票基础信息到数据库")
            except Exception as e:
                logger.error(f"保存股票数据失败: {e}")
                db.rollback()
            finally:
                db.close()
        
        # 获取市场指数数据
        indices_df = await tushare_service.get_market_indices()
        if not indices_df.empty:
            logger.info(f"获取到{len(indices_df)}条市场指数数据")
        
    except Exception as e:
        logger.error(f"获取初始数据失败: {e}")


async def main():
    """主函数"""
    logger.info("开始初始化数据库...")
    
    try:
        # 1. 初始化数据库表结构
        init_db()
        logger.info("数据库表结构创建完成")
        
        # 2. 检查数据库连接
        if check_db_connection():
            logger.info("数据库连接正常")
        else:
            logger.error("数据库连接失败")
            return
        
        # 3. 创建示例数据
        await create_sample_data()
        
        # 4. 获取初始数据（如果配置了Tushare token）
        if tushare_service.token:
            await fetch_initial_data()
        else:
            logger.warning("未配置Tushare token，跳过数据获取")
        
        logger.info("数据库初始化完成！")
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())