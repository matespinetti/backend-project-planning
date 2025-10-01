import logging

from app.db.base import Base
from app.db.session import engine

logger = logging.getLogger(__name__)


async def init_db() -> None:
    """
    Create all database tables asynchronously.
    This is called on application startup.
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise
