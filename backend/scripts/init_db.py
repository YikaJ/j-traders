#!/usr/bin/env python3
"""
数据库初始化脚本（强制重建表结构，插入标准因子）
"""

import asyncio
import logging
import os
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from app.db.database import engine, Base
# 强制导入所有模型，确保Base注册
from app.db.models import factor, stock, strategy, watchlist

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = 'quantitative_stock.db'

async def main():
    # 1. 删除旧数据库文件
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        logger.info(f"已删除旧数据库文件: {DB_PATH}")

    # 2. 创建新数据库并建表
    Base.metadata.create_all(engine)
    logger.info("数据库表结构创建完成")
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # 3. 插入标准因子
        Factor = factor.Factor
        factor_obj = Factor(
            factor_id="test-factor-001",
            name="测试因子",
            display_name="测试因子",
            description="这是一个用于测试的因子",
            formula="import numpy as np\nimport pandas as pd\nresult = data[\"close\"].pct_change()",
            input_fields=["close"],
            default_parameters={},
            parameter_schema={},
            calculation_method="custom",
            is_active=True,
            is_builtin=False,
            usage_count=0,
            last_used_at=None,
            version="1.0.0"
        )
        db.add(factor_obj)
        db.commit()
        logger.info("已插入标准测试因子")
    except Exception as e:
        logger.error(f"插入因子失败: {e}")
        db.rollback()
    finally:
        db.close()
    logger.info("数据库初始化完成！")

if __name__ == "__main__":
    asyncio.run(main())