from typing import AsyncGenerator

import redis.asyncio as aioredis


pool = aioredis.ConnectionPool.from_url(
    "redis://@my_redis:6379/0",
    max_connections=5)


async def get_redis_conn() -> AsyncGenerator:
    redis_client = aioredis.Redis(connection_pool=pool)
    try:
        yield redis_client
    finally:
        await redis_client.close()
