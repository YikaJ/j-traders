from __future__ import annotations

from fastapi import APIRouter
from typing import Any, Dict

from ..core.config import load_settings

def _check_tushare_token() -> Dict[str, Any]:
    s = load_settings()
    ok = bool(s.tushare_token)
    detail: Dict[str, Any] = {"configured": ok}
    if not ok:
        return {"ok": False, "detail": detail}
    # Optional: query user points and nearest expiry via ts.pro_api
    try:
        import tushare as ts  # type: ignore
        ts.set_token(s.tushare_token)
        pro = ts.pro_api()
        df = pro.user(token=s.tushare_token)
        exp_date = None
        exp_score = None
        if df is not None and not df.empty:
            # 取最新到期时间/积分（按到期时间降序）
            try:
                df_sorted = df.sort_values(by=["到期时间"], ascending=False)
            except Exception:
                df_sorted = df
            row = df_sorted.iloc[0]
            exp_date = str(row.get("到期时间"))
            exp_score = float(row.get("到期积分")) if row.get("到期积分") is not None else None
        return {"ok": True, "detail": {"configured": True, "expire_date": exp_date, "expire_score": exp_score}}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e), "detail": detail}

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    token = _check_tushare_token()
    return {"status": "ok", "version": "0.1.0", "tushare": token}
