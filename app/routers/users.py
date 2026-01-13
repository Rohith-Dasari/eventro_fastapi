from app.dependencies import get_user_service, get_current_user, require_roles
from fastapi import APIRouter, Depends
from app.schemas.response import APIResponse
from app.services.user_service import UserService
from app.services.booking_service import BookingService
from app.dependencies import get_booking_service


users_router = APIRouter(prefix="/users", tags=["users"])


@users_router.get("/{user_id}")
def get_user_profile(
    user=Depends(get_current_user),
    userService: UserService = Depends(get_user_service),
):
    user = userService.get_user_profile(user["user_id"])
    return APIResponse(
        status_code=200, message="succesfully retrieved user profile", data=user
    )


@users_router.get("/{user_id}/bookings")
def get_bookings(
    user=Depends(get_current_user),
    booking_service: BookingService = Depends(get_booking_service),
):
    bookings = booking_service.get_user_bookings(user["user_id"])
    return APIResponse(
        status_code=200, message="succesfully retrieved user bookings", data=bookings
    )


@users_router.get("/email/{mail_id}")
def get_user_by_mail(
    mail_id: str,
    user=Depends(require_roles(["admin"])),
    userService: UserService = Depends(get_user_service),
):
    user = userService.get_user_by_mail(mail_id)
    return APIResponse(status_code=200, message="succesfully user by mail", data=user)
