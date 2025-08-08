from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import ValidationError

from ..models.endpoint import EndpointMeta, Registry

router = APIRouter()

CATALOG_ROOT = Path(__file__).resolve().parents[2] / "catalog"
ENDPOINTS_DIR = CATALOG_ROOT / "endpoints"
REGISTRY_FILE = CATALOG_ROOT / "registry.json"


@router.get("/endpoints")
def list_endpoints() -> list[dict[str, Any]]:
    if not REGISTRY_FILE.exists():
        raise HTTPException(status_code=500, detail="registry.json not found")
    try:
        registry = Registry.model_validate_json(REGISTRY_FILE.read_text(encoding="utf-8"))
    except ValidationError as e:
        raise HTTPException(status_code=500, detail={"error": "registry_invalid", "detail": e.errors()})
    return [e.model_dump() for e in registry.endpoints]


@router.get("/endpoints/{name}")
def get_endpoint(name: str) -> dict[str, Any]:
    file_path = ENDPOINTS_DIR / f"{name}.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"endpoint '{name}' not found")
    try:
        meta = EndpointMeta.model_validate_json(file_path.read_text(encoding="utf-8"))
    except ValidationError as e:
        raise HTTPException(status_code=500, detail={"error": "endpoint_invalid", "detail": e.errors()})
    return meta.model_dump()


@router.get("/fields/search")
def search_fields(q: str = Query(min_length=1)) -> list[dict[str, Any]]:
    # naive scan endpoints to search fields
    results: list[dict[str, Any]] = []
    if not ENDPOINTS_DIR.exists():
        return results
    for json_file in ENDPOINTS_DIR.glob("*.json"):
        meta = json.loads(json_file.read_text(encoding="utf-8"))
        endpoint_name = meta.get("name")
        for field in meta.get("fields", []):
            name = field.get("name", "")
            desc = field.get("desc", "")
            if q.lower() in name.lower() or q.lower() in str(desc).lower():
                results.append({
                    "field": name,
                    "endpoint": endpoint_name,
                    "desc": desc,
                })
    return results
