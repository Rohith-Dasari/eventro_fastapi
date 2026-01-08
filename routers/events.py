from fastapi import APIRouter, Depends, status, Query
from schemas.event import CreateEventRequest, UpdateEventRequest
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
async def browse_events(
    name: str = Query(description="Event name to search"),
    city: str = Query(description="Event name to search"),
    user=Depends(get_current_user),
    event_service: EventService = Depends(get_event_service),
):
    if user["role"] == "admin" or user["role"] == "host":
        events = event_service.browse_events(event_name=name)
    else:
        events = event_service.browse_events(event_name=name, city=city)
    return APIResponse(status_code=200, message="successfully retrieved", data=events)


@event_router.patch("/{event_id}")
async def update_event(
    event_id: str,
    req: UpdateEventRequest,
    event_service: EventService = Depends(get_event_service),
    user=Depends(require_roles(["Admin"])),
):
    event_service.update_event(event_id, req)
    return APIResponse(status_code=200, message=f"successfully updated {event_id}")
