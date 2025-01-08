from decimal import Decimal
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from exceptions import DatabaseError, ProductNotFound, HistoryNotFound
from models.products import Product, PriceHistory
import logging


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ProductRepository:
    async def get_all_products(self, db: AsyncSession) -> List[Product]:
        """Получить все товары из базы данных (для админа)."""
        try:
            result = await db.execute(select(Product))
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Ошибка при получении всех товаров: {e}")
            raise DatabaseError(str(e))

    async def get_user_products(self, db: AsyncSession, user_id: int) -> List[Product]:
        """Получить все товары из базы данных для определенного пользователя."""
        try:
            result = await db.execute(select(Product).where(Product.owner_id == user_id))
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Ошибка при получении всех товаров: {e}")
            raise DatabaseError(str(e))

    async def get_product_by_url_user(self, db: AsyncSession, url: str, user_id: int) -> Optional[Product]:
        """Получить товар по URL для определенного пользователя."""
        try:
            result = await db.execute(
                select(Product).where((Product.url == url) & (Product.owner_id == user_id))
            )
            return result.scalar_one_or_none()  # Возвращаем None, если продукт отсутствует
        except Exception as e:
            logger.error(f"Ошибка при получении товара по URL {url}: {e}")
            raise DatabaseError(str(e))

    async def get_product_by_url_admin(self, db: AsyncSession, url: str) -> Optional[Product]:
        """Получить товар по URL для определенного пользователя."""
        try:
            result = await db.execute(
                select(Product).where(Product.url == url)
            )
            return result.scalar_one_or_none()  # Возвращаем None, если продукт отсутствует
        except Exception as e:
            logger.error(f"Ошибка при получении товара по URL {url}: {e}")
            raise DatabaseError(str(e))

    async def get_product_by_id_user(self, db: AsyncSession, product_id: int, user_id: int) -> Optional[Product]:
        """Получить товар по ID для определенного пользователя."""
        try:
            result = await db.execute(
                select(Product).where((Product.id == product_id) & (Product.owner_id == user_id))
            )
            product = result.scalar_one_or_none()
            if not product:
                raise ProductNotFound(str(product_id))
            else:
                return product
        except ProductNotFound:
            raise
        except Exception as e:
            logger.error(f"Ошибка при получении товара по ID {product_id}: {e}")
            raise DatabaseError(str(e))

    async def get_product_by_id_admin(self, db: AsyncSession, product_id: int) -> Optional[Product]:
        """Получить товар по ID для определенного пользователя."""
        try:
            result = await db.execute(select(Product).where(Product.id == product_id))
            product = result.scalar_one_or_none()
            if not product:
                raise ProductNotFound(str(product_id))
            else:
                return product
        except ProductNotFound:
            raise
        except Exception as e:
            logger.error(f"Ошибка при получении товара по ID {product_id}: {e}")
            raise DatabaseError(str(e))

    async def get_price_history_admin(self, db: AsyncSession, product_id: int):
        """Получить историю товара по ID (для админа)."""
        try:
            # Запрос с объединением таблиц PriceHistory и Product
            result = await db.execute(
                select(PriceHistory).where(PriceHistory.product_id == product_id)
            )
            history = result.scalars().all()
            if not history:
                raise HistoryNotFound(str(product_id))
            else:
                return history
        except HistoryNotFound:
            raise
        except Exception as e:
            logger.error(f"Ошибка при получении истории товара по ID {product_id}: {e}")
            raise DatabaseError(str(e))

    async def get_price_history_user(self, db: AsyncSession, product_id: int, user_id: int):
        """Получить историю товара по ID при его наличии у пользователя."""
        try:
            # Запрос с объединением таблиц PriceHistory и Product
            result = await db.execute(
                select(PriceHistory)
                .join(Product, PriceHistory.product_id == Product.id)
                .where((Product.owner_id == user_id) & (Product.id == product_id))
                .options(joinedload(PriceHistory.product))  # Для предварительной загрузки связи
            )
            history = result.scalars().all()
            if not history:
                raise HistoryNotFound(str(product_id))
            else:
                return history
        except HistoryNotFound:
            raise
        except Exception as e:
            logger.error(f"Ошибка при получении истории товара по ID {product_id}: {e}")
            raise DatabaseError(str(e))

    async def add_price_history(self, db: AsyncSession, product_id: int, price: float) -> List[PriceHistory]:
        """Добавить запись в историю цен."""
        try:
            price_history = PriceHistory(product_id=product_id, price=price)
            db.add(price_history)
            await db.commit()

            # Получение актуальной истории цен
            result = await db.execute(
                select(PriceHistory).where(PriceHistory.product_id == product_id)
            )
            history = result.scalars().all()

            if not history:
                raise DatabaseError(f"Не удалось получить историю цен для товара с ID {product_id}.")

            return history
        except Exception as e:
            await db.rollback()
            logger.error(f"Ошибка при добавлении истории цен для товара {product_id}: {e}")
            raise DatabaseError(f"Ошибка при добавлении истории цен: {e}")

    async def add_product(self, db: AsyncSession, product_data: dict, owner_id: int) -> Product:
        """Добавить товар в базу данных для определенного пользователя."""
        try:
            # Проверка обязательных полей
            required_fields = ['name', 'description', 'rating', 'url', 'price']
            for field in required_fields:
                if field not in product_data:
                    raise ValueError(f"Отсутствует обязательное поле: {field}")

            product_instance = Product(
                name=product_data['name'],
                description=product_data['description'],
                rating=round(product_data['rating'], 2),
                url=product_data['url'],
                price=Decimal(product_data['price']),
                owner_id=owner_id,
            )
            db.add(product_instance)
            await db.commit()
            await db.refresh(product_instance)  # Обновление объекта с данными из БД
            return product_instance
        except ValueError as ve:
            logger.error(f"Некорректные данные для товара: {ve}")
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            await db.rollback()
            logger.error(f"Ошибка при добавлении товара: {e}")
            raise DatabaseError(f"Ошибка при добавлении товара: {e}")

    async def delete_product(self, db: AsyncSession, product_id: int, user_id: int) -> Product:
        """Удалить товар по ID для определенного пользователя."""
        try:
            db_product = await self.get_product_by_id_user(db, product_id, user_id)

            if not db_product:
                raise HTTPException(
                    status_code=404,
                    detail=f"Товар с ID {product_id} не найден."
                )

            await db.delete(db_product)
            await db.commit()
            return db_product
        except HTTPException:
            raise  # Перебрасываем, чтобы API мог вернуть правильный статус
        except Exception as e:
            await db.rollback()
            logger.error(f"Ошибка при удалении товара по ID {product_id}: {e}")
            raise DatabaseError(f"Ошибка при удалении товара: {e}")

    async def update_product(self, db: AsyncSession, product_id: int, update_data: dict, user_id: int) -> Product:
        """Обновить товар в базе данных для определенного пользователя."""
        try:
            result = await self.get_product_by_id_user(db, product_id, user_id)
            product = result.scalar_one_or_none()
            if not product:
                raise ProductNotFound(product_id)

            for field, value in update_data.items():
                if hasattr(product, field):
                    setattr(product, field, value)

            await db.commit()
            await db.refresh(product)
            return product
        except ProductNotFound:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Ошибка при обновлении товара {product_id}: {e}")
            raise DatabaseError(f"Не удалось обновить товар: {e}")
