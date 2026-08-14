import time

from src.cache.cache_manager import CacheManager


def test_redis_health():
    cache = CacheManager()

    assert cache.health_check() is True


def test_cache_set_and_get():
    cache = CacheManager()

    cache.set(
        "test:shipment",
        {
            "count": 100,
            "status": "delivered",
        },
    )

    result = cache.get("test:shipment")

    assert result["count"] == 100
    assert result["status"] == "delivered"


def test_cache_delete():
    cache = CacheManager()

    cache.set("test:delete", {"value": 123})

    assert cache.delete("test:delete") is True
    assert cache.get("test:delete") is None


def test_cache_ttl_expiration():
    cache = CacheManager()

    cache.set(
        "test:ttl",
        {"value": 123},
        ttl=2,
    )

    assert cache.get("test:ttl") == {"value": 123}

    time.sleep(3)

    assert cache.get("test:ttl") is None