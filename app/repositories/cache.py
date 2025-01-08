import json

from redis.asyncio import Redis
import logging
from CustomJSONEncoder import CustomJSONEncoder


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CacheRepository:
    def __init__(self):
        self.redis_client = Redis(host="redis", port=6379, decode_responses=True)

    async def get(self, key: str):
        """Получает значение из кэша по ключу."""
        value = await self.redis_client.get(key)
        if value:
            logger.info(f"Returning cached data for key: {key}")
            return json.loads(value)
        return None

    async def set(self, key: str, value, ttl: int = 60):
        """Устанавливает значение в кэше с указанным временем жизни."""
        await self.redis_client.setex(key, ttl, json.dumps(value, cls=CustomJSONEncoder))
        logger.info(f"Cached data for key: {key} with TTL {ttl}")

    async def delete(self, key: str):
        """Удаляет значение из кэша по ключу."""
        await self.redis_client.delete(key)
        logger.info(f"Deleted cache for key: {key}")

    async def close(self):
        """Закрывает соединение с Redis."""
        await self.redis_client.close()
