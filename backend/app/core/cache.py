import json
from typing import Optional, Any
import redis.asyncio as aioredis
from loguru import logger
from app.config import settings

_redis_client: Optional[aioredis.Redis] = None


async def init_redis() -> aioredis.Redis:
    global _redis_client
    _redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    await _redis_client.ping()
    logger.info("Redis 连接成功")
    return _redis_client


async def close_redis():
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis 连接已关闭")


def get_redis() -> aioredis.Redis:
    if _redis_client is None:
        raise RuntimeError("Redis 未初始化")
    return _redis_client


async def cache_get(key: str) -> Optional[Any]:
    try:
        r = get_redis()
        value = await r.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        logger.warning(f"缓存读取失败 key={key}: {e}")
        return None


async def cache_set(key: str, value: Any, ttl: int = 300):
    try:
        r = get_redis()
        await r.set(key, json.dumps(value, default=str), ex=ttl)
    except Exception as e:
        logger.warning(f"缓存写入失败 key={key}: {e}")


async def cache_delete(key: str):
    try:
        r = get_redis()
        await r.delete(key)
    except Exception as e:
        logger.warning(f"缓存删除失败 key={key}: {e}")
