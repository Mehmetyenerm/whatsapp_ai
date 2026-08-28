from fastapi import APIRouter, BackgroundTasks
from fastapi.params import Depends
from dependencies.llm_dep import search_internet, generate_voice
from dependencies.whatsapp_dep import send_wa_audio
from dependencies.config import  verify_api_key

router = APIRouter(
    prefix="/tool",
    tags=["Tool"]
)

@router.post("/websearch", dependencies=[Depends(verify_api_key)])
async def web_search(query: str):
    return search_internet(query)

@router.get("/generate_audio", dependencies=[Depends(verify_api_key)])
async def generate_audio(content: str, number: int, background_tasks: BackgroundTasks):
    background_tasks.add_task(generate_voice, content, number)
    return {"status": "received"}

@router.get("/send_voice", dependencies=[Depends(verify_api_key)])
async def send_voice(number: int, path: str):
    return send_wa_audio(number, path)