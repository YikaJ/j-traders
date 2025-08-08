from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List

from fastapi import APIRouter, HTTPException
from pydantic import ValidationError

from ..models.selection import SelectionSpec

router = APIRouter(prefix="/catalog/selections", tags=["selections"])

CATALOG_ROOT = Path(__file__).resolve().parents[2] / "catalog"
SELECTIONS_DIR = CATALOG_ROOT / "selections"

SELECTIONS_DIR.mkdir(parents=True, exist_ok=True)


def _slug_to_path(slug: str) -> Path:
    return SELECTIONS_DIR / f"{slug}.json"


@router.post("")
def create_selection(spec: SelectionSpec) -> dict[str, Any]:
    path = _slug_to_path(spec.factor_slug)
    if path.exists():
        raise HTTPException(status_code=409, detail="selection with this slug already exists")
    data = spec.model_dump()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "slug": spec.factor_slug}


@router.put("/{slug}")
def update_selection(slug: str, body: dict[str, Any]) -> dict[str, Any]:
    path = _slug_to_path(slug)
    if not path.exists():
        raise HTTPException(status_code=404, detail="selection not found")
    try:
        spec = SelectionSpec.model_validate(body)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors())
    if spec.factor_slug != slug:
        raise HTTPException(status_code=400, detail="slug mismatch with body.factor_slug")
    path.write_text(json.dumps(spec.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True}


@router.get("")
def list_selections() -> List[dict[str, str]]:
    results: List[dict[str, str]] = []
    for p in sorted(SELECTIONS_DIR.glob("*.json")):
        results.append({"slug": p.stem})
    return results


@router.get("/{slug}")
def get_selection(slug: str) -> dict[str, Any]:
    path = _slug_to_path(slug)
    if not path.exists():
        raise HTTPException(status_code=404, detail="selection not found")
    return json.loads(path.read_text(encoding="utf-8"))
