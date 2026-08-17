from contextlib import asynccontextmanager
from typing import AsyncIterator

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.core.exceptions import CodeVoyagerError
from app.core.logger import logger
from app.routers import projects_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    settings.workspace.mkdir(parents=True, exist_ok=True)
    logger.info("CodeVoyager API started in %s mode", settings.environment)
    yield
    logger.info("CodeVoyager API stopped")


app = FastAPI(
    title="CodeVoyager API",
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(projects_router)


@app.exception_handler(CodeVoyagerError)
async def handle_codevoyager_error(
    _: Request, exc: CodeVoyagerError
) -> JSONResponse:
    logger.warning("Application error [%s]: %s", exc.code, exc.message)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "codevoyager-backend"}


def run() -> None:
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        reload=settings.environment == "development",
    )
