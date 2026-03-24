import uuid
from loguru import logger
from app.core.cache import get_redis


async def acquire_lock(name: str, timeout: int = 10) -> bool:
    try:
        r = get_redis()
        lock_key = f"lock:task:{name}"
        token = str(uuid.uuid4())
        acquired = await r.set(lock_key, token, nx=True, ex=timeout)
        if acquired:
            logger.debug(f"获取锁成功: {name}")
            return True
        logger.debug(f"获取锁失败(已被占用): {name}")
        return False
    except Exception as e:
        logger.warning(f"获取锁异常: {name}, {e}，放行任务")
        return True


async def release_lock(name: str):
    try:
        r = get_redis()
        lock_key = f"lock:task:{name}"
        await r.delete(lock_key)
        logger.debug(f"释放锁: {name}")
    except Exception as e:
        logger.warning(f"释放锁异常: {name}, {e}")
