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

    sel = json.loads((Path(__file__).resolve().parents[1] / "catalog" / "selections" / "val_low_combo.json").read_text(encoding="utf-8"))

    # Factors
    body = {
        "name": "val_low_combo",
        "desc": "PE_TTM + PB",
        "code_text": "def compute_factor(data, params):\n    import pandas as pd\n    key = next(iter(data.keys()))\n    df = data[key].copy()\n    df['factor'] = 0.0\n    return df\n",
        "fields_used": ["ts_code", "trade_date", "pe_ttm", "pb"],
        "normalization": {"method": "zscore", "winsor": [0.01, 0.99], "fill": "median"},
        "tags": ["valuation"],
        "selection": sel,
    }
    r1 = client.post("/factors", json=body)
    fid = r1.json().get("id")
    expect(r1.status_code == 200 and isinstance(fid, int), "M5 save factor", results)

    r2 = client.get(f"/factors/{fid}")
    expect(r2.status_code == 200 and r2.json().get("id") == fid, "M5 get factor", results)
    expect(r2.json().get("selection", {}).get("factor_slug") == sel.get("factor_slug"), "M5 factor persisted selection", results)

    r3 = client.get("/factors")
    expect(r3.status_code == 200 and any(x.get("id") == fid for x in r3.json()), "M5 list factors", results)

    # Strategies
    r4 = client.post("/strategies", json={"name": "combo", "normalization": {"method": "zscore"}})
    sid = r4.json().get("id")
    expect(r4.status_code == 200 and isinstance(sid, int), "M5 create strategy", results)

    # Update weights (auto L1 normalize)
    r5 = client.put(f"/strategies/{sid}/weights", json={"weights": [{"factor_id": fid, "weight": 2.0}]})
    expect(r5.status_code == 200, "M5 update strategy weights", results)

    r6 = client.get(f"/strategies/{sid}")
    js6 = r6.json()
    expect(r6.status_code == 200 and any(w.get("factor_id") == fid for w in js6.get("weights", [])), "M5 get strategy with weights", results)

    # Update normalization
    r7 = client.put(f"/strategies/{sid}/normalization", json={"normalization": {"method": "zscore", "fill": "median"}})
    expect(r7.status_code == 200, "M5 update strategy normalization", results)

    print("---- Summary ----")
    print("Passed:", len(results["pass"]))
    print("Failed:", len(results["fail"]), results["fail"])
    return 0 if not results["fail"] else 1


if __name__ == "__main__":
    raise SystemExit(run_acceptance())
