from __future__ import annotations

import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


def _mask_secrets(text: str) -> str:
    secrets = []
    for key in ("TUSHARE_TOKEN", "AI_API_KEY"):
        val = os.getenv(key)
        if val:
            secrets.append(val)
    masked = text
    for s in secrets:
        if s and s in masked:
            masked = masked.replace(s, "***")
    return masked


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "message": _mask_secrets(str(exc)),
                "path": str(request.url),
            },
        )
