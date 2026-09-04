from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.exceptions import NotFoundException, ValidationException


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundException)
    async def handle_not_found(
        _request: Request,
        exception: NotFoundException,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exception)},
        )

    @app.exception_handler(ValidationException)
    async def handle_validation_error(
        _request: Request,
        exception: ValidationException,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": str(exception)},
        )
