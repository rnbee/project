from datetime import datetime, timedelta
from typing import Tuple
import json

import mysql.connector
import requests
import redis
import pika


connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='rabbitmq', port=5672))
channel = connection.channel()
channel.queue_declare(queue='register_parcel')

redis_client = redis.Redis.from_url("redis://@my_redis:6379/0")


def get_usd_from_api() -> Tuple[float, int]:
    """ """

    response = requests.get("https://www.cbr-xml-daily.ru/daily_json.js", timeout=5)

    usd_value: float = response.json()['Valute']['USD']['Value']
    data: str = response.json()['Date']

    # К полученой дате прибавляем один день
    expireAt = datetime.fromisoformat(data) + timedelta(days=1)
    expireAt = int(expireAt.timestamp())
    return usd_value, expireAt


def cashed_usd_value(usd_info: tuple) -> None:
    """Кеширует курс доллара к рублю и устанавливает ttl."""

    usd_value, expireAt = usd_info

    with redis_client.pipeline() as pipe:
        pipe.set(name="usd_value", value=usd_value)
        pipe.expireat(name="usd_value", when=expireAt)
        pipe.execute()


def get_usd_value() -> float:
    """Получает значения USD из Redis или API, в случаи его отсутсвия."""

    usd_value: str = redis_client.get("usd_value")
    if usd_value is None:
        usd_value, expireAt = get_usd_from_api()
        cashed_usd_value((usd_value, expireAt))
        return float(usd_value)

    return float(usd_value.decode('utf-8'))


def calculate_delivery_cost(*, weight, cost) -> float:
    """Вычесляет стоимость доставки по формуле:
    (вес в кг. * 0.5 + стоимость содержимого в долларах * 0.01 ) * курс доллара к рублю."""
    usd_value: float = get_usd_value()
    delivery_cost = (weight * 0.5 + cost * 0.01) * usd_value

    return delivery_cost


def get_saving_parcel_id(query: str, values: tuple) -> int:
    """Сохраняет посылку в db и возвращает id созданной посылки."""

    try:
        conn = mysql.connector.connect(
            host="mysql_db", user="enemy", password="root", database="project")

        cursor = conn.cursor()
        cursor.execute(query, values)
        conn.commit()
        return cursor.lastrowid
    except Exception as error:
        return error
    finally:
        cursor.close()
        conn.close()


def register_parcel(**kwargs) -> dict:
    """Регистрирует посылки."""

    columns = ', '.join(kwargs.keys())
    placeholders = ', '.join(['%s'] * len(kwargs))

    query = f"""
        INSERT INTO parcels({columns})
        VALUES ({placeholders})
        """
    values = tuple(kwargs.values())

    kwargs['id'] = get_saving_parcel_id(query, values)
    kwargs.pop('session_id')

    return kwargs


def on_request(ch, method, props, body):
    parcel_params: dict = json.loads(body)

    delivery_cost: float = calculate_delivery_cost(weight=parcel_params['weight'],
                                                   cost=parcel_params['cost'])

    parcel_params['delivery_cost'] = delivery_cost
    parcel_info = register_parcel(**parcel_params)

    ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(correlation_id=props.correlation_id),
                     body=json.dumps(parcel_info).encode())
    ch.basic_ack(delivery_tag=method.delivery_tag)


channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='register_parcel', on_message_callback=on_request)
print(" [x] Awaiting RPC requests")
channel.start_consuming()
