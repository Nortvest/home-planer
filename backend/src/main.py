"""FastAPI-приложение: точка входа."""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.domain.exceptions import DomainError
from src.infrastructure.db.migrations import init_if_needed
from src.infrastructure.settings import get_settings
from src.presentation.api import (
    calendar,
    dashboard,
    instances,
    templates,
    users,
)
from src.presentation.static import maybe_mount_static

app = FastAPI(title="Home Planner API")


@app.exception_handler(DomainError)
async def domain_error_handler(_request: Request, exc: DomainError) -> JSONResponse:
    error_code = "internal_error"
    status_code = 500
    name = type(exc).__name__
    if name in {"UserNotFoundError", "TemplateNotFoundError", "InstanceNotFoundError"}:
        status_code, error_code = 404, "not_found"
    elif name in {"InstanceAlreadyCompletedError", "DuplicateUserNameError"}:
        status_code, error_code = 409, "conflict"
    elif name == "UserHasActiveTasksError":
        status_code, error_code = 409, "has_active_tasks"
    elif name == "InvalidColorError":
        status_code, error_code = 400, "validation_error"

    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": error_code, "message": str(exc)}},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "validation_error", "message": str(exc)}},
    )


@app.on_event("startup")
def startup() -> None:
    settings = get_settings()
    init_if_needed(settings.db_path_resolved)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(users.router)
app.include_router(templates.router)
app.include_router(calendar.router)
app.include_router(instances.router)
app.include_router(dashboard.router)

settings = get_settings()
if settings.SERVE_FRONTEND:
    maybe_mount_static(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
