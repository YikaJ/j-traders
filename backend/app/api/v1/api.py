"""
API v1 主路由配置
"""

from fastapi import APIRouter

# 创建API路由器
api_router = APIRouter()


# 临时的测试路由
@api_router.get("/test")
async def test_endpoint():
    """测试接口"""
    return {"message": "API v1 工作正常", "version": "1.0.0"}


# 包含所有路由模块
from app.api.v1.endpoints import market, watchlist, factors, strategies, stocks

api_router.include_router(market.router, prefix="/market", tags=["market"])
api_router.include_router(watchlist.router, prefix="/watchlist", tags=["watchlist"])
api_router.include_router(factors.router, prefix="/factors", tags=["factors"])
api_router.include_router(strategies.router, prefix="/strategies", tags=["strategies"])
api_router.include_router(stocks.router, prefix="/stocks", tags=["stocks"])