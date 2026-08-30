"""Optional Redis cache with a safe no-op fallback."""

import json
import logging
from typing import Any

from src.config import settings

logger = logging.getLogger(__name__)


class CacheManager:
    def __init__(self, url: str | None = None) -> None:
        self._client = None
        cache_url = settings.redis_url if url is None else url
        if not cache_url:
            return
        try:
            import redis
            client = redis.from_url(cache_url, decode_responses=True)
            client.ping()
            self._client = client
        except (ImportError, OSError, ConnectionError) as exc:
            logger.info("Redis cache unavailable; continuing without cache: %s", exc)

    @property
    def available(self) -> bool:
        return self._client is not None

    def get_json(self, key: str) -> Any | None:
        if not self._client:
            return None
        try:
            value = self._client.get(key)
            return json.loads(value) if value else None
        except (OSError, ValueError) as exc:
            logger.warning("Redis read failed: %s", exc)
            return None

    def set_json(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        if not self._client:
            return
        try:
            self._client.setex(key, ttl_seconds, json.dumps(value))
        except (OSError, TypeError, ValueError) as exc:
            logger.warning("Redis write failed: %s", exc)
