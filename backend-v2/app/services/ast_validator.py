from __future__ import annotations

import ast
import re
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
                if isinstance(node.value, ast.Name) and node.value.id in {"__builtins__", "__loader__", "__spec__"}:
                    self._error(errors, "access to builtin/loader/spec is banned")

    def _resolve_call_name(self, func: ast.AST) -> str | None:
        if isinstance(func, ast.Name):
            return func.id
        if isinstance(func, ast.Attribute):
            return func.attr
        return None

    def _extract_subscript_key(self, node: ast.Subscript) -> str | None:
        sl = node.slice
        # Python 3.9+ typically uses ast.Constant for string index
        if isinstance(sl, ast.Constant) and isinstance(sl.value, str):
            return sl.value
        # Older AST had ast.Index
        if hasattr(ast, "Index") and isinstance(sl, ast.Index):  # type: ignore[attr-defined]
            inner = sl.value  # type: ignore[assignment]
            if isinstance(inner, ast.Constant) and isinstance(inner.value, str):
                return inner.value
        # Python 3.13 sometimes shows ast.Name due to source parsing quirks in our here-doc
        if isinstance(sl, ast.Name):
            return sl.id
        return None

    def _extract_fields_used(self, tree: ast.AST) -> List[str]:
        fields: Set[str] = set()
        # 1) df['col'] style
        for node in ast.walk(tree):
            if isinstance(node, ast.Subscript):
                # 忽略 data['endpoint'] 这种用于从 data 取端点 DataFrame 的访问，避免把端点名误判为字段
                try:
                    base = getattr(node, "value", None)
                    if isinstance(base, ast.Name) and base.id == "data":
                        # data['endpoint'] — endpoint 名不是字段
                        pass
                    else:
                        key = self._extract_subscript_key(node)
                        if isinstance(key, str):
                            fields.add(key)
                except Exception:
                    key = self._extract_subscript_key(node)
                    if isinstance(key, str):
                        fields.add(key)
            # 2) df.get('col') style
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get":
                if node.args:
                    arg0 = node.args[0]
                    if isinstance(arg0, ast.Constant) and isinstance(arg0.value, str):
                        fields.add(arg0.value)
        return sorted(fields)

    def _collect_assigned_fields(self, tree: ast.AST) -> Set[str]:
        """Collect column names that are assigned to, e.g., df['new'] = ...
        This allows us to exclude derived columns from boundary checks.
        """
        assigned: Set[str] = set()

        def _add_from_target(target: ast.AST) -> None:
            if isinstance(target, ast.Subscript):
                key = self._extract_subscript_key(target)
                if isinstance(key, str):
                    assigned.add(key)
            # handle tuple/list targets recursively
            if isinstance(target, (ast.Tuple, ast.List)):
                for elt in target.elts:
                    _add_from_target(elt)

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    _add_from_target(t)
            elif isinstance(node, ast.AugAssign):
                _add_from_target(node.target)
            elif hasattr(ast, "AnnAssign") and isinstance(node, ast.AnnAssign):  # type: ignore[attr-defined]
                _add_from_target(node.target)  # type: ignore[arg-type]

        return assigned

    def _check_signature(self, tree: ast.AST, errors: List[str]) -> None:
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
        fields_all = self._extract_fields_used(tree)
        assigned_fields = self._collect_assigned_fields(tree)
        # keep only fields that are read, not those created via assignment
        fields_used = [f for f in fields_all if f not in assigned_fields]

        if required_fields:
            for f in required_fields:
                if f not in fields_used:
                    self._error(errors, f"required field '{f}' not referenced in code")

        return AstValidationResult(ok=len(errors) == 0, fields_used=fields_used, errors=errors)
