from fastapi import APIRouter, Depends, status
from dependencies import get_current_user, get_shows_service,require_roles
from services.show_service import ShowService
from typing import Annotated
from schemas.shows import ShowCreateReq,ShowUpdateReq
from schemas.response import APIResponse
shows_router = APIRouter(
    prefix="/shows", tags=["shows"], dependencies=[Depends(get_current_user)]
)

ShowServiceDep = Annotated[ShowService, Depends(get_shows_service)]

@shows_router.post("",status_code=status.HTTP_201_CREATED)
async def create_show(
    req:ShowCreateReq,
    current_user:dict=Depends(require_roles(["host"])),
    show_service:ShowService=Depends(get_shows_service)
):
    show_service.create_show(show_dto=req)
    return APIResponse(status_code=status.HTTP_201_CREATED,message="created show successfully")

@shows_router.get("/{show_id}",status_code=status.HTTP_200_OK)
def get_show_by_id(show_id:str,show_service:ShowService=Depends(get_shows_service)):
    show_response=show_service.get_show_by_id(show_id)
    return APIResponse(
        status_code=200,
        message=f"successfully retrieved show",
        data=show_response
    )
    
@shows_router.get("",status_code=status.HTTP_200_OK)
def event_shows(event_id:str,city:str,date:str,show_service:ShowService=Depends(get_shows_service)):
    show_responses=show_service.get_event_shows(event_id,city,date)
    return APIResponse(
        status_code=200,
        message=f"successfully retrieved shows",
        data=show_responses
    )
    
@shows_router.patch("",status_code=status.HTTP_200_OK)
def update_show(show_id:str,req:ShowUpdateReq,current_user:dict=Depends(require_roles(["host"])),show_service:ShowService=Depends(get_shows_service),):
    show_responses=show_service.update_show(show_id=show_id,req=req)
    return APIResponse(
        status_code=200,
        message=f"successfully updated show",
    )