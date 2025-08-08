from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import List, Set, Tuple


BANNED_IMPORTS = {
    "os",
    "sys",
    "subprocess",
    "socket",
    "pathlib",
    "importlib",
    "builtins",
    "inspect",
    "ctypes",
    "multiprocessing",
    "threading",
    "asyncio",
}

BANNED_NODES = (
    ast.Exec if hasattr(ast, "Exec") else tuple(),  # type: ignore
)


@dataclass
class AstValidationResult:
    ok: bool
    fields_used: List[str]
    errors: List[str]


class FactorAstValidator:
    def __init__(self, allowed_imports: Set[str] | None = None) -> None:
        self.allowed_imports: Set[str] = set(allowed_imports or {"pandas", "numpy"})

    def _error(self, errors: List[str], msg: str) -> None:
        errors.append(msg)

    def _check_imports(self, tree: ast.AST, errors: List[str]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod = alias.name.split(".")[0]
                    if mod not in self.allowed_imports:
                        self._error(errors, f"import '{mod}' not allowed")
            elif isinstance(node, ast.ImportFrom):
                mod = (node.module or "").split(".")[0]
                if mod and mod not in self.allowed_imports:
                    self._error(errors, f"from '{mod}' import ... not allowed")

    def _check_banned_nodes(self, tree: ast.AST, errors: List[str]) -> None:
        banned_call_names = {"open", "eval", "exec", "__import__"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = self._resolve_call_name(node.func)
                if name in banned_call_names:
                    self._error(errors, f"call to '{name}' is banned")
            if isinstance(node, (ast.Attribute,)):
                # rough reflection guard
                if isinstance(node.value, ast.Name) and node.value.id in {"__builtins__", "__loader__", "__spec__"}:
                    self._error(errors, "access to builtin/loader/spec is banned")

    def _resolve_call_name(self, func: ast.AST) -> str | None:
        if isinstance(func, ast.Name):
            return func.id
        if isinstance(func, ast.Attribute):
            return func.attr
        return None

    def _extract_fields_used(self, tree: ast.AST) -> List[str]:
        # Heuristic: look for string constants that look like field names, and DataFrame column access via df['col']
        fields: Set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Subscript):
                # pattern: something['field']
                try:
                    if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
                        fields.add(node.slice.value)
                except Exception:
                    pass
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                # ignore long strings (likely docstrings)
                if 0 < len(node.value) <= 64 and "\n" not in node.value:
                    fields.add(node.value)
        return sorted(fields)

    def _check_signature(self, tree: ast.AST, errors: List[str]) -> None:
        # must define def compute_factor(data, params)
        found = False
        for node in tree.body:  # type: ignore[attr-defined]
            if isinstance(node, ast.FunctionDef) and node.name == "compute_factor":
                found = True
                if len(node.args.args) < 2:
                    self._error(errors, "compute_factor must accept at least (data, params)")
                break
        if not found:
            self._error(errors, "compute_factor function not found")

    def validate(self, code_text: str, required_fields: List[str] | None = None, allowed_imports: Set[str] | None = None) -> AstValidationResult:
        errors: List[str] = []
        try:
            tree = ast.parse(code_text)
        except SyntaxError as e:
            return AstValidationResult(ok=False, fields_used=[], errors=[f"syntax_error: {e}"])

        if allowed_imports is not None:
            self.allowed_imports = set(allowed_imports)

        self._check_signature(tree, errors)
        self._check_imports(tree, errors)
        self._check_banned_nodes(tree, errors)
        fields_used = self._extract_fields_used(tree)

        if required_fields:
            for f in required_fields:
                if f not in fields_used:
                    self._error(errors, f"required field '{f}' not referenced in code")

        return AstValidationResult(ok=len(errors) == 0, fields_used=fields_used, errors=errors)