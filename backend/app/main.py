from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import init_db
from .routers import robot_router, logs_router, chat_router, voice_control_router
from .routers.recognition import router as recognition_router
from .routers.personality import router as personality_router
from .routers.tokens import router as tokens_router
from .routers.storage import router as storage_router
from .services.robot_service import robot_service
from .services.voice_tracking_service import voice_tracking_service
from .services.voice_control_service import voice_control_service

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database (optional - app works without it)
    await init_db()
    print("Backend starting...")
    yield
    # Cleanup
    if voice_control_service.is_running():
        await voice_control_service.stop()
    if voice_tracking_service.is_tracking():
        await voice_tracking_service.stop_tracking()
    if robot_service.connected:
        await robot_service.disconnect()
    print("Backend shutting down...")


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
app.include_router(voice_control_router)
app.include_router(recognition_router)
app.include_router(personality_router)
app.include_router(tokens_router)
app.include_router(storage_router)


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
