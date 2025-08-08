from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.main import create_app  # noqa: E402
from app.storage.db import bulk_upsert_securities  # noqa: E402


def expect(cond: bool, name: str, results: dict) -> None:
    if cond:
        results.setdefault("pass", []).append(name)
        print(f"[PASS] {name}")
    else:
        results.setdefault("fail", []).append(name)
        print(f"[FAIL] {name}")


def run_acceptance() -> int:
    results = {"pass": [], "fail": []}
    app = create_app()
    client = TestClient(app)

    # Seed a few stocks (avoid real tushare dependency in test)
    bulk_upsert_securities([
        {"sec_type": "stock", "ts_code": "000001.SZ", "symbol": "000001", "name": "平安银行", "area": "深圳", "industry": "银行", "market": "主板", "exchange": "SZSE", "list_status": "L", "list_date": "19910403", "delist_date": None, "is_hs": "S"},
        {"sec_type": "stock", "ts_code": "600000.SH", "symbol": "600000", "name": "浦发银行", "area": "上海", "industry": "银行", "market": "主板", "exchange": "SSE", "list_status": "L", "list_date": "19991110", "delist_date": None, "is_hs": "H"},
    ])

    # list
    r1 = client.get("/universe/stocks", params={"industry": "银行"})
    expect(r1.status_code == 200 and len(r1.json()) >= 2, "M6 universe list by industry", results)

    # get
    r2 = client.get("/universe/stocks/000001.SZ")
    expect(r2.status_code == 200 and r2.json().get("ts_code") == "000001.SZ", "M6 universe get by ts_code", results)

    print("---- Summary ----")
    print("Passed:", len(results["pass"]))
    print("Failed:", len(results["fail"]), results["fail"])
    return 0 if not results["fail"] else 1


if __name__ == "__main__":
    raise SystemExit(run_acceptance())
