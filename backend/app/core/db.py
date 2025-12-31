import logging
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.config import DB_LINK


logger = logging.getLogger(__name__)
engine = create_async_engine(DB_LINK, echo=False)
logger.warning(f"LOGGER: Connected to database: {DB_LINK}")
db_session = async_sessionmaker[AsyncSession](engine,expire_on_commit=False)