from typing import AsyncGenerator, Annotated
import asyncio
import json
import uuid

from fastapi import HTTPException, Query, status
import aio_pika

from db_init import AsyncSessionLocal
import schemas


def validate_categorys(category_names: Annotated[list[str],
                                                 Query(description='Filter by category')]) -> list[str]:
    valid_categories = [],
    for category in category_names:
        try:
            valid_category = schemas.FilterCategory(category_name=category)
            valid_categories.append(valid_category)
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))

    return valid_categories


def get_db_conn() -> AsyncGenerator:
    db_conn = AsyncSessionLocal()
    try:
        yield db_conn
    finally:
        db_conn.close()


class RegistrationParcelRPClient:

    def __init__(self):
        self.response_data = None
        self.connection = None
        self.channel = None
        self.callback_queue = None
        self.response = None
        self.corr_id = None

    async def connect(self):
        self.connection = await aio_pika.connect_robust(host='rabbitmq')
        self.channel = await self.connection.channel()

        self.callback_queue = await self.channel.declare_queue('', exclusive=True)
        await self.callback_queue.consume(self.on_response)

    async def on_response(self, message: aio_pika.IncomingMessage):
        async with message.process():
            if self.corr_id == message.correlation_id:
                response_data = json.loads(message.body.decode('utf-8'))
                if 'error' in response_data:
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                        detail=response_data['error'])
                else:
                    self.response = response_data

    async def call(self, parcel):
        self.response = None
        self.corr_id = str(uuid.uuid4())

        await self.channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(parcel).encode(),
                correlation_id=self.corr_id,
                reply_to=self.callback_queue,
            ),
            routing_key='register_parcel',
        )

        while self.response is None:
            await asyncio.sleep(0.1)

        return self.response


async def get_rpc_client() -> RegistrationParcelRPClient:
    client = RegistrationParcelRPClient()
    await client.connect()
    return client
