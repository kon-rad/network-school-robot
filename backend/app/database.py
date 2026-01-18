from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from .config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

# Database connection is optional for development
engine = None
async_session_maker = None
db_available = False

try:
    engine = create_async_engine(settings.database_url, echo=False)
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
except Exception as e:
    logger.warning(f"Database engine creation failed: {e}")


class Base(DeclarativeBase):
    pass


async def get_db():
    if not async_session_maker:
        raise RuntimeError("Database not available")
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    global db_available
    if not engine:
        logger.warning("Database not configured - skipping initialization")
        return

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        db_available = True
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning(f"Database connection failed: {e}")
        logger.warning("Running without database - some features may be unavailable")
        db_available = False
