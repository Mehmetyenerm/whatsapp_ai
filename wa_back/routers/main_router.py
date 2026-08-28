from fastapi import HTTPException, APIRouter
from typing import Dict, Annotated
from requests import get, post, RequestException
from fastapi.params import Depends
from sqlmodel import Session
from database import get_session
from schemas.main_schema import Conversation
from dependencies.config import verify_api_key
from dependencies.settings import get_settings
from crud import get_convs

router = APIRouter(
    prefix="",
    tags=["Ollama"]
)
settings = get_settings()
conversations: Dict[str, Conversation] = {}
SessionDep = Annotated[Session, Depends(get_session)]

@router.get("/models")
async def list_models():
    try:
        response = get(f"{settings.ollama_url}/api/tags")
        response.raise_for_status()
        return {"models": response.json()["models"]}
    except RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching models: {str(e)}")


@router.post("/models/download", dependencies=[Depends(verify_api_key)])
async def download_model(model_name: str):
    try:
        response = post(
            f"{settings.ollama_url}/api/pull",
            json={"name": model_name}
        )
        response.raise_for_status()
        return {"message": f"Model {model_name} downloaded successfully"}
    except RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error downloading model: {str(e)}")

@router.get("/conversation", dependencies=[Depends(verify_api_key)])
async def get_conversation(session: SessionDep):
    return get_convs(session)


