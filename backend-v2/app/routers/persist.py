from __future__ import annotations

from typing import Any, Dict, List, Tuple, Optional

from fastapi import APIRouter, HTTPException

from ..models.persist import (
    FactorCreate,
    FactorRecord,
    StrategyCreate,
    StrategyRecord,
    WeightsUpdate,
    NormalizationUpdate,
    FactorUpdate,
    StrategyListItem,
)
from ..storage.db import (
    insert_factor,
    get_factor,
    list_factors,
    insert_strategy,
    get_strategy,
    upsert_strategy_weights,
    update_strategy_normalization,
    update_factor,
    delete_factor,
    list_strategies,
    query_stocks,
)
from ..services.sandbox import RestrictedSandbox
from ..services.standardize import zscore_df
from ..services.context_builder import load_endpoint_meta
from ..services.param_binding import bind_params_for_source
from ..services.tushare_client import TuShareClient
import pandas as pd
import numpy as np

router = APIRouter(tags=["persist"])


@router.post("/factors", response_model=Dict[str, Any])
def save_factor(body: FactorCreate) -> Any:
    factor_id = insert_factor(
        name=body.name,
        desc=body.desc,
        code_text=body.code_text,
        fields_used=body.fields_used,
        normalization=body.normalization,
        tags=body.tags,
        selection=body.selection,
    )
    return {"id": factor_id}


@router.get("/factors", response_model=List[FactorRecord])
def get_factors() -> Any:
    return list_factors()


@router.get("/factors/{factor_id}", response_model=FactorRecord)
def get_factor_by_id(factor_id: int) -> Any:
    rec = get_factor(factor_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="factor not found")
    return rec


@router.put("/factors/{factor_id}", response_model=Dict[str, Any])
def update_factor_by_id(factor_id: int, body: FactorUpdate) -> Any:
    # ensure exists
    rec = get_factor(factor_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="factor not found")
    update_factor(
        factor_id,
        name=body.name,
        desc=body.desc,
        code_text=body.code_text,
        fields_used=body.fields_used,
        normalization=body.normalization,
        tags=body.tags,
        selection=body.selection,
    )
    return {"ok": True}


@router.delete("/factors/{factor_id}", response_model=Dict[str, Any])
def delete_factor_by_id(factor_id: int) -> Any:
    rec = get_factor(factor_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="factor not found")
    delete_factor(factor_id)
    return {"ok": True}


@router.post("/strategies", response_model=Dict[str, Any])
def create_strategy(body: StrategyCreate) -> Any:
    sid = insert_strategy(name=body.name, normalization=body.normalization)
    return {"id": sid}


@router.get("/strategies", response_model=List[StrategyListItem])
def list_strategies_endpoint() -> Any:
    return list_strategies()


@router.put("/strategies/{strategy_id}/weights", response_model=Dict[str, Any])
def update_strategy_weights(strategy_id: int, body: WeightsUpdate) -> Any:
    # normalize weights to L1 by default
    total = sum(abs(w.weight) for w in body.weights) or 1.0
    normed: List[Tuple[int, float]] = [(w.factor_id, float(w.weight) / total) for w in body.weights]
    upsert_strategy_weights(strategy_id, normed)
    if body.normalization is not None:
        update_strategy_normalization(strategy_id, body.normalization)
    return {"ok": True}


@router.put("/strategies/{strategy_id}/normalization", response_model=Dict[str, Any])
def put_strategy_normalization(strategy_id: int, body: NormalizationUpdate) -> Any:
    update_strategy_normalization(strategy_id, body.normalization)
    return {"ok": True}


@router.get("/strategies/{strategy_id}", response_model=StrategyRecord)
def get_strategy_by_id(strategy_id: int) -> Any:
    rec = get_strategy(strategy_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="strategy not found")
    return rec


@router.post("/strategies/{strategy_id}/run", response_model=Dict[str, Any])
def run_strategy(strategy_id: int, body: Dict[str, Any]) -> Any:
    strat = get_strategy(strategy_id)
    if strat is None:
        raise HTTPException(status_code=404, detail="strategy not found")
    weights = strat.get("weights", [])
    if not weights:
        return {"results": [], "notes": "no weights configured"}

    # L1 normalize again for safety
    total = sum(abs(w.get("weight", 0.0)) for w in weights) or 1.0
    weights = [{"factor_id": w["factor_id"], "weight": float(w["weight"]) / total} for w in weights]

    # Universe filtering: prioritize request-provided universe selection
    ts_codes: List[str] = body.get("ts_codes") or []
    industry: Optional[str] = body.get("industry")
    want_all: bool = bool(body.get("all", False))
    if not ts_codes:
        if industry:
            stocks = query_stocks({"industry": industry})
            ts_codes = [s["ts_code"] for s in stocks if s.get("ts_code")]
        elif want_all:
            stocks = query_stocks({})
            ts_codes = [s["ts_code"] for s in stocks if s.get("ts_code")]
    if not ts_codes:
        ts_codes = ["000001.SZ", "600000.SH"]
    start_date: str = body.get("start_date") or "20210101"
    end_date: str = body.get("end_date") or "20210108"
    top_n: int = int(body.get("top_n") or 5)
    want_diag: bool = bool(body.get("diagnostics", {}).get("enabled", True))

    sb = RestrictedSandbox()

    combined: Optional[pd.DataFrame] = None
    group_by: List[str] = None

    for w in weights:
        f = get_factor(int(w["factor_id"]))
        if f is None:
            continue
        sel = f.get("selection") or {}
        join_keys: List[str] = sel.get("join_keys") or ["ts_code", "trade_date"]
        group_by = group_by or join_keys[-1:]
        # prepare fields
        fields_used: List[str] = f.get("fields_used") or []
        if not fields_used:
            # fallback: use fields from sources
            try:
                _sources = sel.get("sources", [])
                acc: List[str] = []
                for _it in _sources:
                    acc.extend((_it.get("fields") or []))
                fields_used = sorted(sorted(set(acc)))
            except Exception:
                fields_used = []
        fields = list(set(fields_used + join_keys))
        # choose first source endpoint as base key if needed
        data_keys: List[str] = [s.get("endpoint") for s in (sel.get("sources") or []) if s.get("endpoint")] or ["daily_basic"]
        data: Dict[str, pd.DataFrame] = {}
        ts_client = TuShareClient()
        # 为每个数据源按 sources.params 绑定请求参数，并真实拉取
        # 附加 Notebook/运行时传入的 start_date/end_date/ts_codes 作为默认覆盖
        request_args = {
            "start_date": start_date,
            "end_date": end_date,
            "ts_codes": ts_codes,
        }
        # sel 是 dict（来自 DB）而非 Pydantic 模型，这里按 dict 访问
        for item in sel.get("sources", []):
            endpoint_name: str = item.get("endpoint")
            if not endpoint_name:
                continue
            endpoint_meta = load_endpoint_meta(endpoint_name)
            # 绑定参数
            class _SourceShim:
                def __init__(self, d: Dict[str, Any]) -> None:
                    self.params = d.get("params", {})

            bound_params, iter_ts = bind_params_for_source(_SourceShim(item), request_args)
            # 限定字段：仅请求本 source 所需字段 + join_keys，减少带宽并利于因子执行
            item_fields = sorted(sorted(set((item.get("fields") or []) + join_keys)))
            if item_fields:
                bound_params["fields"] = ",".join(item_fields)
            # 若未配置 param_binding.ts_code 迭代，但上层提供了 ts_codes，则使用迭代
            iter_list = iter_ts or ts_codes
            # 推断时间参数名（适配 daily_basic: trade_date, cashflow: end_date）
            if endpoint_meta.axis == "trade_date":
                if "start_date" not in bound_params:
                    bound_params["start_date"] = start_date
                if "end_date" not in bound_params:
                    bound_params["end_date"] = end_date
            elif endpoint_meta.axis == "end_date":
                # cashflow 常见用 period/end_date 范围，优先使用 period=end_date 过滤
                if "start_date" in endpoint_meta.params and "end_date" in endpoint_meta.params:  # type: ignore[attr-defined]
                    bound_params.setdefault("start_date", start_date)
                    bound_params.setdefault("end_date", end_date)
                else:
                    bound_params.setdefault("period", end_date)

            # 拉取（按 ts_code 迭代合并）
            if iter_list:
                df = ts_client.fetch_iter_ts_codes(endpoint_meta, bound_params, iter_list)
            else:
                df = ts_client.fetch(endpoint_meta, bound_params)
            # 只保留需要的列，避免无关列干扰
            if not df.empty and item_fields:
                keep_cols = [c for c in item_fields if c in df.columns]
                if keep_cols:
                    df = df[keep_cols]
            data[endpoint_name] = df
        # execute factor
        res = sb.exec_compute(f.get("code_text", ""), data, {})
        if not res.ok or not isinstance(res.result, pd.DataFrame) or "factor" not in res.result.columns:
            # fallback: use synthetic constant factor
            base_key = data_keys[0] if data_keys and data_keys[0] in data else (next(iter(data.keys()), None))
            if base_key is None or data.get(base_key) is None or data.get(base_key).empty:
                return {"results": [], "notes": "no data fetched for selection"}
            df = data[base_key].copy()
            df["factor"] = 0.0
        else:
            df = res.result
        # standardize
        norm = body.get("normalization_override") or strat.get("normalization") or {"method": "zscore", "winsor": [0.01, 0.99], "fill": "median"}
        df = zscore_df(df, value_col="factor", by=group_by, winsor=norm.get("winsor"), fill=norm.get("fill", "median"))
        df = df.assign(**{f"factor_{f['id']}": df["factor"] * float(w["weight"])})
        key_cols = [c for c in join_keys if c in df.columns]
        part = df[key_cols + [f"factor_{f['id']}"]]
        combined = part if combined is None else combined.merge(part, on=key_cols, how="inner")

    if combined is None or combined.empty:
        return {"results": [], "notes": "no factor produced output"}

    weight_cols = [c for c in combined.columns if c.startswith("factor_")]
    combined["score"] = combined[weight_cols].sum(axis=1)
    # Base results for backward-compat (global top_n)
    base_sorted = combined.sort_values("score", ascending=False)
    results = base_sorted.head(top_n).to_dict(orient="records")

    # Cross-sectional selection key
    date_key = (group_by or ["trade_date"])[0]
    if date_key not in combined.columns:
        date_key = "trade_date" if "trade_date" in combined.columns else combined.columns[-1]

    out: Dict[str, Any] = {"results": results, "group_by": group_by}

    # Optional: per-date Top N for screening workflows
    per_date_top_n = int(body.get("per_date_top_n") or 0)
    if per_date_top_n > 0 and date_key in combined.columns:
        per_date: List[Dict[str, Any]] = []
        for d, g in combined.groupby(date_key):
            top_g = (
                g.sort_values("score", ascending=False)
                .head(per_date_top_n)
                .to_dict(orient="records")
            )
            per_date.append({"date": str(d), "items": top_g})
        # sort sections by date ascending for readability
        try:
            per_date = sorted(per_date, key=lambda x: x["date"])  # type: ignore[assignment]
        except Exception:
            pass
        out["per_date_results"] = per_date

    # Diagnostics: IC/RankIC/Coverage
    if want_diag:
        diag: Dict[str, Any] = {}
        try:
            # fetch close prices for forward returns
            endpoint_meta = load_endpoint_meta("daily_basic")
            ts_client = TuShareClient()
            price_df = ts_client.fetch_iter_ts_codes(
                endpoint_meta,
                {"start_date": start_date, "end_date": end_date, "fields": "ts_code,trade_date,close"},
                ts_codes,
            )
            if not price_df.empty:
                price_df = price_df.sort_values(["ts_code", "trade_date"]).copy()
                price_df["fwd_ret"] = price_df.groupby("ts_code")["close"].pct_change(periods=-1)
                # merge on (ts_code, trade_date)
                if "ts_code" in combined.columns and date_key in combined.columns:
                    merged = combined.merge(
                        price_df[["ts_code", "trade_date", "fwd_ret"]],
                        left_on=["ts_code", date_key],
                        right_on=["ts_code", "trade_date"],
                        how="left",
                    )
                    merged = merged.drop(columns=["trade_date_y"], errors="ignore").rename(columns={"trade_date_x": "trade_date"})
                    # compute IC per date then average
                    grp = merged.dropna(subset=["score", "fwd_ret"]).groupby(date_key)
                    ic_list: List[float] = []
                    ric_list: List[float] = []
                    for _, g in grp:
                        if len(g) >= 2:
                            ic = float(np.corrcoef(g["score"], g["fwd_ret"])[0, 1])
                            ic_list.append(ic)
                            ric = float(g["score"].rank().corr(g["fwd_ret"].rank()))
                            ric_list.append(ric)
                    diag["ic_mean"] = float(np.nanmean(ic_list)) if ic_list else None
                    diag["rank_ic_mean"] = float(np.nanmean(ric_list)) if ric_list else None
                    # coverage: non-missing factor fraction per date
                    cov = []
                    for d, g in combined.groupby(date_key):
                        total = len(g)
                        valid = int(g["score"].notna().sum())
                        cov.append(valid / total if total > 0 else np.nan)
                    diag["coverage_mean"] = float(np.nanmean(cov)) if cov else None
        except Exception as e:
            diag = {"error": str(e)}
        out["diagnostics"] = diag

    return out
