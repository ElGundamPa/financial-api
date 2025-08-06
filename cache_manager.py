import json
import redis
from datetime import datetime, timedelta
from typing import Any, Optional, Dict
from config import REDIS_URL, CACHE_TTL
from logger import logger

class CacheManager:
    def __init__(self):
        try:
            self.redis_client = redis.from_url(REDIS_URL)
            self.redis_client.ping()  # Test connection
            logger.info("✅ Redis cache conectado")
        except Exception as e:
            logger.warning(f"⚠️ Redis no disponible, usando cache en memoria: {e}")
            self.redis_client = None
            self.memory_cache = {}

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get data from cache"""
        try:
            if self.redis_client:
                data = self.redis_client.get(key)
                if data:
                    return json.loads(data)
            else:
                # Fallback to memory cache
                if key in self.memory_cache:
                    data, expires_at = self.memory_cache[key]
                    if datetime.now() < expires_at:
                        return data
                    else:
                        del self.memory_cache[key]
        except Exception as e:
            logger.error(f"❌ Error getting from cache: {e}")
        return None

    def set(self, key: str, value: Dict[str, Any], ttl: int = None) -> bool:
        """Set data in cache"""
        try:
            ttl = ttl or CACHE_TTL
            if self.redis_client:
                self.redis_client.setex(key, ttl, json.dumps(value))
            else:
                # Fallback to memory cache
                expires_at = datetime.now() + timedelta(seconds=ttl)
                self.memory_cache[key] = (value, expires_at)
            return True
        except Exception as e:
            logger.error(f"❌ Error setting cache: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete data from cache"""
        try:
            if self.redis_client:
                self.redis_client.delete(key)
            else:
                self.memory_cache.pop(key, None)
            return True
        except Exception as e:
            logger.error(f"❌ Error deleting from cache: {e}")
            return False

    def clear(self) -> bool:
        """Clear all cache"""
        try:
            if self.redis_client:
                self.redis_client.flushdb()
            else:
                self.memory_cache.clear()
            return True
        except Exception as e:
            logger.error(f"❌ Error clearing cache: {e}")
            return False

# Global cache instance
cache_manager = CacheManager()
