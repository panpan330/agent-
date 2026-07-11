from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import MockServiceException
from app.schemas.error import ErrorResponse


def build_error_response(
    status_code: int,
    code: str,
    message: str,
    details: Any | None = None,
) -> JSONResponse:
    body = ErrorResponse(
        code=code,
        message=message,
        details=details,
    ).model_dump(exclude_none=True)
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(body),
    )


def get_http_error_code(status_code: int) -> str:
    if status_code == 404:
        return "NOT_FOUND"
    if status_code == 405:
        return "METHOD_NOT_ALLOWED"
    return "HTTP_ERROR"


def get_http_error_message(exc: StarletteHTTPException) -> str:
    if exc.status_code == 404:
        return "资源不存在。"
    if exc.status_code == 405:
        return "请求方法不允许。"
    if isinstance(exc.detail, str):
        return exc.detail
    return "请求处理失败。"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(MockServiceException)
    async def mock_service_exception_handler(
        request: Request,
        exc: MockServiceException,
    ) -> JSONResponse:
        return build_error_response(
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            details=exc.details,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        return build_error_response(
            status_code=exc.status_code,
            code=get_http_error_code(exc.status_code),
            message=get_http_error_message(exc),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return build_error_response(
            status_code=422,
            code="VALIDATION_ERROR",
            message="请求参数校验失败。",
            details=jsonable_encoder(exc.errors()),
        )
