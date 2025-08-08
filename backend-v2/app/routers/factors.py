from __future__ import annotations

from typing import Any, List

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
from ..services.context_builder import load_selection_by_slug, gather_selection_fields
from ..services.validator_service import validate_code_against_selection
from ..services.ast_validator import FactorAstValidator

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

    # MVP scaffold code: create a neutral factor column
    code_text = (
        "def compute_factor(data, params):\n"
        "    import pandas as pd\n"
        "    # pick the first dataset from provided data dict\n"
        "    key = next(iter(data.keys()))\n"
        "    df = data[key].copy()\n"
        "    df['factor'] = 0.0\n"
        "    return df\n"
    )
    return CodegenResponse(code_text=code_text, fields_used=fields_used, notes="scaffold: neutral factor=0.0")


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
    # TODO: implement data fetch + sandbox exec + normalization preview
    return TestResponse(sample_rows=[], diagnosis={})
