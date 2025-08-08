from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from pathlib import Path
import json

from .client import LLMClient, LLMMessage


@dataclass
class CodegenResult:
    code_text: str
    notes: Optional[str] = None


class CodegenAgent:
    def __init__(self, llm: Optional[LLMClient]) -> None:
        self.llm = llm

    def _build_messages(self, context: Dict[str, Any], user_factor_spec: str, coding_prefs: Optional[Dict[str, Any]]) -> List[LLMMessage]:
        # Load system prompt template if available, otherwise fallback to a built-in one
        # Locate prompt under app/prompts/FactorCoder.md
        tmpl_path = Path(__file__).resolve().parents[3] / "prompts" / "FactorCoder.md"
        if tmpl_path.exists():
            raw = tmpl_path.read_text(encoding="utf-8")
            # derive helper placeholders
            try:
                sel = context.get("selection", {})
                items = sel.get("selection", [])
                fields = []
                for it in items:
                    fields.extend(it.get("fields", []))
                allowed_fields = sorted(sorted(set(fields)))
            except Exception:
                allowed_fields = []
            output_index = context.get("output_index", [])

            system = (
                raw
                .replace("{{SELECTION_CONTEXT_JSON}}", json.dumps(context, ensure_ascii=False))
                .replace("{{USER_FACTOR_SPEC}}", user_factor_spec)
                .replace("{{ALLOWED_FIELDS}}", ", ".join(allowed_fields))
                .replace("{{OUTPUT_INDEX}}", ", ".join(output_index))
            )
        else:
            system = (
                "你是量化研究编码助手。请只生成 Python 代码，函数签名：\n"
                "def compute_factor(data: dict[str, pd.DataFrame], params: dict) -> pd.DataFrame\n"
                "约束：仅可使用 pandas/numpy；禁止 IO/网络/子进程/动态导入/反射；输出需保留 output_index，且包含 'factor' 列。\n\n"
                "[SELECTION_CONTEXT_JSON]\n" + json.dumps(context, ensure_ascii=False) + "\n\n"
                "[USER_FACTOR_SPEC]\n" + user_factor_spec + "\n\n"
                "只返回代码，不要解释或 Markdown。"
            )
        user = "请根据以上上下文生成 compute_factor，并仅返回代码。"
        return [LLMMessage(role="system", content=system), LLMMessage(role="user", content=user)]

    def generate(self, context: Dict[str, Any], user_factor_spec: str, coding_prefs: Optional[Dict[str, Any]]) -> CodegenResult:
        if self.llm is None:
            # Fallback scaffold
            scaffold = (
                "def compute_factor(data, params):\n"
                "    import pandas as pd\n"
                "    key = next(iter(data.keys()))\n"
                "    df = data[key].copy()\n"
                "    df['factor'] = 0.0\n"
                "    return df\n"
            )
            return CodegenResult(code_text=scaffold, notes="scaffold: llm disabled")

        messages = self._build_messages(context, user_factor_spec, coding_prefs)
        prefs = coding_prefs or {}
        model = prefs.get("model") or "gpt-4o-mini"
        temperature = float(prefs.get("temperature", 0.0))
        max_tokens = int(prefs.get("max_tokens", 1200))
        extra = prefs.get("extra")
        code = self.llm.complete(
            messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            extra=extra,
        )
        sanitized = self._postprocess_code(code)
        return CodegenResult(code_text=sanitized)

    def _postprocess_code(self, raw: str) -> str:
        text = (raw or "").strip()
        # 1) Extract from fenced code if present
        if "```" in text:
            try:
                first = text.index("```")
                rest = text[first + 3 :]
                # drop an optional language tag like "python" immediately after the fence
                if rest.lower().startswith("python"):
                    # remove leading 'python' and an optional newline
                    rest = rest[len("python") :]
                    if rest.startswith("\n"):
                        rest = rest[1:]
                if "```" in rest:
                    text = rest[: rest.index("```")].strip()
                else:
                    text = rest.strip()
            except Exception:
                # fall through with original text
                pass

        # 2) If extra prose remains, try to slice from the function signature
        if "def compute_factor" in text:
            text = text[text.index("def compute_factor") :].strip()

        # 3) Ensure it is not empty and looks like Python
        if not text or "def compute_factor" not in text:
            scaffold = (
                "def compute_factor(data, params):\n"
                "    import pandas as pd\n"
                "    key = next(iter(data.keys()))\n"
                "    df = data[key].copy()\n"
                "    df['factor'] = 0.0\n"
                "    return df\n"
            )
            return scaffold

        return text
