import json
from typing import Any

from redis.asyncio import Redis


class RedisMemory:
    """
    MemoryIO is a class that implements the IO interface for the session store.

    It uses Redis to store session data with configurable TTL/expiration.
    Sessions are stored with the key pattern: session:{session_id}
    """

    def __init__(self, client: Redis) -> None:
        """Initialize an instance of MemoryIO."""
        self._redis_client: Redis = client

    def _make_key(self, session_id: str) -> str:
        """Generate Redis key for a session ID.

        Args:
            session_id: The session identifier

        Returns:
            Redis key in the format: session:{session_id}
        """
        return f"session:{session_id}"

    async def clear(self, session_id: str) -> None:
        """Clear the session store."""
        await self._redis_client.delete(self._make_key(session_id))

    async def has(self, key: str) -> bool:
        """Check if a session ID exists in Redis.

        Args:
            key: The session identifier to check

        Returns:
            True if the session exists, False otherwise
        """
        key = self._make_key(key)
        exists = await self._redis_client.exists(key)
        return bool(exists)

    async def has_no_session_id(self, session_id: str) -> bool:
        """Check if a session ID does not exist in Redis.

        Args:
            session_id: The session identifier to check

        Returns:
            True if the session does not exist, False otherwise
        """
        return not await self.has(session_id)

    async def get_store(self, session_id: str) -> dict[str, Any] | None:
        """Retrieve a session store from Redis.

        Args:
            session_id: The session identifier

        Returns:
            The session store dict if it exists, None otherwise
        """
        key = self._make_key(session_id)

        data = await self._redis_client.get(key)
        if data is None:
            return None

        try:
            return json.loads(data)
        except (json.JSONDecodeError, AttributeError):
            return None

    async def save_store(self, session_id: str, data: dict, ttl: int = None) -> None:
        """Save/update a session store in Redis.

        This method refreshes the TTL for the session.

        Args:
            :param session_id: Session identifier
            :param data: Data to store
        """

        key = self._make_key(session_id)
        await self._redis_client.set(key, json.dumps(data), ex=ttl)
