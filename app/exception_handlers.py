import json
from decimal import Decimal

from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import Response
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from app.schemas import BaseResponse


def encode_decimal(value):
    if isinstance(value, Decimal):
        return str(value)
    return value


class JSONResponse(Response):
    media_type = "application/json"

    def render(self, content) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
            default=encode_decimal,
        ).encode("utf-8")


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
