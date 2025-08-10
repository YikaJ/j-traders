from __future__ import annotations

import builtins
import contextlib
import io
import sys
import types
import signal
import threading
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
        # Provide guarded builtins (including a restricted __import__)
        builtins_dict: Dict[str, Any] = dict(self.safe_builtins)
        builtins_dict["__import__"] = self._guard_import
        g: Dict[str, Any] = {"__builtins__": builtins_dict}
        # provide modules and common aliases (pd/np) to tolerate typical user code
        g.update(self.allowed_modules)
        g.setdefault("pd", pd)
        g.setdefault("np", np)

        # capture prints
        stdout_io = io.StringIO()
        old_stdout = sys.stdout
        # signal 仅能在主线程使用；Notebook/TestClient 可能运行在非主线程
        is_main_thread = threading.current_thread() is threading.main_thread()
        old_handler = signal.getsignal(signal.SIGALRM) if is_main_thread else None
        try:
            sys.stdout = stdout_io
            # exec code
            exec(compile(code_text, "<factor>", "exec"), g, g)
            if "compute_factor" not in g or not callable(g["compute_factor"]):
                return SandboxResult(False, None, stdout_io.getvalue(), "compute_factor not defined")
            # set timeout
            if is_main_thread:
                signal.signal(signal.SIGALRM, self._timeout_handler)
                signal.alarm(self.timeout_seconds)
                res = g["compute_factor"](data, params)
                signal.alarm(0)
            else:
                # 非主线程环境下不使用 signal，直接执行；MVP 暂不强制超时
                res = g["compute_factor"](data, params)
            return SandboxResult(True, res, stdout_io.getvalue(), None)
        except Exception as e:
            return SandboxResult(False, None, stdout_io.getvalue(), str(e))
        finally:
            sys.stdout = old_stdout
            try:
                if is_main_thread:
                    signal.alarm(0)
                    if old_handler is not None:
                        signal.signal(signal.SIGALRM, old_handler)
            except Exception:
                pass
