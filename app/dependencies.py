from typing import List
from fastapi import Depends, HTTPException, status,Request
from fastapi.security import OAuth2PasswordBearer
from utils.jwt_service import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_user_service(request: Request):
    return request.app.state.user_service

def get_artist_service(request: Request):
    return request.app.state.artist_service

def get_event_service(request: Request):
    return request.app.state.event_service

def get_show_service(request: Request):
    return request.app.state.show_service

def get_venue_service(request: Request):
    return request.app.state.venue_service

def get_booking_service(request: Request):
    return request.app.state.booking_service

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
