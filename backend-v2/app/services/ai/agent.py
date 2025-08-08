from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .client import LLMClient, LLMMessage


@dataclass
class CodegenResult:
    code_text: str
    notes: Optional[str] = None


class CodegenAgent:
    def __init__(self, llm: Optional[LLMClient]) -> None:
        self.llm = llm

    def _build_messages(self, context: Dict[str, Any], user_factor_spec: str, coding_prefs: Optional[Dict[str, Any]]) -> List[LLMMessage]:
        system = (
            "You are a quantitative research coding assistant. Generate ONLY Python code for a function: \n"
            "def compute_factor(data: dict[str, pd.DataFrame], params: dict) -> pd.DataFrame\n"
            "Constraints: use ONLY pandas/numpy. No IO, no network, no subprocess, no dynamic import, no reflection. \n"
            "Return a DataFrame that preserves the given output index and includes a 'factor' column."
        )
        user = (
            "CONTEXT (JSON):\n" + str(context) + "\n\n"
            "USER_FACTOR_SPEC:\n" + user_factor_spec + "\n\n"
            "REQUIREMENTS:\n- Use only fields provided by the selection.\n- Do not include any explanation, comments, or markdown. Return ONLY Python code."
        )
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
        model = (coding_prefs or {}).get("model") or "gpt-4o-mini"
        temperature = float((coding_prefs or {}).get("temperature", 0.0))
        max_tokens = int((coding_prefs or {}).get("max_tokens", 1200))
        code = self.llm.complete(messages, model=model, temperature=temperature, max_tokens=max_tokens)
        return CodegenResult(code_text=code)
