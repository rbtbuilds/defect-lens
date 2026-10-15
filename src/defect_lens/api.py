import sqlite3
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from defect_lens.config import Settings
from defect_lens.contracts import ReadyState


def create_app(settings: Settings) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
        settings.runtime.mkdir(parents=True, exist_ok=True)
        yield

    app = FastAPI(title="Defect Lens", lifespan=lifespan)

    @app.get("/healthz")
    def health() -> dict[str, str]:
        with sqlite3.connect(settings.database_path) as connection:
            connection.execute("SELECT 1").fetchone()
        return {"status": "ok", "database": "ok"}

    @app.get("/readyz")
    def readiness() -> JSONResponse:
        return JSONResponse(ReadyState().model_dump(), status_code=503)

    return app
