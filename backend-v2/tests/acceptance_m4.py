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

    # 1) standardize/zscore
    data = [
        {"ts_code": "000001.SZ", "trade_date": "20210101", "factor": 1.0},
        {"ts_code": "600000.SH", "trade_date": "20210101", "factor": 2.0},
        {"ts_code": "000001.SZ", "trade_date": "20210108", "factor": 3.0},
        {"ts_code": "600000.SH", "trade_date": "20210108", "factor": 4.0},
    ]
    r1 = client.post("/standardize/zscore", json={"by": ["trade_date"], "winsor": [0.01, 0.99], "fill": "median", "data": data})
    js1 = r1.json()
    expect(r1.status_code == 200 and isinstance(js1.get("data"), list), "M4 /standardize/zscore 200", results)

    # 2) factors/test preview
    sel = json.loads((Path(__file__).resolve().parents[1] / "catalog" / "selections" / "val_low_combo.json").read_text(encoding="utf-8"))
    code = (
        "import pandas as pd\n\n"
        "def compute_factor(data, params):\n"
        "    df = data['daily_basic'].copy()\n"
        "    df['factor'] = -df['pe_ttm'] + -df['pb']\n"
        "    return df\n"
    )
    body = {"selection": sel, "code_text": code, "params": {}, "ts_codes": ["000001.SZ", "600000.SH"], "start_date": "20210101", "end_date": "20210108", "normalization": {"method": "zscore", "winsor": [0.01, 0.99], "fill": "median", "by": ["trade_date"]}, "top_n": 3}
    r2 = client.post("/factors/test", json=body)
    js2 = r2.json()
    expect(r2.status_code == 200 and isinstance(js2.get("sample_rows"), list), "M4 /factors/test 200", results)

    print("---- Summary ----")
    print("Passed:", len(results["pass"]))
    print("Failed:", len(results["fail"]), results["fail"])
    return 0 if not results["fail"] else 1


if __name__ == "__main__":
    raise SystemExit(run_acceptance())
