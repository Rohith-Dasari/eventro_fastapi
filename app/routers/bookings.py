from app.dependencies import (
    get_booking_service,
    get_current_user,
    require_roles,
    get_user_service,
)
from fastapi import APIRouter, Depends
from app.schemas.booking import BookingReq
from app.schemas.response import APIResponse
from app.services.booking_service import BookingService
from app.models.users import Role
from app.services.user_service import UserService

bookings_router = APIRouter(prefix="/bookings", tags=["bookings"])


@bookings_router.post("", status_code=201)
def create_bookings(
    req: BookingReq,
    current_user=Depends(get_current_user),
    booking_service: BookingService = Depends(get_booking_service),
    user_service: UserService = Depends(get_user_service),
):
    if current_user["role"] == Role.ADMIN.value:
        user = user_service.get_user_by_mail(mail=req.user_id)
        user_id = user.user_id
    else:
        user_id = current_user["user_id"]
    booking = booking_service.create_booking(req, user_id)
    return APIResponse(
        status_code=201, message="succesfully made booking", data=booking
    )
