from sqlalchemy import Column, Integer, String, Text, Numeric, ForeignKey, DECIMAL, DateTime, Float
from datetime import datetime

from sqlalchemy.orm import relationship

from db.database import BaseModel


# Модель товара
class Product(BaseModel):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    rating = Column(Float, nullable=True)
    url = Column(String(255), nullable=False)
    price = Column(Float, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="products")
    # Связь с историей цен
    history = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")


# Модель истории цен
class PriceHistory(BaseModel):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    price = Column(Float, nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow)

    # Обратная связь к продукту
    product = relationship("Product", back_populates="history")
