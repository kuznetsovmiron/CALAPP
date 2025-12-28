from uuid import UUID
from typing import Optional, List
from sqlalchemy import select, func

from app.core.db import db_session
from app.orm.session import SessionOrm

class SessionRepository:
    """Repository for managing Session records database operations."""

    @classmethod
    async def retrieve(cls, id: UUID) -> Optional[SessionOrm]:
        async with db_session() as session:            
            stmt = select(SessionOrm).where(SessionOrm.id == id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()       

    @classmethod
    async def retrieve_by_user_id(cls, user_id: UUID) -> Optional[SessionOrm]:
        async with db_session() as session:            
            stmt = select(SessionOrm)
            stmt = stmt.where(SessionOrm.user_id == user_id).order_by(SessionOrm.created_at.desc())
            result = await session.execute(stmt)
            return result.scalars().first() or None             
        
    @classmethod
    async def create(cls, data: SessionOrm) -> SessionOrm:
        async with db_session() as session:
            session.add(data)
            await session.flush()
            await session.commit()
            return data

            
        
  