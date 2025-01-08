from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

SECRET_KEY = "TX9aH5cJC9xn4IygzfPNCCOt"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as err:
        raise HTTPException(status_code=401, detail=f"Invalid token: {err}")


async def admin_required(user: dict = Depends(get_current_user)):
    """
    Проверка на наличие прав администратора.
    """
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Access forbidden")
    return user


def require_role(required_role: str):
    def role_checker(payload: dict = Depends(get_current_user)):
        if payload.get("role") != required_role:
            raise HTTPException(status_code=403, detail="Forbidden")
        return payload

    return role_checker
