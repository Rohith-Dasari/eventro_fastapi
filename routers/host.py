from fastapi import APIRouter, Depends, HTTPException
from services.venue_service import VenuService
from dependencies import get_venue_service, require_roles, get_current_user
from schemas.response import APIResponse

hosts_router = APIRouter(prefix="/hosts", tags=["host"])


@hosts_router.get("/{host_id}/venues")
async def get_host_venues(
    host_id: str,
    venue_service: VenuService = Depends(get_venue_service),
    user=Depends(get_current_user),
):
    if user["role"] != "admin":
        if user["user_id"] != host_id:
            raise HTTPException(
                status_code=401, detail=f"not authorised to see host: {host_id} venues"
            )
    venues = venue_service.get_host_venues(host_id=host_id)
    return APIResponse(
        status_code=200,
        message=f"successfully retrieved {host_id}'s venues",
        data=venues,
    )
