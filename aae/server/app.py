"""FastAPI app (§17 & §13.4)."""
from __future__ import annotations

from fastapi import FastAPI

from aae.server.routes import health, webhooks


def create_app() -> FastAPI:
    app = FastAPI(title="AAE V3.0 Mother Agent", version="3.0.0")
    app.include_router(health.router)
    app.include_router(webhooks.router)
    return app


app = create_app()
