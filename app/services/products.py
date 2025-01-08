from decimal import Decimal
import logging
from typing import List

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.cache import CacheRepository
from repositories.products import ProductRepository
from exceptions import ProductNotFound, AppException
from models.products import Product, PriceHistory
from schemas.products import ProductCreate
from services.messaging import send_message_rabbitmq


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ProductService:
    def __init__(self):
        self.repository = ProductRepository()
        self.cache = CacheRepository()

    async def get_products(self, db: AsyncSession, current_user: dict) -> List[Product]:
        """Получить список всех товаров. Администраторы видят все товары, пользователи — только свои."""
        if current_user['role'] == 'admin':
            cache_key = f"products:list"
        else:
            cache_key = f"products:{current_user['sub']}"
        cached_products = await self.cache.get(cache_key)

        if cached_products:
            logger.info("Возвращаем товары из кэша.")
            return cached_products

        logger.info("Кэш пуст. Получаем товары из базы данных.")

        if current_user['role'] == 'admin':
            products = await self.repository.get_all_products(db)
        else:
            products = await self.repository.get_user_products(db, int(current_user['sub']))

        await self.cache.set(cache_key, [product.to_dict() for product in products], ttl=3600)  # Кэшируем результат на 1 час
        return products

    async def get_product_by_id(self, db: AsyncSession, product_id, current_user: dict):
        """Получить товар по ID."""
        cache_key = f"product:{product_id}"
        cached_product = await self.cache.get(cache_key)

        if (cached_product and cached_product['owner_id'] == current_user["sub"]) or (cached_product and current_user["role"] == "admin"):
            logger.info(f"Возвращаем товар {product_id} из кэша.")
            return cached_product
        elif current_user["role"] == "admin":
            try:
                logger.info(f"Кэш пуст. Получаем товар {product_id} из базы данных.")
                product = await self.repository.get_product_by_id_user(db, product_id)
                await self.cache.set(cache_key, product.to_dict(), ttl=3600)  # Кэшируем результат на 1 час
                return product
            except ProductNotFound:
                raise
            except Exception as e:
                logger.error(f"Ошибка сервиса при получении товара по ID {product_id}: {e}")
                raise AppException("Не удалось получить товар", status_code=500)
        else:
            try:
                logger.info(f"Кэш пуст. Получаем товар {product_id} из базы данных.")
                product = await self.repository.get_product_by_id_user(db, product_id, int(current_user["sub"]))
                await self.cache.set(cache_key, product.to_dict(), ttl=3600)  # Кэшируем результат на 1 час
                return product
            except ProductNotFound:
                raise
            except Exception as e:
                logger.error(f"Ошибка сервиса при получении товара по ID {product_id}: {e}")
                raise AppException("Не удалось получить товар", status_code=500)

    async def get_price_history(self, db: AsyncSession, product_id: int, current_user: dict) -> List[PriceHistory]:
        """Получить историю цен для товара."""
        cache_key = f"price_history:{product_id}"
        cached_history = await self.cache.get(cache_key)

        if current_user["role"] == "admin":
            if cached_history:
                logger.info(f"Возвращаем историю цен для товара {product_id} из кэша.")
                return cached_history

            logger.info(f"Кэш пуст. Получаем историю цен для товара {product_id} из базы данных.")
            price_history = await self.repository.get_price_history_admin(db, product_id)
            await self.cache.set(cache_key, [price_hist.to_dict() for price_hist in price_history], ttl=3600)  # Кэшируем результат на 1 час
            return price_history
        else:
            try:
                product = await self.repository.get_product_by_id_user(db, product_id, int(current_user["sub"]))
                if cached_history:
                    logger.info(f"Возвращаем историю цен для товара {product_id} из кэша.")
                    return cached_history

                logger.info(f"Кэш пуст. Получаем историю цен для товара {product_id} из базы данных.")
                price_history = await self.repository.get_price_history_admin(db, product_id)
                await self.cache.set(cache_key, [price_hist.to_dict() for price_hist in price_history],
                                     ttl=3600)  # Кэшируем результат на 1 час
                return price_history
            except ProductNotFound:
                raise

    async def add_product(self, db: AsyncSession, product_create: ProductCreate, current_user: dict) -> Product:
        """Добавить новый товар, если его нет в базе данных."""
        owner_id = int(current_user["sub"])

        # Проверяем, существует ли продукт в базе
        product_exist = await self.repository.get_product_by_url_admin(db=db, url=product_create.url)
        if product_exist:
            raise HTTPException(
                status_code=409,
                detail=f'Продукт с URL {product_exist.url} уже существует в базе данных'
            )

        # Получаем данные о продукте через RabbitMQ
        product_data = await send_message_rabbitmq(product_create.url, 'get_product_data')
        if not product_data or 'price' not in product_data:
            raise AppException(
                "Некорректные данные о продукте, полученные через RabbitMQ",
                status_code=500
            )

        # Добавление товара
        try:
            new_product = await self.repository.add_product(db, product_data, owner_id)
            await self.repository.add_price_history(db, new_product.id, new_product.price)

            # Обновляем кэш
            await self.cache.delete("products:list")  # Удаляем список всех товаров
            await self.cache.delete(f"products:{current_user['sub']}")
            await self.cache.set(f"product:{new_product.id}", new_product.to_dict(), ttl=3600)

            return new_product
        except Exception as e:
            logger.error(f"Ошибка при добавлении товара: {e}")
            raise AppException("Ошибка при добавлении товара", status_code=500)

    async def delete_product(self, db: AsyncSession, product_id: int, current_user: dict) -> Product:
        """Удалить товар по ID."""
        product = await self.repository.delete_product(db, product_id, int(current_user["sub"]))
        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Товар с ID {product_id} не найден."
            )

        # Удаляем товар из кэша
        await self.cache.delete(f"product:{product_id}")
        await self.cache.delete("products:list")  # Удаляем список всех товаров
        await self.cache.delete(f"products:{current_user['sub']}")
        return product

    async def update_price_history(self, db: AsyncSession, product_id: int, current_user: dict) -> List[PriceHistory]:
        """Обновить историю цен товара."""
        try:
            product = await self.repository.get_product_by_id_user(db, product_id, int(current_user["sub"]))
        except ProductNotFound:
            raise

        # Получаем актуальную цену через RabbitMQ
        product_data = await send_message_rabbitmq(product.url, 'get_product_price')
        if not product_data or 'price' not in product_data:
            raise AppException(
                f"Некорректные данные о цене для товара с ID {product_id}, полученные через RabbitMQ",
                status_code=500
            )

        # Обновляем историю цен
        try:
            price_history = await self.repository.add_price_history(db, product_id, product_data['price'])

            # Обновляем кэш
            await self.cache.delete(f"price_history:{product_id}")
            await self.cache.set(f"price_history:{product_id}", [price_hist.to_dict() for price_hist in price_history], ttl=3600)

            return price_history
        except Exception as e:
            logger.error(f"Ошибка при обновлении истории цен для товара с ID {product_id}: {e}")
            raise AppException("Ошибка при обновлении истории цен", status_code=500)
