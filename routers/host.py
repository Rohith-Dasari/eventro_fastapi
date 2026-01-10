from fastapi import APIRouter, Depends, HTTPException
from services.venue_service import VenuService
from services.event_service import EventService
from dependencies import (
    get_venue_service,
    require_roles,
    get_event_service,
)
from schemas.response import APIResponse


hosts_router = APIRouter(prefix="/hosts", tags=["host"])


@hosts_router.get("/{host_id}/venues")
async def get_host_venues(
    host_id: str,
    venue_service: VenuService = Depends(get_venue_service),
    user=Depends(require_roles(["host", "admin"])),
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


@hosts_router.get("/{host_id}/events")
async def get_host_shows(
    host_id: str,
    event_service: EventService = Depends(get_event_service),
    user=Depends(require_roles(["host", "admin"])),
):
    if user["role"] != "admin":
        if user["user_id"] != host_id:
            raise HTTPException(
                status_code=401, detail=f"not authorised to see host: {host_id} events"
            )
    events = event_service.get_host_events(host_id=host_id)
    return APIResponse(
        status_code=200,
        message=f"successfully retrieved {host_id}'s events",
        data=events,
    )
