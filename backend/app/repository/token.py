from typing import Optional, List
from uuid import UUID
from pydantic import EmailStr
from sqlalchemy import select, delete

from app.core.db import db_session
from app.orm.token import TokenOrm


class TokenRepository:
    """Repository class for managing TokenOrm database operations."""

    @classmethod
    async def create(cls, data: TokenOrm) -> TokenOrm:
        """Create a new token."""
        async with db_session() as session:
            session.add(data)
            await session.flush()
            await session.commit()
            return data

    @classmethod
    async def list(cls) -> List[TokenOrm]:
        """List all tokens."""
        async with db_session() as session:
            query = select(TokenOrm)
            result = await session.execute(query)
            return result.scalars().all()

    @classmethod
    async def retrieve(cls, id: UUID) -> Optional[TokenOrm]:
        """Retrieve a token by ID."""
        async with db_session() as session:
            query = select(TokenOrm).where(TokenOrm.id == id)
            result = await session.execute(query)
            db_token = result.scalar_one_or_none()
            return db_token

    @classmethod
    async def retrieve_by_user_id(cls, user_id: UUID) -> Optional[TokenOrm]:
        """Retrieve a token by user ID."""
        async with db_session() as session:
            query = select(TokenOrm).where(TokenOrm.user_id == user_id).order_by(TokenOrm.created_at.desc())
            result = await session.execute(query)
            return result.scalars().first() or None

    @classmethod
    async def update(cls, data: TokenOrm) -> TokenOrm:
        """Update a token."""
        async with db_session() as session:
            session.add(data)
            await session.flush()
            await session.commit()
            return data

    @classmethod
    async def delete(cls, id: UUID) -> None:
        """Delete a token by ID."""
        async with db_session() as session:
            query = delete(TokenOrm).where(TokenOrm.id == id)
            await session.execute(query)
            await session.commit()