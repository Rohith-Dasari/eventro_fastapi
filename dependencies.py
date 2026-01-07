from typing import List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from boto3 import resource
from functools import lru_cache
from utils.jwt_service import decode_access_token
from types_boto3_dynamodb.service_resource import Table

from repository.user_repository import UserRepository
from repository.event_repository import EventRepository
from repository.artist_repository import ArtistRepository
from repository.venue_repository import VenueRepository
from repository.show_repository import ShowRepository

from services.event_service import EventService
from services.artist_service import ArtistService
from services.user_service import UserService
from services.venue_service import VenuService
from services.show_service import ShowService


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


@lru_cache
def get_dynamodb_table() -> Table:
    dynamodb = resource("dynamodb")
    return dynamodb.Table("eventro_table")


def get_shows_repo(table: Table = Depends(get_dynamodb_table)) -> ShowService:
    return ShowRepository(table=table)


def get_user_repo(table: Table = Depends(get_dynamodb_table)) -> UserRepository:
    return UserRepository(table=table)


def get_artist_repo(table: Table = Depends(get_dynamodb_table)) -> ArtistRepository:
    return ArtistRepository(table=table)


def get_event_repo(
    table: Table = Depends(get_dynamodb_table),
) -> EventRepository:
    return EventRepository(table=table)


def get_venue_repo(
    table: Table = Depends(get_dynamodb_table),
) -> VenueRepository:
    return VenueRepository(table=table)


def get_shows_service(
    show_repo: ShowRepository = Depends(get_shows_repo),
) -> ShowService:
    return ShowService(show_repo)


def get_venue_service(
    venue_repo: VenueRepository = Depends(get_venue_repo),
) -> VenuService:
    return VenuService(venue_repo)


def get_user_service(
    user_repo: UserRepository = Depends(get_user_repo),
) -> UserService:
    return UserService(user_repo)


def get_artist_service(
    artist_repo: ArtistRepository = Depends(get_artist_repo),
) -> ArtistService:
    return ArtistService(artist_repo)


def get_event_service(
    event_repo: EventRepository = Depends(get_event_repo),
    artist_service: ArtistService = Depends(get_artist_service),
) -> EventService:
    return EventService(event_repo, artist_service)


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = decode_access_token(token)
        return payload
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )


def require_roles(allowed_roles: List[str]):
    def role_checker(
        current_user: dict = Depends(get_current_user),
    ):
        if current_user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="unauthorised"
            )
        return current_user

    return role_checker
