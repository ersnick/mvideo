from api import products as products_api, users, auth
from exceptions.exceptions import AppException
from models import products
from db import database
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

# Подключение маршрутов
app.include_router(products_api.router)
app.include_router(users.router)
app.include_router(auth.router)


# Асинхронная функция для инициализации базы данных
async def init_db():
    async with database.engine.begin() as conn:
        # Создание таблиц, если их нет
        await conn.run_sync(products.BaseModel.metadata.create_all)


# Запуск инициализации базы данных при старте приложения
@app.on_event("startup")
async def startup_event():
    await init_db()


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.message}
    )
