from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv, dotenv_values
except Exception:  # pragma: no cover
    load_dotenv = None  # type: ignore
    dotenv_values = None  # type: ignore


@dataclass(frozen=True)
class Settings:
    tushare_token: str | None
    cache_ttl_hours: int
    max_qps: int
    log_level: str
    api_host: str
    api_port: int
    # AI settings (OpenAI-compatible)
    ai_endpoint: str | None = None
    ai_api_key: str | None = None
    ai_model: str | None = None


def load_settings() -> Settings:
    # Prefer explicit .env files; backend-v2/.env has highest priority, then project .env, then OS env
    token_from_env_files: str | None = None
    here = Path(__file__).resolve()
    backend_v2_root = here.parents[2]
    project_root = here.parents[3] if len(here.parents) >= 4 else backend_v2_root
    if dotenv_values is not None:
        for env_path in (backend_v2_root / ".env", project_root / ".env"):
            if env_path.exists():
                values = dotenv_values(dotenv_path=env_path)
                tok = values.get("TUSHARE_TOKEN")
                if tok:
                    token_from_env_files = tok.strip()
                    break
    # Also load into process env so downstream libs can read
    if load_dotenv is not None:
        for env_path in (project_root / ".env", backend_v2_root / ".env"):
            if env_path.exists():
                load_dotenv(dotenv_path=env_path, override=True)

    def _get_int(key: str, default: int) -> int:
        try:
            return int(os.getenv(key, str(default)))
        except Exception:
            return default

    # AI configuration with DashScope OpenAI-compatible defaults
    ai_api_key = os.getenv("AI_API_KEY") or os.getenv("DASHSCOPE_API_KEY")
    ai_endpoint = os.getenv("AI_ENDPOINT")
    if not ai_endpoint and os.getenv("DASHSCOPE_API_KEY"):
        # Default to DashScope OpenAI-compatible endpoint when key is present
        ai_endpoint = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    ai_model = os.getenv("AI_MODEL")
    if not ai_model and os.getenv("DASHSCOPE_API_KEY"):
        # Provide a sensible default model for DashScope if none supplied
        ai_model = "qwen3-coder-plus"

    return Settings(
        tushare_token=token_from_env_files or os.getenv("TUSHARE_TOKEN"),
        cache_ttl_hours=_get_int("CACHE_TTL_HOURS", 24),
        max_qps=_get_int("MAX_QPS", 8),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        api_host=os.getenv("API_HOST", "127.0.0.1"),
        api_port=_get_int("API_PORT", 8000),
        ai_endpoint=ai_endpoint,
        ai_api_key=ai_api_key,
        ai_model=ai_model,
    )
