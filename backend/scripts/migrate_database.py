#!/usr/bin/env python3
"""
数据库迁移脚本
删除 factor_values 和 weight_presets 表
添加 stock_company_info 表
"""

import asyncio
import logging
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.db.database import engine, SessionLocal


# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate_database():
    """执行数据库迁移"""
    
    db = SessionLocal()
    
    try:
        # 1. 删除 factor_values 表
        logger.info("正在删除 factor_values 表...")
        try:
            db.execute(text("DROP TABLE IF EXISTS factor_values"))
            logger.info("factor_values 表删除成功")
        except Exception as e:
            logger.warning(f"删除 factor_values 表失败: {e}")
        
        # 2. 删除 weight_presets 表
        logger.info("正在删除 weight_presets 表...")
        try:
            db.execute(text("DROP TABLE IF EXISTS weight_presets"))
            logger.info("weight_presets 表删除成功")
        except Exception as e:
            logger.warning(f"删除 weight_presets 表失败: {e}")
        

        
        # 3. 提交更改
        db.commit()
        logger.info("数据库迁移完成")
        
        # 4. 验证迁移结果
        logger.info("验证迁移结果...")
        
        # 检查表是否存在
        tables_to_check = [
            ("factor_values", False),  # 应该不存在
            ("weight_presets", False)  # 应该不存在
        ]
        
        for table_name, should_exist in tables_to_check:
            result = db.execute(text(f"""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='{table_name}'
            """))
            
            exists = result.fetchone() is not None
            
            if exists == should_exist:
                logger.info(f"✓ {table_name} 表状态正确")
            else:
                logger.warning(f"✗ {table_name} 表状态异常 (期望: {should_exist}, 实际: {exists})")
        
    except Exception as e:
        logger.error(f"数据库迁移失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


async def rollback_migration():
    """回滚迁移（如果需要）"""
    logger.info("开始回滚迁移...")
    
    db = SessionLocal()
    
    try:
        # 重新创建被删除的表（如果需要的话）
        logger.info("重新创建 factor_values 表...")
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS factor_values (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                factor_id VARCHAR(100) NOT NULL,
                symbol VARCHAR(20) NOT NULL,
                execution_id INTEGER,
                value FLOAT NOT NULL,
                percentile FLOAT,
                rank INTEGER,
                calculated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (execution_id) REFERENCES strategy_executions(id)
            )
        """))
        
        logger.info("重新创建 weight_presets 表...")
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS weight_presets (
                id VARCHAR(100) PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                applicable_categories JSON,
                weights JSON,
                is_default BOOLEAN DEFAULT FALSE,
                usage_count INTEGER DEFAULT 0,
                last_used_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        db.commit()
        logger.info("回滚完成")
        
    except Exception as e:
        logger.error(f"回滚失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="数据库迁移脚本")
    parser.add_argument("--rollback", action="store_true", help="回滚迁移")
    
    args = parser.parse_args()
    
    if args.rollback:
        asyncio.run(rollback_migration())
    else:
        asyncio.run(migrate_database()) 