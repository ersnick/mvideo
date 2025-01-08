from repositories.users import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.users import UserCreate
from core.auth import verify_password, create_access_token


class UserService:
    def __init__(self):
        self.repository = UserRepository()

    async def create_user(self, db: AsyncSession, user_data: UserCreate):
        """
        Создаёт нового пользователя.
        """
        return await self.repository.create_user(db, user_data)

    async def authenticate_user(self, db: AsyncSession, username: str, password: str):
        """
        Аутентификация пользователя.
        """
        user = await self.repository.get_user_by_username(db, username)
        if user and verify_password(password, user.hashed_password):
            return user
        return None

    async def create_access_token(self, user):
        """
        Создаёт токен для пользователя.
        """
        return create_access_token({"sub": str(user.id), "role": user.role})
