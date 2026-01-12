from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from routers.auth import auth_router
from routers.events import event_router
from routers.artists import artist_router
from routers.venues import venue_router
from routers.hosts import hosts_router
from routers.shows import shows_router
from routers.users import users_router
from routers.bookings import bookings_router

from custom_exceptions.user_exceptions import (
    UserAlreadyExists,
    IncorrectCredentials,
)
from custom_exceptions.generic import NotFoundException
from botocore.exceptions import ClientError

from boto3 import resource

from repository.user_repository import UserRepository
from repository.event_repository import EventRepository
from repository.artist_repository import ArtistRepository
from repository.venue_repository import VenueRepository
from repository.show_repository import ShowRepository
from repository.booking_repository import BookingRepository

from services.event_service import EventService
from services.artist_service import ArtistService
from services.user_service import UserService
from services.venue_service import VenuService
from services.show_service import ShowService
from services.booking_service import BookingService

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    dynamodb = resource("dynamodb", region_name="ap-south-1")
    table = dynamodb.Table("eventro_table")

    app.state.user_repo = UserRepository(table=table)
    app.state.event_repo = EventRepository(table=table)
    app.state.artist_repo = ArtistRepository(table=table)
    app.state.venue_repo = VenueRepository(table=table)
    app.state.show_repo = ShowRepository(table=table)
    app.state.booking_repo = BookingRepository(table=table)

    app.state.user_service = UserService(app.state.user_repo)
    app.state.artist_service = ArtistService(app.state.artist_repo)
    app.state.venue_service = VenuService(app.state.venue_repo)
    app.state.show_service = ShowService(
        show_repo=app.state.show_repo,
        event_repo=app.state.event_repo,
        venue_repo=app.state.venue_repo,
    )
    app.state.event_service = EventService(
        event_repo=app.state.event_repo,
        artist_service=app.state.artist_service,
    )
    app.state.booking_service = BookingService(
        booking_repo=app.state.booking_repo,
        show_repo=app.state.show_repo,
        event_repo=app.state.event_repo,
        venue_repo=app.state.venue_repo,
    )

    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router=auth_router)
app.include_router(router=event_router)
app.include_router(router=artist_router)
app.include_router(router=venue_router)
app.include_router(router=hosts_router)
app.include_router(router=shows_router)
app.include_router(router=users_router)
app.include_router(router=bookings_router)


@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status_code": exc.status_code,
            "message": exc.detail,
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


@app.exception_handler(NotFoundException)
async def not_found_handler(request: Request, exc: NotFoundException):
    return JSONResponse(
        status_code=404,
        content={
            "status_code": exc.status_code,
            "message": f"{exc.resource} {exc.identifier} not found",
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



@app.exception_handler(UserAlreadyExists)
def user_already_exists_handler(request: Request, exc: UserAlreadyExists):
    return JSONResponse(
        status_code=400,
        content={
            "status_code": 400,
            "message": str(exc),
        },
    )


@app.exception_handler(IncorrectCredentials)
def incorrect_credentials_handler(request: Request, exc: IncorrectCredentials):
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
