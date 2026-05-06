from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    status_code: int = 500
    code: str = "INTERNAL_ERROR"

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class UpstreamError(AppError):
    status_code = 502
    code = "UPSTREAM_ERROR"


class ProductNotFoundError(AppError):
    status_code = 404
    code = "PRODUCT_NOT_FOUND"


class NoStationsFoundError(AppError):
    status_code = 404
    code = "NO_STATIONS_FOUND"


def _error_body(code: str, message: str) -> dict:
    return {"success": False, "error": {"code": code, "message": message}}


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(exc.code, exc.message),
    )


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=_error_body("INTERNAL_ERROR", "Unexpected server error"),
    )
