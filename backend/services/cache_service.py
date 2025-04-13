import logging
from typing import List, Dict, Any, Optional
import json
import asyncio
import pickle
from datetime import datetime, timedelta

import redis
from redis.asyncio import Redis

from config import settings

logger = logging.getLogger("retrieval")

class CacheService:
    def __init__(self):
        # 连接到Redis
        try:
            self.redis = Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=False  # 不自动解码，因为我们存储的是序列化对象
            )
            logger.info(f"Connected to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}", exc_info=True)
            self.redis = None
    
    async def get(self, key: str) -> Optional[Any]:
        """从缓存获取值"""
        try:
            if not self.redis or not settings.REDIS_CACHE_EXPIRE:
                return None
                
            # 获取缓存值
            cached_data = await self.redis.get(key)
            if not cached_data:
                return None
                
            # 反序列化
            try:
                return pickle.loads(cached_data)
            except Exception as e:
                logger.error(f"Cache deserialization error: {str(e)}", exc_info=True)
                return None
                
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}", exc_info=True)
            return None
    
    async def set(self, key: str, value: Any, expire: int = None) -> bool:
        """设置缓存值"""
        try:
            if not self.redis or not settings.REDIS_CACHE_EXPIRE:
                return False
                
            # 序列化值
            try:
                serialized_data = pickle.dumps(value)
            except Exception as e:
                logger.error(f"Cache serialization error: {str(e)}", exc_info=True)
                return False
                
            # 设置缓存
            if expire is None:
                expire = settings.REDIS_CACHE_EXPIRE
                
            await self.redis.set(key, serialized_data, ex=expire)
            return True
                
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}", exc_info=True)
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        try:
            if not self.redis:
                return False
                
            await self.redis.delete(key)
            return True
                
        except Exception as e:
            logger.error(f"Cache delete error: {str(e)}", exc_info=True)
            return False
    
    async def clear_all(self) -> bool:
        """清空所有缓存"""
        try:
            if not self.redis:
                return False
                
            await self.redis.flushdb()
            return True
                
        except Exception as e:
            logger.error(f"Cache clear error: {str(e)}", exc_info=True)
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            if not self.redis:
                return {"connected": False}
                
            # 获取Redis信息
            info = await self.redis.info()
            
            # 计算缓存命中率
            hits = info.get("keyspace_hits", 0)
            misses = info.get("keyspace_misses", 0)
            hit_rate = hits / (hits + misses) if (hits + misses) > 0 else 0
            
            return {
                "connected": True,
                "total_keys": await self.redis.dbsize(),
                "hit_rate": hit_rate,
                "memory_used": info.get("used_memory_human", "unknown"),
                "uptime": info.get("uptime_in_seconds", 0)
            }
                
        except Exception as e:
            logger.error(f"Cache stats error: {str(e)}", exc_info=True)
            return {"connected": False, "error": str(e)}
    
    async def close(self):
        """关闭Redis连接"""
        if self.redis:
            await self.redis.close()