from asyncpg.exceptions import UniqueViolationError
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_409_CONFLICT, HTTP_422_UNPROCESSABLE_ENTITY

from app.schemas import BaseResponse


async def unique_violation_error_handler(
    request: Request, exc: UniqueViolationError
) -> JSONResponse:
    return JSONResponse(
        BaseResponse(success=False, errors=[exc.detail], result=None).dict(),
        status_code=HTTP_409_CONFLICT,
    )


async def http_exception_handler(
    request: Request, exc: HTTPException
) -> JSONResponse:
    return JSONResponse(
        BaseResponse(success=False, errors=[exc.detail], result=None).dict(),
        status_code=exc.status_code,
        headers=getattr(exc, "headers", None),
    )


async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        BaseResponse(success=False, errors=exc.errors(), result=None).dict(),
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
    )
