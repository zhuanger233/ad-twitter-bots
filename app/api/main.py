from __future__ import annotations

from fastapi import FastAPI

from app.api.routes.admin import router as admin_router
from app.api.routes.health import router as health_router
from app.api.routes.tasks import router as tasks_router
from app.api.routes.webhook import router as webhook_router
from app.core.logging import configure_logging

configure_logging()

app = FastAPI(title="Twitter Subtitle Bot")
app.include_router(health_router)
app.include_router(tasks_router)
app.include_router(admin_router)
app.include_router(webhook_router)
