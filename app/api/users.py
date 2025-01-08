from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.users import UserCreate, UserResponse
from db.database import get_db
from services.users import UserService

router = APIRouter(prefix="/users", tags=["Users"])
user_service = UserService()


@router.post("/", response_model=UserResponse)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Создаёт нового пользователя.
    """
    created_user = await user_service.create_user(db, user)
    return created_user
