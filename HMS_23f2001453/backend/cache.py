# cache.py
"""
Redis cache layer.
Usage:
    from cache import cache
    cache.set('key', value, ttl=300)
    value = cache.get('key')          # returns None on miss
    cache.delete('key')
    cache.delete_pattern('doctors:*') # wildcard invalidation
"""
import json
import redis
from functools import wraps
from flask import current_app


class RedisCache:
    _client = None

    def _get_client(self):
        if self._client is None:
            url = current_app.config.get('CACHE_REDIS_URL', 'redis://localhost:6379/1')
            self._client = redis.from_url(url, decode_responses=True)
        return self._client

    def get(self, key):
        try:
            raw = self._get_client().get(key)
            return json.loads(raw) if raw is not None else None
        except Exception:
            return None

    def set(self, key, value, ttl=300):
        try:
            self._get_client().setex(key, ttl, json.dumps(value))
        except Exception:
            pass   # cache failure is non-fatal

    def delete(self, key):
        try:
            self._get_client().delete(key)
        except Exception:
            pass

    def delete_pattern(self, pattern):
        """Delete all keys matching a glob pattern e.g. 'doctors:*'"""
        try:
            client = self._get_client()
            keys = client.keys(pattern)
            if keys:
                client.delete(*keys)
        except Exception:
            pass

    def cached(self, key_fn, ttl=300):
        """
        Decorator factory for caching function return values.

        Usage:
            @cache.cached(lambda: 'doctors:all', ttl=300)
            def get_all_doctors(): ...
        """
        def decorator(fn):
            @wraps(fn)
            def wrapper(*args, **kwargs):
                key = key_fn(*args, **kwargs) if callable(key_fn) else key_fn
                hit = self.get(key)
                if hit is not None:
                    return hit
                result = fn(*args, **kwargs)
                self.set(key, result, ttl)
                return result
            return wrapper
        return decorator


cache = RedisCache()
