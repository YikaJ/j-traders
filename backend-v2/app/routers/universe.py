from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from ..core.config import load_settings
from ..storage.db import bulk_upsert_securities, query_stocks, get_stock

router = APIRouter(prefix="/universe", tags=["universe"])


@router.post("/sync", response_model=Dict[str, Any])
def sync_universe(
    sec_type: str = Query("stock", pattern="^(stock|etf)$"),
    mock: bool = Query(False, description="Seed demo rows when true"),
) -> Any:
    if sec_type != "stock":
        return {"ok": True, "synced": 0, "notes": "ETFs not implemented in MVP"}
    if mock:
        rows = [
            {"sec_type": "stock", "ts_code": "000001.SZ", "symbol": "000001", "name": "平安银行", "area": "深圳", "industry": "银行", "market": "主板", "exchange": "SZSE", "list_status": "L", "list_date": "19910403", "delist_date": None, "is_hs": "S"},
            {"sec_type": "stock", "ts_code": "600000.SH", "symbol": "600000", "name": "浦发银行", "area": "上海", "industry": "银行", "market": "主板", "exchange": "SSE", "list_status": "L", "list_date": "19991110", "delist_date": None, "is_hs": "H"},
        ]
        n = bulk_upsert_securities(rows)
        return {"ok": True, "synced": n, "notes": "mock seeded"}
    # fetch stock_basic via tushare
    try:
        import tushare as ts  # type: ignore
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail="tushare not installed")
    settings = load_settings()
    if not settings.tushare_token:
        raise HTTPException(status_code=500, detail="TUSHARE_TOKEN is required")
    ts.set_token(settings.tushare_token)
    pro = ts.pro_api()
    df = pro.stock_basic(fields="ts_code,symbol,name,area,industry,market,exchange,list_status,list_date,delist_date,is_hs")
    rows: List[Dict[str, Any]] = []
    for _, r in df.iterrows():
        rows.append({
            "sec_type": "stock",
            "ts_code": r.get("ts_code"),
            "symbol": r.get("symbol"),
            "name": r.get("name"),
            "area": r.get("area"),
            "industry": r.get("industry"),
            "market": r.get("market"),
            "exchange": r.get("exchange"),
            "list_status": r.get("list_status"),
            "list_date": r.get("list_date"),
            "delist_date": r.get("delist_date"),
            "is_hs": r.get("is_hs"),
        })
    n = bulk_upsert_securities(rows)
    return {"ok": True, "synced": n}


@router.get("/stocks", response_model=List[Dict[str, Any]])
def list_stocks(
    industry: Optional[str] = None,
    market: Optional[str] = None,
    list_status: Optional[str] = None,
    exchange: Optional[str] = None,
    is_hs: Optional[str] = None,
    q: Optional[str] = None,
) -> Any:
    return query_stocks({
        "industry": industry,
        "market": market,
        "list_status": list_status,
        "exchange": exchange,
        "is_hs": is_hs,
        "q": q,
    })


@router.get("/stocks/{ts_code}", response_model=Dict[str, Any])
def get_stock_by_code(ts_code: str) -> Any:
    rec = get_stock(ts_code)
    if not rec:
        raise HTTPException(status_code=404, detail="not found")
    return rec
