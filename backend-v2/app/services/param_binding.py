from __future__ import annotations

from typing import Any, Dict, List, Tuple

from ..models.selection import ParamBindingFixed, ParamBindingRequestArg, SelectionItem, SelectionSpec


def bind_params_for_item(item: SelectionItem, request_args: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    params: Dict[str, Any] = {}
    ts_codes: List[str] = []
    for key, binding in item.param_binding.items():
        if isinstance(binding, ParamBindingFixed):
            params[key] = binding.value
        elif isinstance(binding, ParamBindingRequestArg):
            value = request_args.get(binding.name)
            if value is None:
                continue
            # Special case: map a list of ts_codes to ts_code iteration
            if key == "ts_code" and isinstance(value, list):
                ts_codes = [str(v) for v in value]
            else:
                params[key] = value
        else:
            # derived rules not implemented in MVP
            pass
    return params, ts_codes


def bind_params_for_selection(spec: SelectionSpec, request_args: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Return endpoint_name -> bound params (without ts_code list)."""
    result: Dict[str, Dict[str, Any]] = {}
    for item in spec.selection:
        params, _ = bind_params_for_item(item, request_args)
        result[item.endpoint] = params
    return result
