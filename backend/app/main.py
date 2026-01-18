from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import init_db
from .routers import robot_router, logs_router, chat_router
from .services.robot_service import robot_service

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    if robot_service.connected:
        await robot_service.disconnect()


app = FastAPI(
    title="Network School Robot API",
    description="API for controlling and monitoring the Reachy Mini robot",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(robot_router)
app.include_router(logs_router)
app.include_router(chat_router)


@app.get("/")
async def root():
    return {
        "name": "Network School Robot API",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    status = await robot_service.get_status()
    return {
        "status": "healthy",
        "robot_connected": status["connected"]
    }
