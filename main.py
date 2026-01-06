from fastapi import FastAPI, Request, HTTPException
from routers.auth import auth_router
from routers.events import event_router
from routers.artists import artist_router
from routers.venues import venue_router
from routers.host import hosts_router

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from custom_exceptions.user_exceptions import (
    UserNotFoundError,
    UserAlreadyExists,
    IncorrectCredentials,
)
from custom_exceptions.artist_exceptions import InvalidArtistID
from custom_exceptions.event_exceptions import EventNotFound
from botocore.exceptions import ClientError

app = FastAPI()

app.include_router(router=auth_router)
app.include_router(router=event_router)
app.include_router(router=artist_router)
app.include_router(router=venue_router)
app.include_router(router=hosts_router)


@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status_code": exc.status_code,
            "message": exc.detail,
        },
    )


@app.exception_handler(EventNotFound)
def http_exception_handler(request: Request, exc: EventNotFound):
    return JSONResponse(
        status_code=404,
        content={
            "status_code": exc.status_code,
            "message": str(exc),
        },
    )


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "status_code": 422,
            "message": str(exc),
        },
    )


@app.exception_handler(ValueError)
def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=422,
        content={
            "status_code": 422,
            "message": str(exc),
        },
    )


@app.exception_handler(InvalidArtistID)
def value_error_handler(request: Request, exc: InvalidArtistID):
    return JSONResponse(
        status_code=422,
        content={
            "status_code": 422,
            "message": str(exc),
        },
    )


@app.exception_handler(UserNotFoundError)
def user_not_found_handler(request: Request, exc: UserNotFoundError):
    return JSONResponse(
        status_code=404,
        content={
            "status_code": 404,
            "message": str(exc),
        },
    )


@app.exception_handler(UserAlreadyExists)
def user_not_found_handler(request: Request, exc: UserAlreadyExists):
    return JSONResponse(
        status_code=400,
        content={
            "status_code": 400,
            "message": str(exc),
        },
    )


@app.exception_handler(IncorrectCredentials)
def user_not_found_handler(request: Request, exc: IncorrectCredentials):
    return JSONResponse(
        status_code=401,
        content={
            "status_code": 401,
            "message": str(exc),
        },
    )


@app.exception_handler(ClientError)
def client_error_handler(request: Request, exc: ClientError):
    return JSONResponse(
        status_code=500,
        content={
            "status_code": 500,
            "message": str(exc),
        },
    )


@app.exception_handler(Exception)
def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "status_code": 500,
            "message": str(exc),
        },
    )
