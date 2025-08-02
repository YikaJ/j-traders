"""
数据库连接和会话管理
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    # SQLite特定配置
    connect_args={
        "check_same_thread": False,  # 允许多线程访问
        "timeout": 20  # 连接超时时间
    },
    # 使用静态连接池，适合SQLite
    poolclass=StaticPool,
    echo=settings.DEBUG  # 在调试模式下显示SQL语句
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()


def get_db():
    """
    获取数据库会话的依赖函数
    用于FastAPI的依赖注入
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"数据库会话错误: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """
    初始化数据库
    创建所有表
    """
    try:
        # 直接导入所有模型以确保它们被注册到Base.metadata
        from app.db.models.stock import Stock, StockDaily, MarketIndex
        from app.db.models.factor import Factor, FactorFormulaHistory, FactorValue
        from app.db.models.strategy import Strategy, StrategyExecution, SelectionResult
        from app.db.models.watchlist import Watchlist, WatchlistGroup, WatchlistGroupMember
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        logger.info("数据库初始化完成")
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


def check_db_connection():
    """
    检查数据库连接状态
    """
    try:
        from sqlalchemy import text
        db = SessionLocal()
        # 执行一个简单的查询来测试连接
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception as e:
        logger.error(f"数据库连接检查失败: {e}")
        return False