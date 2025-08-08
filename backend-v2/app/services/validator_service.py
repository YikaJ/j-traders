from __future__ import annotations

from typing import Any, Dict, List, Set

from .ast_validator import FactorAstValidator
from .context_builder import build_agent_context, gather_selection_fields
from ..models.selection import SelectionSpec


def validate_code_against_selection(code_text: str, spec: SelectionSpec) -> Dict[str, Any]:
    context = build_agent_context(spec)
    allowed_imports: Set[str] = set(["pandas", "numpy"])  # from context

    validator = FactorAstValidator(allowed_imports=allowed_imports)
    res = validator.validate(code_text, allowed_imports=allowed_imports)

    # field boundary: code may only reference fields within selection fields set
    endpoint_to_fields = gather_selection_fields(spec)
    allowed_fields: Set[str] = set()
    for fields in endpoint_to_fields.values():
        allowed_fields.update(fields)

    allowed_non_field_tokens: Set[str] = set(spec.output_index)
    allowed_non_field_tokens.add("factor")
    # Treat data keys as dataset identifiers, not fields
    allowed_non_field_tokens.update(set(spec.code_contract.data_keys))

    boundary_errors: List[str] = []
    for f in res.fields_used:
        if f in allowed_non_field_tokens:
            continue
        if f not in allowed_fields:
            boundary_errors.append(f"field '{f}' not in selection fields")

    errors = res.errors + boundary_errors
    return {
        "ok": len(errors) == 0,
        "fields_used": res.fields_used,
        "errors": errors,
    }