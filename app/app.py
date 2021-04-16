from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError, StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from app.models import database
from app.settings import ORIGINS
from app.views import router

# TODO index.html


def create_app() -> FastAPI:
    app = FastAPI(
        on_startup=[database.connect],
        on_shutdown=[database.disconnect],
        exception_handlers={
            StarletteHTTPException: http_exception_handler,
            RequestValidationError: request_validation_exception_handler,
        },
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)

    @app.get("/ping")
    def ping():
        return {"text": "pong"}

    return app
