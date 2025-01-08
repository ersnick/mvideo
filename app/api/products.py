from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from core.auth import get_current_user
from db.database import get_db
from schemas.products import ProductView, ProductCreate, PriceHistoryView
from services.products import ProductService


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/products")
product_service = ProductService()


@router.get("/", response_model=List[ProductView])
async def read_products(
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_user),
):
    """
    Получить все товары.
    """
    try:
        return await product_service.get_products(db, current_user)
    except Exception as e:
        logger.error(f"Ошибка при получении списка товаров: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении списка товаров")


@router.get("/{product_id}", response_model=ProductView)
async def read_product(
        product_id: int, db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_user),
):
    """
    Получить товар по ID.
    """
    try:
        return await product_service.get_product_by_id(db, product_id, current_user)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Ошибка при получении товара с ID {product_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении товара")


@router.post("/", response_model=ProductView)
async def create_product(
        product: ProductCreate, db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_user),
):
    """
    Добавить новый товар.
    """
    try:
        return await product_service.add_product(db, product, current_user)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Ошибка при добавлении товара: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при добавлении товара")


@router.delete("/{product_id}")
async def delete_product(
        product_id: int, db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_user),
):
    """
    Удалить товар по ID.
    """
    try:
        deleted_product = await product_service.delete_product(db, product_id, current_user)
        if not deleted_product:
            raise HTTPException(status_code=404, detail=f"Товар с ID {product_id} не найден.")
        return {"message": "Товар успешно удален"}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Ошибка при удалении товара с ID {product_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при удалении товара")


@router.put("/{product_id}/price-history", response_model=List[PriceHistoryView])
async def update_price_history(
        product_id: int, db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_user),
):
    """
    Обновить историю цен товара по ID.
    """
    try:
        price_history = await product_service.update_price_history(db, product_id, current_user)
        if not price_history:
            raise HTTPException(
                status_code=404,
                detail=f"История цен для товара с ID {product_id} не найдена."
            )
        return price_history
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Ошибка при обновлении истории цен для товара с ID {product_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при обновлении истории цен")


@router.get("/{product_id}/price-history", response_model=List[PriceHistoryView])
async def get_price_history(
        product_id: int, db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_user),
):
    """
    Получить историю цен товара по ID.
    """
    try:
        price_history = await product_service.get_price_history(db, product_id, current_user)
        if not price_history:
            raise HTTPException(
                status_code=404,
                detail=f"История цен для товара с ID {product_id} не найдена."
            )
        return price_history
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Ошибка при получении истории цен для товара с ID {product_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении истории цен")
