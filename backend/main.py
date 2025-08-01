"""
量化主观选股系统 - FastAPI后端入口文件
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    setup_logging()
    logging.info("量化选股系统启动中...")
    
    # 这里可以添加数据库初始化、定时任务启动等
    
    yield
    
    # 关闭时执行
    logging.info("量化选股系统关闭中...")


# 创建FastAPI应用实例
app = FastAPI(
    title="量化主观选股系统",
    description="基于Python的量化选股平台，支持自定义因子和策略回测",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React开发服务器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 健康检查接口
@app.get("/health")
async def health_check():
    """健康检查接口"""
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "quantitative-stock-selection",
            "version": "1.0.0"
        }
    )


# 根路径
@app.get("/")
async def root():
    """根路径欢迎信息"""
    return {
        "message": "欢迎使用量化主观选股系统",
        "docs": "/docs",
        "health": "/health"
    }


# 注册API路由
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )