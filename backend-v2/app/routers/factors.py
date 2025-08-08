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
)
from ..models.selection import SelectionSpec
from ..services.context_builder import load_selection_by_slug, gather_selection_fields, build_agent_context
from ..services.validator_service import validate_code_against_selection
from ..services.ast_validator import FactorAstValidator
from ..core.config import load_settings
from ..services.ai.client import create_llm_client
from ..services.ai.agent import CodegenAgent
from ..services.sandbox import RestrictedSandbox
from ..services.standardize import zscore_df, compute_diagnostics

router = APIRouter(prefix="/factors", tags=["factors"])


def _flatten_fields(fields_map: dict[str, set[str]]) -> List[str]:
    flat: List[str] = []
    for s in fields_map.values():
        flat.extend(list(s))
    return sorted(sorted(set(flat)))


@router.post("/codegen", response_model=CodegenResponse)
def codegen(req: CodegenRequest) -> Any:
    # resolve selection
    spec: SelectionSpec | None = None
    if req.selection is not None:
        spec = req.selection
    elif req.selection_slug:
        try:
            spec = load_selection_by_slug(req.selection_slug)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="selection slug not found")
    else:
        raise HTTPException(status_code=400, detail="selection or selection_slug is required")

    fields_map = gather_selection_fields(spec)
    fields_used = _flatten_fields(fields_map)

    # Build context and try agent
    context = build_agent_context(spec)
    settings = load_settings()
    llm = create_llm_client(endpoint=settings.ai_endpoint, api_key=settings.ai_api_key)
    agent = CodegenAgent(llm)
    result = agent.generate(context, req.user_factor_spec, req.coding_prefs)

    return CodegenResponse(code_text=result.code_text, fields_used=fields_used, notes=result.notes or "")


@router.post("/validate", response_model=ValidateResponse)
def validate(req: ValidateRequest) -> Any:
    if req.selection is None:
        raise HTTPException(status_code=400, detail="selection is required for validation in MVP")
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
    # MVP: simulate small sample data from selection, execute code in sandbox, then preview zscore
    if req.selection is None:
        raise HTTPException(status_code=400, detail="selection is required for test in MVP")
    spec: SelectionSpec = req.selection

    # 1) build minimal synthetic data for each endpoint
    data: Dict[str, pd.DataFrame] = {}
    for item in spec.selection:
        rows: List[Dict[str, Any]] = []
        # build two dates and two tickers
        tickers = req.ts_codes or ["000001.SZ", "600000.SH"]
        dates = [req.start_date or "20210101", req.end_date or "20210108"]
        for ts in tickers:
            for d in dates:
                row = {}
                for f in set(item.fields + spec.output_index):
                    if f == "ts_code":
                        row[f] = ts
                    elif f in ("trade_date", "end_date"):
                        row[f] = d
                    else:
                        row[f] = 1.0
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
        by = norm.by or spec.output_index[-1:]
        out_df = zscore_df(out_df, value_col="factor", by=by, winsor=norm.winsor, fill=norm.fill)

    # 4) diagnosis
    diag = compute_diagnostics(out_df["factor"]) if "factor" in out_df.columns else {}

    # 5) sample rows
    sample = out_df.head(req.top_n).to_dict(orient="records")

    return TestResponse(sample_rows=sample, diagnosis=diag)
