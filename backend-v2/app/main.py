from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .routers import health, catalog, selections, factors
from .storage.db import init_db
from .core.config import load_settings
from .core.logging import setup_logging
from .core.errors import install_error_handlers


def create_app() -> FastAPI:
    settings = load_settings()
    logger = setup_logging(settings.log_level)
    app = FastAPI(title="backend-v2", version="0.1.0")

    # DB
    init_db()

    # Errors
    install_error_handlers(app)

    # Routers
    app.include_router(health.router)
    app.include_router(catalog.router, prefix="/catalog", tags=["catalog"])
    app.include_router(selections.router)
    app.include_router(factors.router)

    return app


app = create_app()
