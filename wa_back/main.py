from fastapi import FastAPI
from dotenv import load_dotenv
import logging
from contextlib import asynccontextmanager
from routers.main_router import router as main_router
from routers.webhook_router import router as webhook_router
from routers.tool_router import router as tool_router
from database import create_db_and_tables
from dependencies.settings import get_settings

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

logging.getLogger("numba").setLevel(settings.log)
load_dotenv()
app = FastAPI(lifespan=lifespan)

@app.get("/")
def read_root():
    return {"Message": "Hello World"}

app.include_router(main_router)
app.include_router(webhook_router)
app.include_router(tool_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)