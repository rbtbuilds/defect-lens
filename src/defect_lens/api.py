import logging
import sqlite3
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException
from starlette.middleware.base import RequestResponseEndpoint
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response

from defect_lens.config import Settings
from defect_lens.errors import DomainError
from defect_lens.repository import Repository
from defect_lens.routes import BodyLimit, build_router, error_response
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

    app.add_middleware(BodyLimit, settings=settings)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5111"],
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Idempotency-Key"],
    )
    app.include_router(build_router(settings, repository, supervisor))

    @app.middleware("http")
    async def request_context(request: Request, call_next: RequestResponseEndpoint) -> Response:
        request.state.request_id = str(uuid4())
        if request.method == "POST" and request.headers.get("origin") not in {
            None,
            "http://127.0.0.1:5111",
        }:
            return error_response(
                "INVALID_REQUEST", "Origin is not allowed", 403, request.state.request_id
            )
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    @app.exception_handler(DomainError)
    async def domain_error(request: Request, error: DomainError) -> JSONResponse:
        return error_response(
            error.code, error.message, error.status, request.state.request_id, error.retryable
        )

    @app.exception_handler(RequestValidationError)
    @app.exception_handler(ValidationError)
    async def invalid(request: Request, _error: Exception) -> JSONResponse:
        return error_response(
            "INVALID_REQUEST",
            "Invalid fields; check the documented format and limits",
            422,
            request.state.request_id,
        )

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, error: HTTPException) -> JSONResponse:
        return error_response(
            "NOT_FOUND" if error.status_code == 404 else "INVALID_REQUEST",
            "Request could not be handled",
            error.status_code,
            request.state.request_id,
        )

    @app.exception_handler(Exception)
    async def internal_error(request: Request, error: Exception) -> JSONResponse:
        logging.getLogger(__name__).error(
            "Request %s failed", request.state.request_id, exc_info=error
        )
        return error_response(
            "INTERNAL",
            "Unexpected failure; consult local logs with the request ID",
            500,
            request.state.request_id,
        )

    app.state.repository = repository
    app.state.supervisor = supervisor

    @app.get("/healthz")
    def health() -> dict[str, str]:
        try:
            with sqlite3.connect(settings.database_path) as connection:
                connection.execute("SELECT 1").fetchone()
        except sqlite3.Error as error:
            raise DomainError(
                "DATABASE_UNAVAILABLE", "Database health probe failed", 503, True
            ) from error
        return {"status": "ok", "database": "ok"}

    @app.get("/readyz")
    def readiness() -> JSONResponse:
        return JSONResponse(
            supervisor.ready.model_dump(),
            status_code=200 if supervisor.ready.status == "ready" else 503,
        )

    return app
