from __future__ import annotations

from typing import Any, List, Dict

import pandas as pd
from fastapi import APIRouter, HTTPException

from ..models.factor import (
    CodegenRequest,
    CodegenResponse,
    TestRequest,
    TestResponse,
    ValidateRequest,
    ValidateResponse,
    SampleRequest,
    SampleResponse,
)
from ..models.selection import SelectionSpec
from ..services.context_builder import (
    gather_selection_fields,
    build_agent_context,
    load_endpoint_meta,
)
from ..services.validator_service import validate_code_against_selection
from ..services.ast_validator import FactorAstValidator
from ..core.config import load_settings
from ..services.ai.client import create_llm_client
from ..services.ai.agent import CodegenAgent
from ..services.sandbox import RestrictedSandbox
from ..services.standardize import zscore_df, compute_diagnostics
from ..services.tushare_client import TuShareClient
from ..services.param_binding import bind_params_for_source

router = APIRouter(prefix="/factors", tags=["factors"])


def _flatten_fields(fields_map: dict[str, set[str]]) -> List[str]:
    flat: List[str] = []
    for s in fields_map.values():
        flat.extend(list(s))
    return sorted(sorted(set(flat)))


@router.post("/sample", response_model=SampleResponse)
def sample_data(req: SampleRequest) -> Any:
    # 从 TuShare 抓取真实样本（带缓存）。不再生成 fallback 合成数据。
    spec: SelectionSpec = req.selection

    tickers = req.ts_codes or []

    ts_client: TuShareClient | None = None
    try:
        ts_client = TuShareClient()
    except Exception:
        ts_client = None

    out: Dict[str, List[Dict[str, Any]]] = {}
    notes: List[str] = []

    # 组合可用于绑定的请求参数：通用 request_args + 显式起止日期 + ts_codes
    request_args: Dict[str, Any] = dict(req.request_args or {})
    if req.start_date:
        request_args["start_date"] = req.start_date
    if req.end_date:
        request_args["end_date"] = req.end_date
    if req.ts_codes:
        # 适配绑定器，允许前端传入 ts_codes 数组
        request_args["ts_codes"] = req.ts_codes

    for item in spec.sources:
        df: pd.DataFrame | None = None
        if ts_client is not None:
            try:
                meta = load_endpoint_meta(item.endpoint)
                # bind params based on selection + request_args
                bound_params, iter_ts = bind_params_for_source(item, request_args)
                # include fields (requested columns) — 仅保留该端点合法字段，避免 Tushare 因未知字段报错
                try:
                    if isinstance(meta, dict):
                        fields_meta = meta.get("fields") or []
                        valid_fields = {str(f.get("name")) for f in fields_meta if isinstance(f, dict) and f.get("name")}
                    else:
                        valid_fields = {str(getattr(f, "name")) for f in getattr(meta, "fields", [])}
                except Exception:
                    valid_fields = set()
                need_cols_all = list(sorted(set(item.fields + spec.join_keys)))
                need_cols = [c for c in need_cols_all if (not valid_fields or c in valid_fields)]
                if need_cols:
                    bound_params["fields"] = ",".join(need_cols)
                # 决定迭代列表：优先 sources.param 绑定出的 ts_code 列表；其次使用 bound_params 中的单个 ts_code；再其次使用请求体的 ts_codes；否则不迭代
                iter_list = list(iter_ts or [])
                if not iter_list:
                    single_ts = bound_params.get("ts_code")
                    if isinstance(single_ts, str) and single_ts.strip():
                        iter_list = [single_ts.strip()]
                        # 交给迭代器设置 ts_code，避免重复
                        bound_params.pop("ts_code", None)
                if not iter_list:
                    iter_list = tickers
                if iter_list:
                    pulled = ts_client.fetch_iter_ts_codes(meta, bound_params, iter_list)
                else:
                    pulled = ts_client.fetch(meta, bound_params)
                if pulled is not None and not pulled.empty:
                    need_cols_set = set(need_cols or (item.fields + spec.join_keys))
                    present = [c for c in pulled.columns if c in need_cols_set] or list(pulled.columns)
                    df = pulled[present].copy()
            except Exception as e:  # noqa: BLE001
                notes.append(f"fetch failed for {item.endpoint}: {e}")
                df = None
        # 不再生成 fallback。若无数据，返回空数组并附注说明。
        if df is None or df.empty:
            notes.append(f"no_data_for {item.endpoint}")
            out[item.endpoint] = []
        else:
            out[item.endpoint] = df.head(req.top_n).to_dict(orient="records")

    return SampleResponse(data=out, notes="; ".join(notes) if notes else None)


@router.post("/codegen", response_model=CodegenResponse)
def codegen(req: CodegenRequest) -> Any:
    spec: SelectionSpec = req.selection

    fields_map = gather_selection_fields(spec)
    fields_used = _flatten_fields(fields_map)

    # Build context and try agent
    context = build_agent_context(spec)
    settings = load_settings()
    # 允许通过 req.coding_prefs 覆盖模型名称与额外 body（如 DashScope 的 enable_thinking）
    llm = create_llm_client(endpoint=settings.ai_endpoint, api_key=settings.ai_api_key)
    agent = CodegenAgent(llm)
    # 若未显式传入模型，使用配置的默认模型
    coding_prefs = dict(req.coding_prefs or {})
    if "model" not in coding_prefs and settings.ai_model:
        coding_prefs["model"] = settings.ai_model
    result = agent.generate(context, req.user_factor_spec, coding_prefs)

    return CodegenResponse(code_text=result.code_text, fields_used=fields_used, notes=result.notes or "")


@router.post("/validate", response_model=ValidateResponse)
def validate(req: ValidateRequest) -> Any:
    spec: SelectionSpec = req.selection

    result = validate_code_against_selection(req.code_text, spec)

    # if required_fields provided, re-run quick check on detected fields
    if req.required_fields:
        missing = [f for f in req.required_fields if f not in result["fields_used"]]
        if missing:
            result["errors"] = result["errors"] + [f"required field '{f}' not referenced in code" for f in missing]
            result["ok"] = False

    return ValidateResponse(ok=result["ok"], fields_used=result["fields_used"], errors=result["errors"]) 


@router.post("/test", response_model=TestResponse)
def test_factor(req: TestRequest) -> Any:
    # simulate small sample data from selection, execute code in sandbox, then preview zscore
    spec: SelectionSpec = req.selection

    # 1) build small sample per endpoint: prefer TuShare (cached); fallback to synthetic with perturbation
    data: Dict[str, pd.DataFrame] = {}
    tickers = req.ts_codes or ["000001.SZ", "600000.SH"]
    dates = [req.start_date or "20210101", req.end_date or "20210108"]

    # try init TuShare client; if unavailable, fallback later
    ts_client: TuShareClient | None = None
    try:
        ts_client = TuShareClient()
    except Exception:
        ts_client = None

    for item in spec.sources:
        df: pd.DataFrame | None = None
        if ts_client is not None:
            try:
                meta = load_endpoint_meta(item.endpoint)
                base_params: Dict[str, Any] = {}
                if req.start_date:
                    base_params["start_date"] = req.start_date
                if req.end_date:
                    base_params["end_date"] = req.end_date
                pulled = ts_client.fetch_iter_ts_codes(meta, base_params, tickers)
                if pulled is not None and not pulled.empty:
                    need_cols = set(item.fields + spec.join_keys)
                    present = [c for c in pulled.columns if c in need_cols]
                    if present:
                        df = pulled[present].copy()
                        if not set(spec.join_keys).issubset(set(df.columns)):
                            df = None
            except Exception:
                df = None

        if df is None or df.empty:
            rows: List[Dict[str, Any]] = []
            for ts in tickers:
                for d in dates:
                    row: Dict[str, Any] = {}
                    for f in set(item.fields + spec.join_keys):
                        if f == "ts_code":
                            row[f] = ts
                        elif f in ("trade_date", "end_date"):
                            row[f] = d
                        else:
                            idx_t = tickers.index(ts)
                            idx_d = dates.index(d)
                            row[f] = 1.0 + 0.2 * idx_t + 0.1 * idx_d
                    rows.append(row)
            df = pd.DataFrame(rows)

        data[item.endpoint] = df

    # 2) run in sandbox
    sb = RestrictedSandbox()
    res = sb.exec_compute(req.code_text, data, req.params or {})
    if not res.ok or not isinstance(res.result, pd.DataFrame):
        return TestResponse(sample_rows=[], diagnosis={"error": res.error or "execution_failed", "stdout": res.stdout})

    out_df: pd.DataFrame = res.result
    # 3) standardization preview (zscore)
    norm = req.normalization
    if norm is not None:
        by = norm.by or spec.join_keys[-1:]
        out_df = zscore_df(out_df, value_col="factor", by=by, winsor=norm.winsor, fill=norm.fill)

    # 4) diagnosis
    diag = compute_diagnostics(out_df["factor"]) if "factor" in out_df.columns else {}

    # 5) sample rows
    sample = out_df.head(req.top_n).to_dict(orient="records")

    return TestResponse(sample_rows=sample, diagnosis=diag)
