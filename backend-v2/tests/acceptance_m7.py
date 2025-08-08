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

    # health
    r0 = client.get("/health")
    expect(r0.status_code == 200, "M7 /health", results)

    # codegen scaffold & validate
    sel = json.loads((Path(__file__).resolve().parents[1] / "catalog" / "selections" / "val_low_combo.json").read_text(encoding="utf-8"))
    r1 = client.post("/factors/codegen", json={"selection": sel, "user_factor_spec": "neutral"})
    js1 = r1.json()
    expect(r1.status_code == 200 and bool(js1.get("code_text")), "M7 codegen", results)
    code = js1.get("code_text")
    r2 = client.post("/factors/validate", json={"code_text": code, "selection": sel})
    expect(r2.status_code == 200 and r2.json().get("ok") is True, "M7 validate ok", results)

    # persist factor
    r3 = client.post("/factors", json={"name": "e2e_factor", "code_text": code, "fields_used": ["ts_code","trade_date"], "selection": sel})
    fid = r3.json().get("id")
    expect(r3.status_code == 200 and isinstance(fid, int), "M7 save factor", results)

    # strategy and run
    r4 = client.post("/strategies", json={"name": "e2e_strategy", "normalization": {"method":"zscore","winsor":[0.01,0.99],"fill":"median"}})
    sid = r4.json().get("id")
    expect(r4.status_code == 200 and isinstance(sid, int), "M7 create strategy", results)

    client.put(f"/strategies/{sid}/weights", json={"weights":[{"factor_id": fid, "weight": 1.0}]})
    r5 = client.post(f"/strategies/{sid}/run", json={"ts_codes":["000001.SZ","600000.SH"], "start_date":"20210101","end_date":"20210108","top_n":2})
    expect(r5.status_code == 200 and isinstance(r5.json().get("results"), list), "M7 run strategy", results)

    print("---- Summary ----")
    print("Passed:", len(results["pass"]))
    print("Failed:", len(results["fail"]), results["fail"])
    return 0 if not results["fail"] else 1


if __name__ == "__main__":
    raise SystemExit(run_acceptance())
