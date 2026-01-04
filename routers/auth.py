from fastapi import APIRouter, Depends, HTTPException, status
from schemas.auth import UserResponse, SignupRequest, LoginRequest
from services.user_service import UserService
from dependencies import get_user_service
from custom_exceptions.user_exceptions import (
    UserNotFoundError,
    IncorrectCredentials,
)

router = APIRouter(prefix="/", tags=["auth"])


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def signup(
    payload: SignupRequest,
    service: UserService = Depends(get_user_service),
):
    try:
        user = service.signup(
            email=payload.email,
            username=payload.username,
            password=payload.password,
            phone=payload.phone,
        )
        return UserResponse.from_domain(user)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/login", response_model=UserResponse)
def login(
    payload: LoginRequest,
    service: UserService = Depends(get_user_service),
):
    try:
        user = service.login(
            email=payload.email,
            password=payload.password,
        )
        return UserResponse.from_domain(user)

    except (UserNotFoundError, IncorrectCredentials):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
