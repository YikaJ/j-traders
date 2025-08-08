from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

from ..models.endpoint import EndpointMeta
from ..models.selection import SelectionItem, SelectionSpec


CATALOG_ROOT = Path(__file__).resolve().parents[2] / "catalog"
ENDPOINTS_DIR = CATALOG_ROOT / "endpoints"
SELECTIONS_DIR = CATALOG_ROOT / "selections"


def load_selection_by_slug(slug: str) -> SelectionSpec:
    path = SELECTIONS_DIR / f"{slug}.json"
    if not path.exists():
        raise FileNotFoundError(f"selection '{slug}' not found")
    return SelectionSpec.model_validate_json(path.read_text(encoding="utf-8"))


def load_endpoint_meta(name: str) -> EndpointMeta:
    file_path = ENDPOINTS_DIR / f"{name}.json"
    if not file_path.exists():
        raise FileNotFoundError(f"endpoint '{name}' not found in catalog")
    return EndpointMeta.model_validate_json(file_path.read_text(encoding="utf-8"))


def gather_selection_fields(spec: SelectionSpec) -> Dict[str, Set[str]]:
    endpoint_to_fields: Dict[str, Set[str]] = {}
    for item in spec.selection:
        endpoint_to_fields.setdefault(item.endpoint, set()).update(item.fields)
    return endpoint_to_fields


def build_agent_context(spec: SelectionSpec) -> Dict[str, Any]:
    endpoints: Dict[str, Dict[str, Any]] = {}
    for item in spec.selection:
        meta = load_endpoint_meta(item.endpoint)
        endpoints[item.endpoint] = meta.model_dump()

    context: Dict[str, Any] = {
        "selection": spec.model_dump(),
        "endpoints": endpoints,
        "output_index": spec.output_index,
        "code_contract": spec.code_contract.model_dump(),
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