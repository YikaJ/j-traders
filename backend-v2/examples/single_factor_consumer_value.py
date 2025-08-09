from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from fastapi.testclient import TestClient


def main() -> int:
    backend_v2_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(backend_v2_root))
    from app.main import create_app  # noqa: WPS433, E402

    app = create_app()
    client = TestClient(app)

    # 数据选择（无需持久化）：使用 daily_basic，字段包含股息率TTM、总市值、PE_TTM
    selection: Dict[str, Any] = {
        "join_keys": ["ts_code", "trade_date"],
        "sources": [
            {
                "endpoint": "daily_basic",
                "fields": ["ts_code", "trade_date", "dv_ttm", "total_mv", "pe_ttm"],
                "params": {"start_date": {"type": "arg"}, "end_date": {"type": "arg"}}
            }
        ],
        "constraints": {"winsor": [0.01, 0.99], "zscore_axis": "trade_date"}
    }

    # 通过 LLM 进行代码生成（若未配置 AI，将自动回退脚手架）
    factor_spec = (
        "请生成以 daily_basic 为输入的单因子：偏好‘股息率高(dv_ttm)’、‘总市值大(total_mv)’、‘市盈率低(pe_ttm)’。"
        "函数签名遵循系统约束，仅返回包含 'factor' 列且保留 join_keys 的 DataFrame。"
    )
    cg = client.post("/factors/codegen", json={"selection": selection, "user_factor_spec": factor_spec, "coding_prefs": {}})
    if cg.status_code != 200:
        print("[FAIL] codegen:", cg.status_code, cg.text)
        return 1
    code_text = cg.json().get("code_text") or ""
    print("[PASS] codegen ok, code length:", len(code_text))

    # 验证
    v = client.post("/factors/validate", json={"code_text": code_text, "selection": selection})
    if v.status_code != 200 or not v.json().get("ok"):
        print("[FAIL] validate:", v.status_code, v.json())
        return 1
    print("[PASS] validate ok")

    # 保存因子
    save_body = {
        "name": "consumer_value_single",
        "desc": "偏好高股息、大盘、低PE（消费行业在运行时通过股票池筛选）",
        "code_text": code_text,
        "fields_used": ["ts_code", "trade_date", "dv_ttm", "total_mv", "pe_ttm"],
        "normalization": {"method": "zscore", "winsor": [0.01, 0.99], "fill": "median"},
        "tags": ["value", "yield", "size"],
        "selection": selection,
    }
    r_save = client.post("/factors", json=save_body)
    if r_save.status_code != 200:
        print("[FAIL] save factor:", r_save.status_code, r_save.text)
        return 1
    factor_id = r_save.json().get("id")
    print(f"[PASS] save factor id={factor_id}")

    # 策略：单因子，权重=1
    r_create = client.post("/strategies", json={"name": "consumer_single", "normalization": {"method": "zscore", "winsor": [0.01, 0.99], "fill": "median"}})
    if r_create.status_code != 200:
        print("[FAIL] create strategy:", r_create.status_code, r_create.text)
        return 1
    strategy_id = r_create.json().get("id")
    print(f"[PASS] create strategy id={strategy_id}")

    r_w = client.put(f"/strategies/{strategy_id}/weights", json={"weights": [{"factor_id": factor_id, "weight": 1.0}]})
    if r_w.status_code != 200:
        print("[FAIL] set weights:", r_w.status_code, r_w.text)
        return 1
    print("[PASS] set weight = 1.0")

    # 快速测试（不依赖真实 TuShare，可回退合成数据）
    ts_codes: List[str] = ["600519.SH", "000858.SZ", "600887.SH"]
    test_body = {
        "selection": selection,
        "code_text": code_text,
        "params": {},
        "ts_codes": ts_codes,
        "start_date": "20210101",
        "end_date": "20210108",
        "normalization": {"method": "zscore", "winsor": [0.01, 0.99], "fill": "median", "by": ["trade_date"]},
        "top_n": 5,
    }
    r_test = client.post("/factors/test", json=test_body)
    if r_test.status_code == 200:
        js = r_test.json()
        print("[PASS] factors/test sample_rows:")
        print(json.dumps(js.get("sample_rows", []), ensure_ascii=False, indent=2))
        print("diagnosis:", js.get("diagnosis"))
    else:
        print("[WARN] factors/test:", r_test.status_code, r_test.text)

    # 尝试运行策略（需要 TUSHARE_TOKEN；若未配置将提示失败信息）
    try:
        run_body = {
            "ts_codes": ts_codes,
            "start_date": "20210101",
            "end_date": "20210108",
            "top_n": 5,
            # 新增：每期（按 trade_date）Top N 结果，便于“按期筛选标的”
            "per_date_top_n": 5,
        }
        r_run = client.post(f"/strategies/{strategy_id}/run", json=run_body)
        if r_run.status_code == 200:
            data = r_run.json()
            print("[PASS] strategies/run results (global topN):")
            print(json.dumps({"results": data.get("results", []), "group_by": data.get("group_by")}, ensure_ascii=False, indent=2))
            if data.get("per_date_results"):
                print("[PASS] strategies/run per-date topN:")
                print(json.dumps(data.get("per_date_results"), ensure_ascii=False, indent=2))
        else:
            print("[INFO] strategies/run 可能需要已配置的 TUSHARE_TOKEN:", r_run.status_code, r_run.text)
    except Exception as e:  # noqa: BLE001
        print("[INFO] 跳过 strategies/run:", str(e))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


