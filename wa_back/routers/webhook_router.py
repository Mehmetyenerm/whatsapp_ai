from fastapi import APIRouter, BackgroundTasks
from fastapi.params import Depends
from typing import Annotated
from sqlmodel import Session
from schemas.main_schema import WhatsAppMessage
from dependencies.llm_dep import handle_message
from dependencies.config import  verify_api_key
from database import get_session

SessionDep = Annotated[Session, Depends(get_session)]

router = APIRouter(
    prefix="/webhook",
    tags=["Webhook"]
)

@router.post("/whatsapp", dependencies=[Depends(verify_api_key)])
async def webhook_listener(message:WhatsAppMessage, background_tasks: BackgroundTasks):
    background_tasks.add_task(handle_message,message)
    return { "status": "received" }