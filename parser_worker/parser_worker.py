import asyncio
import json
import logging
import aio_pika
from functools import partial

from parser import MvidParser

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def get_product_data_consumer(
    msg: aio_pika.IncomingMessage,
    channel: aio_pika.RobustChannel,
):
    # используем контекстный менеджер для ack'а сообщения
    async with msg.process():
        logger.info(f'Сообщение: {msg.body}')

        mvid_parser = MvidParser()

        product_url = msg.body.decode("utf-8")
        product_name, product_rating, product_description = await mvid_parser.get_product_data(product_url)
        product_price = await mvid_parser.get_product_price(product_url)

        # Формируем словарь с данными
        product_data = {
            "url": product_url,
            "name": product_name,
            "rating": product_rating,
            "description": product_description,
            "price": product_price,
        }

        # проверяем, требует ли сообщение ответа
        if msg.reply_to:
            # Преобразуем словарь в JSON-строку
            product_data_json = json.dumps(product_data)

            # отправляем ответ в default exchange
            await channel.default_exchange.publish(
                message=aio_pika.Message(
                    body=product_data_json.encode("utf-8"),
                    correlation_id=msg.correlation_id,
                ),
                routing_key=msg.reply_to,
            )


async def get_product_price_consumer(
    msg: aio_pika.IncomingMessage,
    channel: aio_pika.RobustChannel,
):
    # используем контекстный менеджер для ack'а сообщения
    async with msg.process():
        logger.info(f'Сообщение: {msg.body}')

        product_url = msg.body.decode("utf-8")

        mvid_parser = MvidParser()
        product_price = await mvid_parser.get_product_price(product_url)

        product_price_data = {
            "price": product_price,
        }

        # проверяем, требует ли сообщение ответа
        if msg.reply_to:
            # Преобразуем словарь в JSON-строку
            product_price_data_json = json.dumps(product_price_data)

            # отправляем ответ в default exchange
            await channel.default_exchange.publish(
                message=aio_pika.Message(
                    body=product_price_data_json.encode("utf-8"),
                    correlation_id=msg.correlation_id,
                ),
                routing_key=msg.reply_to,
            )


async def main():
    # Подключение к RabbitMQ
    connection = await aio_pika.connect_robust("amqp://guest:guest@rabbitmq/")

    async with connection:
        channel = await connection.channel()

        # Объявляем очереди
        get_product_queue = await channel.declare_queue("get_product_data", durable=True)
        get_price_queue = await channel.declare_queue("get_product_price", durable=True)

        # через partial прокидываем в наш обработчик сам канал
        await get_product_queue.consume(partial(get_product_data_consumer, channel=channel))
        await get_price_queue.consume(partial(get_product_price_consumer, channel=channel))

        try:
            logger.info("Слушатель RabbitMQ запущен. Ожидание сообщений...")
            await asyncio.Future()
        except Exception as e:
            logger.error(f'Ошибка при инициализации консьюмера: {e}')


if __name__ == "__main__":
    asyncio.run(main())
