from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .routers import health, catalog, selections, factors
from .routers import standardize
from .routers import persist
from .routers import universe
from .storage.db import init_db
from .core.config import load_settings
from .core.logging import setup_logging
from .core.errors import install_error_handlers


def create_app() -> FastAPI:
    settings = load_settings()
    logger = setup_logging(settings.log_level)
    app = FastAPI(title="backend-v2", version="0.1.0")

    # CORS
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # DB
    init_db()

    # Errors
    install_error_handlers(app)

    # Routers
    app.include_router(health.router)
    app.include_router(catalog.router, prefix="/catalog", tags=["catalog"])
    app.include_router(selections.router)
    app.include_router(factors.router)
    app.include_router(standardize.router)
    app.include_router(persist.router)
    app.include_router(universe.router)

    return app


app = create_app()
