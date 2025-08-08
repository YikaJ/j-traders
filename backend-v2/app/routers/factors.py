from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from ..models.factor import (
    CodegenRequest,
    CodegenResponse,
    TestRequest,
    TestResponse,
    ValidateRequest,
    ValidateResponse,
)

router = APIRouter(prefix="/factors", tags=["factors"])


@router.post("/codegen", response_model=CodegenResponse)
def codegen(req: CodegenRequest) -> Any:
    # MVP scaffold: return placeholder code
    code_text = (
        "def compute_factor(data: dict[str, pd.DataFrame], params: dict) -> pd.DataFrame:\n"
        "    import pandas as pd\n"
        "    df = data[next(iter(data.keys()))].copy()\n"
        "    df['factor'] = 0.0\n"
        "    return df\n"
    )
    return CodegenResponse(code_text=code_text, fields_used=[], notes="scaffold")


@router.post("/validate", response_model=ValidateResponse)
def validate(req: ValidateRequest) -> Any:
    # TODO: implement AST/sandbox checks
    return ValidateResponse(ok=True, fields_used=[], errors=[])


@router.post("/test", response_model=TestResponse)
def test_factor(req: TestRequest) -> Any:
    # TODO: implement data fetch + sandbox exec + normalization preview
    return TestResponse(sample_rows=[], diagnosis={})
