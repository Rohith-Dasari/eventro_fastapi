from app.dependencies import get_user_service, get_current_user, require_roles
from fastapi import APIRouter, Depends, status, HTTPException
from app.schemas.response import APIResponse
from app.services.user_service import UserService
from app.services.booking_service import BookingService
from app.dependencies import get_booking_service


users_router = APIRouter(prefix="/users", tags=["users"])


@users_router.get("/{user_id}", status_code=200)
def get_user_profile(
    user_id: str,
    user=Depends(get_current_user),
    userService: UserService = Depends(get_user_service),
):
    if user["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to access this user profile",
        )
    profile = userService.get_user_profile(user_id)
    return APIResponse(
        status_code=200, message="succesfully retrieved user profile", data=profile
    )


@users_router.get("/{user_id}/bookings", status_code=200)
def get_bookings(
    user_id: str,
    user=Depends(get_current_user),
    booking_service: BookingService = Depends(get_booking_service),
):
    if user["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to access this user bookings",
        )
    bookings = booking_service.get_user_bookings(user_id)
    return APIResponse(
        status_code=200, message="succesfully retrieved user bookings", data=bookings
    )


@users_router.get("/email/{mail_id}", status_code=200)
def get_user_by_mail(
    mail_id: str,
    user=Depends(require_roles(["admin"])),
    userService: UserService = Depends(get_user_service),
):
    user = userService.get_user_by_mail(mail_id)
    return APIResponse(status_code=200, message="succesfully user by mail", data=user)
