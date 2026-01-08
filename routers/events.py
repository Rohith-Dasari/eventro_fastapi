from fastapi import APIRouter, Depends, status, Query
from schemas.event import CreateEventRequest
from schemas.response import APIResponse
from services.event_service import EventService
from dependencies import require_roles, get_event_service, get_current_user

event_router = APIRouter(
    prefix="/events", tags=["events"], dependencies=[Depends(get_current_user)]
)


@event_router.post("", status_code=status.HTTP_201_CREATED)
async def create_event(
    req: CreateEventRequest,
    current_user: dict = Depends(require_roles(["admin", "host"])),
    event_service: EventService = Depends(get_event_service),
):
    event = event_service.create_event(
        event_name=req.name,
        description=req.description,
        duration=req.duration,
        category=req.category,
        artist_ids=req.artist_ids,
    )
    return APIResponse(
        status_code=status.HTTP_201_CREATED,
        message="event successfully created",
        data=event,
    )


@event_router.get("/{event_id}")
async def get_event_by_id(
    event_id: str,
    event_service: EventService = Depends(get_event_service),
):
    event = event_service.get_event_by_id(event_id)
    return APIResponse(status_code=200, message="successfully retrieved", data=event)


@event_router.get("")
async def get_event_by_name(
    name: str = Query(..., min_length=1, description="Event name to search"),
    event_service: EventService = Depends(get_event_service),
):
    events = event_service.get_event_by_name(name)
    return APIResponse(status_code=200, message="successfully retrieved", data=events)

#name,city- put eventname in sk prefix, adding in show repo, get in event repo