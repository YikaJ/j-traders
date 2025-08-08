from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "message": str(exc),
                "path": str(request.url),
            },
        )
