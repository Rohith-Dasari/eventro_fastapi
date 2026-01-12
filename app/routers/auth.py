from fastapi import APIRouter, Depends, status
from schemas.auth import SignupRequest, LoginRequest
from schemas.response import APIResponse
from services.user_service import UserService
from typing import Annotated
from dependencies import get_user_service

auth_router = APIRouter(tags=["auth"])
UserServiceDep = Annotated[UserService, Depends(get_user_service)]


@auth_router.post(
    "/signup",
    status_code=status.HTTP_201_CREATED,
    response_model=APIResponse,
)
def signup(
    payload: SignupRequest,
    service: UserServiceDep,
):

    token = service.signup(
        email=payload.email,
        username=payload.username,
        password=payload.password,
        phone=payload.phone_number,
    )
    return APIResponse(status_code=201, message="signup successful", data=token)


@auth_router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=APIResponse,
)
def login(
    payload: LoginRequest,
    service: UserServiceDep,
):
    token = service.login(
        email=payload.email,
        password=payload.password,
    )
    return APIResponse(status_code=200, message="login successful", data=token)
