from dependencies import get_booking_service, get_current_user, require_roles
from fastapi import APIRouter, Depends
from schemas.booking import BookingReq, BookingResponse
from schemas.response import APIResponse
from services.booking_service import BookingService

bookings_router = APIRouter(prefix="/bookings", tags=["bookings"])


@bookings_router.post("")
def create_bookings(
    req: BookingReq,
    user=Depends(get_current_user),
    booking_service: BookingService = Depends(get_booking_service),
):
    booking = booking_service.create_booking(req, user["user_id"])
    return APIResponse(
        status_code=201, message="succesfully made booking", data=booking
    )


@bookings_router.get("/{user_id}")
def get_bookings(
    user=Depends(get_current_user),
    booking_service: BookingService = Depends(get_booking_service),
):
    bookings = booking_service.get_user_bookings(user["user_id"])
    return APIResponse(
        status_code=201, message="succesfully retrieved user bookings", data=bookings
    )
