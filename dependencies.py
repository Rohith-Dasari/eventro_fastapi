from services.user_service import UserService
from repository.user_repository import UserRepository
from repository.event_repository import EventRepository
from typing import List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from services.user_service import decode_access_token
from services.event_service import EventService
from services.artist_service import ArtistService
from repository.artist_repository import ArtistRepository
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_user_repo() -> UserRepository:
    return UserRepository()
def get_artist_repo() -> ArtistRepository:
    return ArtistRepository()
def get_event_repo() -> EventRepository:
    return EventRepository()
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
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

def require_roles(allowed_roles: List[str]):
    def role_checker(
        current_user: dict = Depends(get_current_user),
    ):
        if current_user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted"
            )
        return current_user
    return role_checker
