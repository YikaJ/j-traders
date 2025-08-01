"""
日志配置模块
"""

import logging
import logging.handlers
import os
from pathlib import Path

from app.core.config import settings


def setup_logging():
    """设置应用日志配置"""
    
    # 创建logs目录
    log_dir = Path(settings.LOG_FILE).parent
    log_dir.mkdir(exist_ok=True)
    
    # 配置日志格式
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # 根日志器配置
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # 清除现有处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    root_logger.addHandler(console_handler)
    
    # 文件处理器（轮转日志）
    file_handler = logging.handlers.RotatingFileHandler(
        filename=settings.LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    root_logger.addHandler(file_handler)
    
    # 设置第三方库的日志级别
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    logging.info("日志系统初始化完成")


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志器"""
    return logging.getLogger(name)