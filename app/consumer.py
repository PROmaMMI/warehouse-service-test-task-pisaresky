import os
import asyncio
import json
from aiokafka import AIOKafkaConsumer
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging

from .database import SessionLocal
from . import crud
from dotenv import load_dotenv

load_dotenv()


KAFKA_HOST = os.getenv("KAFKA_ADVERTISED_HOST_NAME", "localhost")
KAFKA_PORT = os.getenv("KAFKA_ADVERTISED_PORT", "9092")
KAFKA_BOOTSTRAP = f"{KAFKA_HOST}:{KAFKA_PORT}"
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "warehouse_movements")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "warehouse-service-group")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("consumer")


def parse_iso_timestamp(ts_str: str) -> datetime:

    return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))


async def consume():
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        group_id=KAFKA_GROUP_ID,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )
    await consumer.start()
    try:
        logger.info(f"Kafka-консьюмер запущен, слушаем топик '{KAFKA_TOPIC}'")
        async for msg in consumer:
            try:
                message = msg.value
                data = message.get("data", {})
                movement_id = data["movement_id"]
                warehouse_id = data["warehouse_id"]
                event = data["event"]  # "departure" или "arrival"
                product_id = data["product_id"]
                timestamp = parse_iso_timestamp(data["timestamp"])

                if event == "departure":
                    quantity = data["quantity_departure"]
                elif event == "arrival":
                    quantity = data["quantity_arrival"]
                else:
                    logger.warning(f"Неизвестный event '{event}' в сообщении {movement_id}")
                    continue

                db: Session = SessionLocal()
                mv = crud.create_or_update_movement(
                    db=db,
                    movement_id=movement_id,
                    product_id=product_id,
                    event=event,
                    warehouse_id=warehouse_id,
                    timestamp=timestamp,
                    quantity=quantity,
                )
                if event == "departure":
                    try:
                        crud.update_inventory_on_departure(
                            db=db,
                            warehouse_id=warehouse_id,
                            product_id=product_id,
                            quantity_departure=quantity,
                        )
                    except ValueError as ve:
                        logger.error(f"Ошибка инвентаря: {ve}. Пропускаем сообщение.")
                else:  
                    crud.update_inventory_on_arrival(
                        db=db,
                        warehouse_id=warehouse_id,
                        product_id=product_id,
                        quantity_arrival=quantity,
                    )

                db.close()
                logger.info(f"Обработано движение {movement_id} (event={event})")
            except KeyError as ke:
                logger.error(f"Неправильное сообщение: отсутствует ключ {ke}. Пропускаем.")
            except SQLAlchemyError as se:
                logger.error(f"Ошибка БД: {se}")
            except Exception as e:
                logger.exception(f"Непредвиденная ошибка при обработке сообщения: {e}")
    finally:
        await consumer.stop()


def start_consumer_loop():
    loop = asyncio.get_event_loop()
    loop.create_task(consume())
    loop.run_forever()


if __name__ == "__main__":
    start_consumer_loop()
