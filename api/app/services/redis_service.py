from redis import asyncio as aioredis
from typing import Any, Dict, Optional
import json
import logging

class RedisService:
    def __init__(self, redis_url: str = "redis://redis:6379"):
        self.redis_url = redis_url
        self.redis = None

    async def connect(self):
        """Initialize the Redis connection."""
        if not self.redis:
            try:
                self.redis = aioredis.from_url(self.redis_url, decode_responses=True)
            except Exception as e:
                logging.error(f"Failed to connect to Redis: {e}")
                raise

    async def disconnect(self):
        """Close the Redis connection."""
        if self.redis:
            try:
                await self.redis.close()
            except Exception as e:
                logging.error(f"Failed to close Redis connection: {e}")

    async def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from Redis."""
        try:
            await self.connect()
            value = await self.redis.get(key)
            if value:
                return json.loads(value)  # Deserialize JSON string to Python object
            return None
        except json.JSONDecodeError as e:
            logging.error(f"Failed to decode JSON for key '{key}': {e}")
            return None
        except Exception as e:
            logging.error(f"Error retrieving key '{key}' from Redis: {e}")
            return None

    async def set(self, key: str, value: Any, expire: int = 600):
        """
        Store a value in Redis with an optional expiration time.
        Default expiration is 600 seconds (10 minutes).
        """
        try:
            await self.connect()
            serialized_value = json.dumps(value)  # Serialize Python object to JSON string
            if expire > 0:
                await self.redis.set(key, serialized_value, ex=expire)
            else:
                await self.redis.set(key, serialized_value)
        except json.JSONDecodeError as e:
            logging.error(f"Failed to encode JSON for key '{key}': {e}")
            raise
        except Exception as e:
            logging.error(f"Error setting key '{key}' in Redis: {e}")
            raise

    async def delete(self, key: str):
        """Delete a key from Redis."""
        try:
            await self.connect()
            await self.redis.delete(key)
        except Exception as e:
            logging.error(f"Error deleting key '{key}' from Redis: {e}")
            raise

# Initialize the Redis service
redis_service = RedisService()
