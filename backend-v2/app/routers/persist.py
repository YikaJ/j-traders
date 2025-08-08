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
)
from ..storage.db import (
    insert_factor,
    get_factor,
    list_factors,
    insert_strategy,
    get_strategy,
    upsert_strategy_weights,
    update_strategy_normalization,
)
from ..services.sandbox import RestrictedSandbox
from ..services.standardize import zscore_df
import pandas as pd

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


@router.post("/strategies", response_model=Dict[str, Any])
def create_strategy(body: StrategyCreate) -> Any:
    sid = insert_strategy(name=body.name, normalization=body.normalization)
    return {"id": sid}


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

    ts_codes: List[str] = body.get("ts_codes") or ["000001.SZ", "600000.SH"]
    dates: List[str] = [body.get("start_date") or "20210101", body.get("end_date") or "20210108"]
    top_n: int = int(body.get("top_n") or 5)

    sb = RestrictedSandbox()

    combined: Optional[pd.DataFrame] = None
    group_by: List[str] = None

    for w in weights:
        f = get_factor(int(w["factor_id"]))
        if f is None:
            continue
        sel = f.get("selection") or {}
        output_index: List[str] = sel.get("output_index") or ["ts_code", sel.get("code_contract", {}).get("axis", "trade_date")]
        group_by = group_by or output_index[-1:]
        # prepare fields
        fields_used: List[str] = f.get("fields_used") or []
        fields = list(set(fields_used + output_index))
        data_keys: List[str] = sel.get("code_contract", {}).get("data_keys") or ["daily_basic"]
        data: Dict[str, pd.DataFrame] = {}
        for key in data_keys:
            rows: List[Dict[str, Any]] = []
            for ts in ts_codes:
                for d in dates:
                    row: Dict[str, Any] = {}
                    for fld in fields:
                        if fld == "ts_code":
                            row[fld] = ts
                        elif fld in ("trade_date", "end_date"):
                            row[fld] = d
                        else:
                            row[fld] = 1.0
                    rows.append(row)
            data[key] = pd.DataFrame(rows)
        # execute factor
        res = sb.exec_compute(f.get("code_text", ""), data, {})
        if not res.ok or not isinstance(res.result, pd.DataFrame) or "factor" not in res.result.columns:
            # fallback: use synthetic constant factor
            df = data[data_keys[0]].copy()
            df["factor"] = 0.0
        else:
            df = res.result
        # standardize
        norm = body.get("normalization_override") or strat.get("normalization") or {"method": "zscore", "winsor": [0.01, 0.99], "fill": "median"}
        df = zscore_df(df, value_col="factor", by=group_by, winsor=norm.get("winsor"), fill=norm.get("fill", "median"))
        df = df.assign(**{f"factor_{f['id']}": df["factor"] * float(w["weight"])})
        key_cols = [c for c in output_index if c in df.columns]
        part = df[key_cols + [f"factor_{f['id']}"]]
        combined = part if combined is None else combined.merge(part, on=key_cols, how="inner")

    if combined is None or combined.empty:
        return {"results": [], "notes": "no factor produced output"}

    weight_cols = [c for c in combined.columns if c.startswith("factor_")]
    combined["score"] = combined[weight_cols].sum(axis=1)
    combined = combined.sort_values("score", ascending=False)
    results = combined.head(top_n).to_dict(orient="records")
    return {"results": results, "group_by": group_by}
