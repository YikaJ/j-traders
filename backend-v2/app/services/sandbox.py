from __future__ import annotations

import builtins
import contextlib
import io
import sys
import types
import signal
from dataclasses import dataclass
from typing import Any, Dict

import numpy as np
import pandas as pd


@dataclass
class SandboxResult:
    ok: bool
    result: Any | None
    stdout: str
    error: str | None


class RestrictedSandbox:
    def __init__(self, timeout_seconds: int = 2) -> None:
        self.timeout_seconds = timeout_seconds
        self.safe_builtins = {
            "abs": abs,
            "min": min,
            "max": max,
            "range": range,
            "len": len,
            "sum": sum,
            "enumerate": enumerate,
            "zip": zip,
            "map": map,
            "filter": filter,
            "float": float,
            "int": int,
            "str": str,
            "bool": bool,
            "list": list,
            "dict": dict,
            "set": set,
            "tuple": tuple,
        }
        self.allowed_modules = {
            "numpy": np,
            "pandas": pd,
        }

    def _guard_import(self, name: str, globals_dict: Dict[str, Any], locals_dict: Dict[str, Any], fromlist: Any, level: int = 0):
        root = name.split(".")[0]
        if root in self.allowed_modules:
            return self.allowed_modules[root]
        raise ImportError(f"import of '{root}' is not allowed in sandbox")

    def _timeout_handler(self, signum, frame):  # type: ignore[no-untyped-def]
        raise TimeoutError("sandbox execution timed out")

    def exec_compute(self, code_text: str, data: Dict[str, pd.DataFrame], params: Dict[str, Any]) -> SandboxResult:
        g: Dict[str, Any] = {
            "__builtins__": self.safe_builtins,
        }
        # provide modules
        g.update(self.allowed_modules)

        # capture prints
        stdout_io = io.StringIO()
        old_stdout = sys.stdout
        old_handler = signal.getsignal(signal.SIGALRM)
        try:
            sys.stdout = stdout_io
            # allow only whitelisted imports
            g["__import__"] = self._guard_import
            # exec code
            exec(compile(code_text, "<factor>", "exec"), g, g)
            if "compute_factor" not in g or not callable(g["compute_factor"]):
                return SandboxResult(False, None, stdout_io.getvalue(), "compute_factor not defined")
            # set timeout
            signal.signal(signal.SIGALRM, self._timeout_handler)
            signal.alarm(self.timeout_seconds)
            res = g["compute_factor"](data, params)
            signal.alarm(0)
            return SandboxResult(True, res, stdout_io.getvalue(), None)
        except Exception as e:
            return SandboxResult(False, None, stdout_io.getvalue(), str(e))
        finally:
            sys.stdout = old_stdout
            try:
                signal.alarm(0)
                if old_handler is not None:
                    signal.signal(signal.SIGALRM, old_handler)
            except Exception:
                pass
