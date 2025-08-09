from __future__ import annotations

from typing import Any, Dict, List, Tuple

from ..models.selection import ParamBindingFixed, ParamBindingArg, SourceItem, SelectionSpec


def bind_params_for_source(source: SourceItem, request_args: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    params: Dict[str, Any] = {}
    ts_codes: List[str] = []
    for key, binding in source.params.items():
        if isinstance(binding, ParamBindingFixed):
            params[key] = binding.value
        elif isinstance(binding, ParamBindingArg):
            value = request_args.get(key)
            if value is None:
                continue
            if key == "ts_code" and isinstance(value, list):
                ts_codes = [str(v) for v in value]
            else:
                params[key] = value
    return params, ts_codes


def bind_params_for_selection(spec: SelectionSpec, request_args: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Return endpoint_name -> bound params (without ts_code list)."""
    result: Dict[str, Dict[str, Any]] = {}
    for src in spec.sources:
        params, _ = bind_params_for_source(src, request_args)
        result[src.endpoint] = params
    return result
