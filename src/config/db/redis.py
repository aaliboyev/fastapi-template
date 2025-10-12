from redis.asyncio import Redis

from src.config.settings import settings
from src.lib.memory.redis import RedisMemory

redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
redis_memory = RedisMemory(redis_client)
