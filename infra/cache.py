import redis.asyncio as redis
from config import settings

class Cache:
    def __init__(self):
        self.redis_client = None

    async def connect(self):
        self.redis_client = redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)

    async def disconnect(self):
        if self.redis_client:
            await self.redis_client.aclose()

    async def get(self, key: str):
        if not self.redis_client:
            return None
        return await self.redis_client.get(key)
    
    async def set(self, key: str, value: str, ex: int = 86400):
        if self.redis_client:
            await self.redis_client.set(key, value, ex=ex)

    async def increment(self, key: str):
        if self.redis_client:
            await self.redis_client.incr(key)

cache = Cache()
