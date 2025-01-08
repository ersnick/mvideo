from pydantic import BaseModel
from datetime import datetime
from typing import Optional


# Pydantic модель для создания товара
class ProductCreate(BaseModel):
    url: str


# Pydantic модель для отображения информации о товаре
class ProductView(BaseModel):
    id: int
    name: Optional[str]
    description: Optional[str]
    url: str
    price: Optional[float]
    rating: Optional[float]

    class Config:
        orm_mode = True
