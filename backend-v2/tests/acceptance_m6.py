from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.main import create_app  # noqa: E402


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

    # prepare factor with selection
    sel = json.loads((Path(__file__).resolve().parents[1] / "catalog" / "selections" / "val_low_combo.json").read_text(encoding="utf-8"))
    code = (
        "import pandas as pd\n\n"
        "def compute_factor(data, params):\n"
        "    df = data['daily_basic'].copy()\n"
        "    df['factor'] = -df['pe_ttm'] + -df['pb']\n"
        "    return df\n"
    )
    r1 = client.post("/factors", json={"name": "val_low_combo", "code_text": code, "fields_used": ["ts_code", "trade_date", "pe_ttm", "pb"], "selection": sel})
    fid = r1.json().get("id")
    expect(r1.status_code == 200 and isinstance(fid, int), "M6 save factor", results)

    # strategy
    r2 = client.post("/strategies", json={"name": "combo", "normalization": {"method": "zscore", "winsor": [0.01, 0.99], "fill": "median"}})
    sid = r2.json().get("id")
    expect(r2.status_code == 200 and isinstance(sid, int), "M6 create strategy", results)

    # weights
    r3 = client.put(f"/strategies/{sid}/weights", json={"weights": [{"factor_id": fid, "weight": 1.0}]})
    expect(r3.status_code == 200, "M6 set weights", results)

    # run
    body = {"ts_codes": ["000001.SZ", "600000.SH"], "start_date": "20210101", "end_date": "20210108", "top_n": 2}
    r4 = client.post(f"/strategies/{sid}/run", json=body)
    js4 = r4.json()
    expect(r4.status_code == 200 and isinstance(js4.get("results"), list) and len(js4.get("results")) > 0, "M6 run strategy returns results", results)

    print("---- Summary ----")
    print("Passed:", len(results["pass"]))
    print("Failed:", len(results["fail"]), results["fail"])
    return 0 if not results["fail"] else 1


if __name__ == "__main__":
    raise SystemExit(run_acceptance())
