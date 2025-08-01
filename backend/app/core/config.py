"""
应用配置管理
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """应用配置类"""
    
    # 基础配置
    DEBUG: bool = True
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./quantitative_stock.db"
    
    # Tushare配置
    TUSHARE_TOKEN: Optional[str] = None
    
    # 安全配置
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    
    # 数据更新配置
    DATA_UPDATE_INTERVAL: int = 300  # 秒
    MAX_CONCURRENT_REQUESTS: int = 5
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"
    
    # Redis配置（可选）
    REDIS_URL: str = "redis://localhost:6379/0"
    USE_REDIS: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局设置实例
settings = Settings()


def get_database_url() -> str:
    """获取数据库URL"""
    return settings.DATABASE_URL


def get_tushare_token() -> Optional[str]:
    """获取Tushare Token"""
    if not settings.TUSHARE_TOKEN:
        raise ValueError(
            "Tushare token not configured. Please set TUSHARE_TOKEN in .env file"
        )
    return settings.TUSHARE_TOKEN