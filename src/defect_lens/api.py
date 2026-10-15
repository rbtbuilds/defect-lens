import sqlite3
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from defect_lens.config import Settings
from defect_lens.repository import Repository
from defect_lens.supervisor import Supervisor


def create_app(settings: Settings) -> FastAPI:
    repository = Repository(settings)
    supervisor = Supervisor(settings, repository)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
        settings.runtime.mkdir(parents=True, exist_ok=True)
        supervisor.start()
        try:
            yield
        finally:
            supervisor.shutdown()

    app = FastAPI(title="Defect Lens", lifespan=lifespan)

    app.state.repository = repository
    app.state.supervisor = supervisor

    @app.get("/healthz")
    def health() -> dict[str, str]:
        with sqlite3.connect(settings.database_path) as connection:
            connection.execute("SELECT 1").fetchone()
        return {"status": "ok", "database": "ok"}

    @app.get("/readyz")
    def readiness() -> JSONResponse:
        return JSONResponse(
            supervisor.ready.model_dump(),
            status_code=200 if supervisor.ready.status == "ready" else 503,
        )

    return app
