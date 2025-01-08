from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from services.users import UserService

router = APIRouter(prefix="/auth")
user_service = UserService()


@router.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    """
    Маршрут для получения токена.
    """
    user = await user_service.authenticate_user(
        db, form_data.username, form_data.password
    )
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = await user_service.create_access_token(user)
    return {"access_token": access_token, "token_type": "bearer"}
