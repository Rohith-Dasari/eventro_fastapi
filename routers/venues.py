from fastapi import APIRouter, Depends, status
from typing import Annotated
from services.venue_service import VenuService
from schemas.venues import VenueCreateReq, VenueUpdateReq
from dependencies import get_venue_service, require_roles, get_current_user
from schemas.response import APIResponse


venue_router = APIRouter(
    prefix="/venues", tags=["venue"], dependencies=[Depends(get_current_user)]
)
VenueServiceDep = Annotated[VenuService, Depends(get_venue_service)]


@venue_router.post("", status_code=status.HTTP_201_CREATED)
async def add_venue(
    req: VenueCreateReq,
    current_user: dict = Depends(require_roles(["admin", "host"])),
    venue_service: VenuService = Depends(get_venue_service),
):
    host_id = current_user["user_id"]
    venue = venue_service.add_venue(req, host_id)
    return APIResponse(
        status_code=status.HTTP_201_CREATED,
        message="added venue successfully",
        data=venue,
    )


@venue_router.get("/{venue_id}", status_code=status.HTTP_200_OK)
async def get_venue_by_id(
    venue_id: str,
    venue_service: VenuService = Depends(get_venue_service),
):
    venue = venue_service.get_venue_by_id(venue_id=venue_id)
    return APIResponse(status_code=200, message="successfully retrieved", data=venue)


@venue_router.patch("/{venue_id}")
async def update_venue(
    req: VenueUpdateReq,
    venue_id: str,
    venue_service: VenuService = Depends(get_venue_service),
    user=Depends(get_current_user),
):
    host_id = user["user_id"]
    venue_service.update_venue(venue_id, host_id, req.is_blocked)
    return APIResponse(
        status_code=200,
        message=f"successfully updated {venue_id}",
    ).model_dump(exclude_none=True)


@venue_router.delete("/{venue_id}")
async def delete_venue(
    venue_id: str,
    venue_service: VenuService = Depends(get_venue_service),
    user=Depends(get_current_user),
):
    host_id = user["user_id"]
    venue_service.delete_venue(venue_id=venue_id, host_id=host_id)
    return APIResponse(
        status_code=200,
        message=f"successfully deleted {venue_id}",
    )
