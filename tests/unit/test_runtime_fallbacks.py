from src.cache import CacheManager
from src.memory.embedding_manager import embedding_device


def test_redis_is_optional_without_url():
    cache = CacheManager(url="")
    assert not cache.available
    assert cache.get_json("missing") is None


def test_embedding_device_has_cpu_fallback():
    assert embedding_device() in {"cpu", "cuda"}