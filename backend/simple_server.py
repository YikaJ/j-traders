"""
简化的后端服务器 - 提供基本的API接口用于前端测试
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from datetime import datetime, timedelta
import random

app = FastAPI(title="量化选股系统 API", version="1.0.0")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据模型
class MarketIndex(BaseModel):
    symbol: str
    name: str
    price: float
    change: float
    changePercent: float
    volume: int
    amount: Optional[float] = None
    tradeDate: Optional[str] = None

class StockQuote(BaseModel):
    symbol: str
    name: str
    price: float
    change: float
    changePercent: float
    volume: Optional[int] = None
    amount: Optional[float] = None

class Factor(BaseModel):
    id: str
    name: str
    description: str
    category: str
    code: str

class StrategyResult(BaseModel):
    symbol: str
    name: str
    score: float
    rank: int
    price: float
    changePercent: float

class WatchlistStock(BaseModel):
    id: Optional[int] = None
    symbol: str
    name: str
    price: float
    change: float
    changePercent: float
    addedAt: Optional[str] = None

class CreateFactorRequest(BaseModel):
    name: str
    description: str
    category: str
    code: str

class ExecuteStrategyRequest(BaseModel):
    factors: List[str]
    maxResults: Optional[int] = 50

class AddWatchlistRequest(BaseModel):
    symbol: str
    name: str

# 模拟数据
mock_indices = [
    MarketIndex(
        symbol="000001.SH",
        name="上证指数",
        price=3245.12 + random.uniform(-50, 50),
        change=random.uniform(-30, 30),
        changePercent=random.uniform(-1.5, 1.5),
        volume=245600000,
        tradeDate=datetime.now().strftime("%Y%m%d")
    ),
    MarketIndex(
        symbol="399001.SZ",
        name="深证成指",
        price=10234.56 + random.uniform(-100, 100),
        change=random.uniform(-40, 40),
        changePercent=random.uniform(-1.8, 1.8),
        volume=189400000,
        tradeDate=datetime.now().strftime("%Y%m%d")
    ),
    MarketIndex(
        symbol="399006.SZ",
        name="创业板指",
        price=2156.78 + random.uniform(-80, 80),
        change=random.uniform(-25, 25),
        changePercent=random.uniform(-2.0, 2.0),
        volume=156700000,
        tradeDate=datetime.now().strftime("%Y%m%d")
    )
]

mock_factors = [
    Factor(
        id="1",
        name="PE倍数因子",
        description="基于市盈率的估值因子",
        category="估值",
        code="def calculate(data):\n    pe_ratio = data['market_cap'] / data['net_income']\n    return 1 / pe_ratio"
    ),
    Factor(
        id="2",
        name="动量因子",
        description="基于价格动量的技术因子",
        category="技术",
        code="def calculate(data):\n    returns_20d = data['close'].pct_change(20)\n    return returns_20d.fillna(0)"
    )
]

mock_watchlist = [
    WatchlistStock(
        id=1,
        symbol="000001.SZ",
        name="平安银行",
        price=15.23 + random.uniform(-2, 2),
        change=random.uniform(-1, 1),
        changePercent=random.uniform(-5, 5),
        addedAt=datetime.now().strftime("%Y-%m-%d")
    ),
    WatchlistStock(
        id=2,
        symbol="000002.SZ",
        name="万科A",
        price=18.67 + random.uniform(-3, 3),
        change=random.uniform(-1.5, 1.5),
        changePercent=random.uniform(-6, 6),
        addedAt=(datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    ),
    WatchlistStock(
        id=3,
        symbol="600036.SH",
        name="招商银行",
        price=42.15 + random.uniform(-5, 5),
        change=random.uniform(-2, 2),
        changePercent=random.uniform(-4, 4),
        addedAt=(datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    )
]

# API接口
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/v1/test")
async def test_api():
    return {"message": "API v1 工作正常", "version": "1.0.0"}

# 市场数据接口
@app.get("/api/v1/market/indices", response_model=List[MarketIndex])
async def get_market_indices(trade_date: Optional[str] = None):
    """获取市场指数数据"""
    # 随机更新价格模拟实时数据
    for index in mock_indices:
        base_price = float(index.price)
        index.price = base_price + random.uniform(-base_price*0.02, base_price*0.02)
        index.change = random.uniform(-30, 30)
        index.changePercent = (index.change / (index.price - index.change)) * 100
    
    return mock_indices

@app.get("/api/v1/market/quotes", response_model=List[StockQuote])
async def get_stock_quotes(symbols: Optional[str] = None):
    """获取股票行情"""
    quotes = []
    if symbols:
        symbol_list = symbols.split(',')
        for symbol in symbol_list:
            quotes.append(StockQuote(
                symbol=symbol,
                name=f"股票{symbol}",
                price=random.uniform(10, 100),
                change=random.uniform(-5, 5),
                changePercent=random.uniform(-10, 10),
                volume=random.randint(1000000, 10000000)
            ))
    return quotes

# 因子管理接口
@app.get("/api/v1/factors", response_model=List[Factor])
async def get_factors():
    """获取所有因子"""
    return mock_factors

@app.post("/api/v1/factors", response_model=Factor)
async def create_factor(factor: CreateFactorRequest):
    """创建新因子"""
    new_factor = Factor(
        id=str(len(mock_factors) + 1),
        name=factor.name,
        description=factor.description,
        category=factor.category,
        code=factor.code
    )
    mock_factors.append(new_factor)
    return new_factor

@app.delete("/api/v1/factors/{factor_id}")
async def delete_factor(factor_id: str):
    """删除因子"""
    global mock_factors
    mock_factors = [f for f in mock_factors if f.id != factor_id]
    return {"message": "因子删除成功"}

# 策略执行接口
@app.post("/api/v1/strategies/execute", response_model=List[StrategyResult])
async def execute_strategy(request: ExecuteStrategyRequest):
    """执行选股策略"""
    results = []
    stock_names = ["平安银行", "招商银行", "万科A", "贵州茅台", "五粮液", "宁德时代", "比亚迪", "中国平安", "工商银行", "建设银行"]
    
    for i in range(min(request.maxResults, len(stock_names))):
        results.append(StrategyResult(
            symbol=f"{random.choice(['000', '600', '300'])}{random.randint(100, 999):03d}.{'SZ' if random.random() > 0.5 else 'SH'}",
            name=stock_names[i],
            score=random.uniform(0.5, 1.0),
            rank=i + 1,
            price=random.uniform(10, 200),
            changePercent=random.uniform(-5, 8)
        ))
    
    return results

# 自选股管理接口
@app.get("/api/v1/watchlist", response_model=List[WatchlistStock])
async def get_watchlist():
    """获取自选股列表"""
    # 随机更新价格
    for stock in mock_watchlist:
        base_price = float(stock.price)
        stock.price = base_price + random.uniform(-base_price*0.05, base_price*0.05)
        stock.change = random.uniform(-2, 2)
        stock.changePercent = (stock.change / (stock.price - stock.change)) * 100
    
    return mock_watchlist

@app.post("/api/v1/watchlist", response_model=WatchlistStock)
async def add_to_watchlist(request: AddWatchlistRequest):
    """添加自选股"""
    new_stock = WatchlistStock(
        id=len(mock_watchlist) + 1,
        symbol=request.symbol,
        name=request.name,
        price=random.uniform(10, 100),
        change=random.uniform(-2, 2),
        changePercent=random.uniform(-5, 5),
        addedAt=datetime.now().strftime("%Y-%m-%d")
    )
    mock_watchlist.append(new_stock)
    return new_stock

@app.delete("/api/v1/watchlist/{stock_id}")
async def remove_from_watchlist(stock_id: int):
    """删除自选股"""
    global mock_watchlist
    mock_watchlist = [s for s in mock_watchlist if s.id != stock_id]
    return {"message": "自选股删除成功"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)