from typing import Optional, List
from uuid import UUID
from pydantic import EmailStr
from sqlalchemy import select

from app.core.db import db_session
from app.orm.user import UserOrm


class UserRepository:
    """Repository class for managing UserOrm database operations."""

    @classmethod
    async def login(cls, login: EmailStr, password: str) -> Optional[UserOrm]:
        """Authenticate a user by email and password."""
        async with db_session() as session:
            query = select(UserOrm)
            query = query.where(UserOrm.password == password, UserOrm.email == login)
            result = await session.execute(query)
            db_user = result.scalar_one_or_none()
            return db_user

    @classmethod
    async def list(cls) -> List[UserOrm]:
        """Retrieve a list of users."""
        async with db_session() as session:
            query = select(UserOrm)
            result = await session.execute(query)
            return result.scalars().all()

    @classmethod
    async def retrieve(cls, id: UUID) -> Optional[UserOrm]:
        """Retrieve a user by their unique ID."""
        async with db_session() as session:
            query = select(UserOrm).where(UserOrm.id == id)
            result = await session.execute(query)
            db_user = result.scalar_one_or_none()
            return db_user

    @classmethod
    async def retrieve_by_email(cls, email: EmailStr) -> Optional[UserOrm]:
        """Retrieve a user by their email (login)."""
        async with db_session() as session:
            query = select(UserOrm).where(UserOrm.email == email)
            result = await session.execute(query)
            db_user = result.scalar_one_or_none()
            return db_user

    @classmethod
    async def create(cls, data: UserOrm) -> UserOrm:
        """Create a new user in the database."""
        async with db_session() as session:
            session.add(data)
            await session.flush()
            await session.commit()
            return data

    @classmethod
    async def update(cls, data: UserOrm) -> UserOrm:
        """Update an existing user in the database."""
        async with db_session() as session:
            session.add(data)
            await session.flush()
            await session.commit()
            return data

