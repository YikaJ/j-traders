from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.main import create_app  # noqa: E402
from app.models.selection import SelectionSpec, SelectionItem, ParamBindingRequestArg  # noqa: E402
from app.services.param_binding import bind_params_for_selection, bind_params_for_item  # noqa: E402


def expect(condition: bool, name: str, results: Dict[str, List[str]]) -> None:
    if condition:
        results["pass"].append(name)
        print(f"[PASS] {name}")
    else:
        results["fail"].append(name)
        print(f"[FAIL] {name}")


def run_acceptance() -> int:
    results: Dict[str, List[str]] = {"pass": [], "fail": []}

    app = create_app()
    client = TestClient(app)

    # M0: health
    r = client.get("/health")
    expect(r.status_code == 200 and r.json().get("status") == "ok", "M0 /health", results)

    # M1: catalog
    r = client.get("/catalog/endpoints")
    js = r.json()
    names = {e.get("name") for e in js} if isinstance(js, list) else set()
    expect(r.status_code == 200 and "daily_basic" in names, "M1 list endpoints", results)

    r2 = client.get("/catalog/endpoints/daily_basic")
    expect(r2.status_code == 200 and r2.json().get("name") == "daily_basic", "M1 get endpoint daily_basic", results)

    r3 = client.get("/catalog/fields/search", params={"q": "pe"})
    expect(r3.status_code == 200 and isinstance(r3.json(), list), "M1 search fields", results)

    # M1: selections CRUD
    backend_v2_root = Path(__file__).resolve().parents[1]
    selections_dir = backend_v2_root / "catalog" / "selections"
    slug = "acceptance_tmp_m3"
    tmp_path = selections_dir / f"{slug}.json"
    if tmp_path.exists():
        tmp_path.unlink()

    base_sel = json.loads(
        (backend_v2_root / "catalog" / "selections" / "val_low_combo.json").read_text(encoding="utf-8")
    )
    base_sel["factor_slug"] = slug
    base_sel["title"] = "Acceptance TMP"

    r4 = client.post("/catalog/selections", json=base_sel)
    expect(r4.status_code in (200, 409), "M1 create selection (or exists)", results)

    r5 = client.get(f"/catalog/selections/{slug}")
    expect(r5.status_code == 200 and r5.json().get("factor_slug") == slug, "M1 get selection", results)

    updated = r5.json()
    updated["title"] = "Acceptance TMP Updated"
    r6 = client.put(f"/catalog/selections/{slug}", json=updated)
    expect(r6.status_code == 200, "M1 update selection", results)

    # M2: param binding (unit-level)
    spec = SelectionSpec.model_validate(updated)
    params_map = bind_params_for_selection(spec, {"start_date": "20210101", "end_date": "20211231"})
    ok_params = params_map.get(spec.selection[0].endpoint, {})
    expect(ok_params.get("start_date") == "20210101" and ok_params.get("end_date") == "20211231", "M2 param binding selection", results)

    # ts_code list binding test
    item = SelectionItem(
        endpoint="daily_basic",
        fields=["ts_code"],
        param_binding={"ts_code": ParamBindingRequestArg(type="request_arg", name="ts_codes")},
        join_keys=["ts_code"],
    )
    _, ts_codes = bind_params_for_item(item, {"ts_codes": ["000001.SZ", "600000.SH"]})
    expect(ts_codes == ["000001.SZ", "600000.SH"], "M2 ts_code iteration binding", results)

    # M3: codegen
    r7 = client.post("/factors/codegen", json={"selection_slug": "val_low_combo", "user_factor_spec": "neutral"})
    j7 = r7.json()
    expect(r7.status_code == 200 and bool(j7.get("code_text")), "M3 codegen returns code", results)
    expect(len(j7.get("fields_used", [])) >= 1, "M3 codegen fields_used", results)

    # M3: validate ok
    code_ok = (
        "import pandas as pd\n\n"
        "def compute_factor(data, params):\n"
        "    df = data['daily_basic'].copy()\n"
        "    df['factor'] = -df['pe_ttm'] + -df['pb']\n"
        "    return df\n"
    )
    r8 = client.post("/factors/validate", json={"code_text": code_ok, "selection": base_sel})
    expect(r8.status_code == 200 and r8.json().get("ok") is True, "M3 validate ok", results)

    # M3: validate bad
    code_bad = (
        "import os\n\n"
        "def compute_factor(data, params):\n"
        "    df = data['daily_basic'].copy()\n"
        "    df['factor'] = df['unknown_col']\n"
        "    return df\n"
    )
    r9 = client.post("/factors/validate", json={"code_text": code_bad, "selection": base_sel})
    bad = r9.json()
    has_os = any("import 'os' not allowed" in e for e in bad.get("errors", []))
    has_unknown = any("not in selection fields" in e for e in bad.get("errors", []))
    expect(r9.status_code == 200 and (bad.get("ok") is False) and has_os, "M3 validate blocks import os", results)
    expect(has_unknown, "M3 validate blocks unknown field", results)

    print("---- Summary ----")
    print("Passed:", len(results["pass"]))
    print("Failed:", len(results["fail"]), results["fail"])
    return 0 if not results["fail"] else 1


if __name__ == "__main__":
    raise SystemExit(run_acceptance())
