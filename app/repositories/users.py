from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.users import User
from schemas.users import UserCreate
from core.auth import hash_password


class UserRepository:
    async def create_user(self, db: AsyncSession, user_data: UserCreate) -> User:
        """
        Создание нового пользователя с хэшированным паролем.
        """
        hashed_password = hash_password(user_data.password)
        user = User(
            username=user_data.username,
            hashed_password=hashed_password,
            role=user_data.role,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def get_user_by_username(self, db: AsyncSession, username: str) -> User:
        """
        Получение пользователя по имени пользователя.
        """
        result = await db.execute(select(User).filter(User.username == username))
        return result.scalars().first()
