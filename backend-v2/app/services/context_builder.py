from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

from ..models.endpoint import EndpointMeta
from ..models.selection import SelectionSpec


CATALOG_ROOT = Path(__file__).resolve().parents[2] / "catalog"
ENDPOINTS_DIR = CATALOG_ROOT / "endpoints"


# Persistent selections are removed in current stage.


def load_endpoint_meta(name: str) -> EndpointMeta:
    file_path = ENDPOINTS_DIR / f"{name}.json"
    if not file_path.exists():
        raise FileNotFoundError(f"endpoint '{name}' not found in catalog")
    return EndpointMeta.model_validate_json(file_path.read_text(encoding="utf-8"))


def gather_selection_fields(spec: SelectionSpec) -> Dict[str, Set[str]]:
    endpoint_to_fields: Dict[str, Set[str]] = {}
    for src in spec.sources:
        endpoint_to_fields.setdefault(src.endpoint, set()).update(src.fields)
    return endpoint_to_fields


def build_agent_context(spec: SelectionSpec) -> Dict[str, Any]:
    endpoints: Dict[str, Dict[str, Any]] = {}
    for src in spec.sources:
        meta = load_endpoint_meta(src.endpoint)
        endpoints[src.endpoint] = meta.model_dump()

    context: Dict[str, Any] = {
        "selection": spec.model_dump(),
        "endpoints": endpoints,
        "join_keys": spec.join_keys,
        "constraints": spec.constraints.model_dump() if spec.constraints else None,
        "allowed_imports": ["pandas", "numpy"],
        "denied_capabilities": [
            "io",
            "network",
            "subprocess",
            "dynamic_import",
            "reflection",
        ],
    }
    return context
