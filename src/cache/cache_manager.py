import json
import redis


class CacheManager:
    def __init__(
        self,
        host="localhost",
        port=6379,
        default_ttl=300,
    ):
        self.default_ttl = default_ttl

        self.client = redis.Redis(
            host=host,
            port=port,
            decode_responses=True,
        )

    def health_check(self):
        try:
            return self.client.ping()
        except redis.RedisError:
            return False

    def set(self, key, value, ttl=None):
        try:
            data = json.dumps(value)

            return self.client.set(
                key,
                data,
                ex=ttl or self.default_ttl,
            )
        except (redis.RedisError, TypeError):
            return False

    def get(self, key):
        try:
            data = self.client.get(key)

            if data is None:
                return None

            return json.loads(data)

        except (redis.RedisError, json.JSONDecodeError):
            return None

    def delete(self, key):
        try:
            return self.client.delete(key) > 0
        except redis.RedisError:
            return False