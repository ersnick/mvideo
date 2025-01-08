import aio_pika
import asyncio
import json
import logging


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
RABBIT_REPLY = "amq.rabbitmq.reply-to"


async def send_message_rabbitmq(product_url: str, queue_name: str):
    connection = await aio_pika.connect_robust(
        "amqp://guest:guest@rabbitmq/"
    )

    async with connection:
        channel = await connection.channel()

        callback_queue = await channel.get_queue(RABBIT_REPLY)

        # создаем asyncio.Queue для ответа
        rq = asyncio.Queue(maxsize=1)

        # сначала подписываемся
        consumer_tag = await callback_queue.consume(
            callback=rq.put,  # помещаем сообщение в asyncio.Queue
            no_ack=True,
        )

        # потом публикуем
        await channel.default_exchange.publish(
            message=aio_pika.Message(
                body=f'{product_url}'.encode("utf-8"),
                reply_to=RABBIT_REPLY  # указываем очередь для ответа
            ),
            routing_key=f"{queue_name}"
        )

        # получаем ответ из asyncio.Queue
        response = await rq.get()
        response_data = json.loads(response.body.decode("utf-8"))

        # освобождаем RABBIT_REPLY
        await callback_queue.cancel(consumer_tag)

        return response_data
