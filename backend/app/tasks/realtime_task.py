import asyncio
import json
from datetime import datetime
from loguru import logger

from app.core.cache import cache_set, cache_get, get_redis
from app.data_sources.akshare_client import fetch_realtime_price
from app.database import async_session
from app.models.commodity import Commodity
from app.models.price import PriceDaily
from sqlalchemy import select

# All commodity configs for realtime fetching
_commodity_configs: list[dict] = []
_task: asyncio.Task | None = None


async def _load_commodity_configs():
    """Load commodity list from DB once"""
    global _commodity_configs
    if _commodity_configs:
        return
    async with async_session() as db:
        result = await db.execute(select(Commodity))
        commodities = result.scalars().all()
        _commodity_configs = [
            {"symbol": c.symbol, "name_cn": c.name_cn, "category": c.category, "akshare_symbol": c.akshare_symbol}
            for c in commodities
        ]


async def _fetch_one(cfg: dict) -> dict:
    """Fetch realtime price for one commodity, fallback to DB daily close"""
    try:
        rt = await fetch_realtime_price(cfg["akshare_symbol"])
        if rt and rt.get("price"):
            return {
                "symbol": cfg["symbol"],
                "name_cn": cfg["name_cn"],
                "category": cfg["category"],
                "latest_price": rt["price"],
                "change_pct": rt.get("change_pct"),
                "open": rt.get("open"),
                "settle": rt.get("settle"),
                "prev_close": rt.get("prev_close"),
                "volume": rt.get("volume"),
                "open_interest": rt.get("open_interest"),
                "updated_at": rt.get("updated_at", datetime.now().isoformat()),
            }
    except Exception as e:
        logger.debug(f"实时价格失败 {cfg['symbol']}: {e}")

    # Fallback: read latest daily close from DB
    try:
        async with async_session() as db:
            from app.models.commodity import Commodity
            c = (await db.execute(
                select(Commodity).where(Commodity.symbol == cfg["symbol"])
            )).scalar_one_or_none()
            if c:
                p = (await db.execute(
                    select(PriceDaily).where(PriceDaily.commodity_id == c.id)
                    .order_by(PriceDaily.trade_date.desc()).limit(1)
                )).scalar_one_or_none()
                if p:
                    return {
                        "symbol": cfg["symbol"],
                        "name_cn": cfg["name_cn"],
                        "category": cfg["category"],
                        "latest_price": float(p.close) if p.close else None,
                        "change_pct": float(p.change_pct) if p.change_pct else None,
                        "open": float(p.open) if p.open else None,
                        "settle": None,
                        "prev_close": None,
                        "volume": int(p.volume) if p.volume else None,
                        "open_interest": int(p.open_interest) if p.open_interest else None,
                        "updated_at": str(p.trade_date),
                    }
    except Exception as e:
        logger.debug(f"DB fallback 失败 {cfg['symbol']}: {e}")

    return {
        "symbol": cfg["symbol"],
        "name_cn": cfg["name_cn"],
        "category": cfg["category"],
        "latest_price": None,
        "change_pct": None,
        "open": None,
        "settle": None,
        "prev_close": None,
        "volume": None,
        "open_interest": None,
        "updated_at": None,
    }


async def _fetch_all_from_db() -> list[dict]:
    """Fast path: load all latest prices from DB without hitting akshare"""
    items = []
    try:
        async with async_session() as db:
            for cfg in _commodity_configs:
                try:
                    c = (await db.execute(
                        select(Commodity).where(Commodity.symbol == cfg["symbol"])
                    )).scalar_one_or_none()
                    if c:
                        p = (await db.execute(
                            select(PriceDaily).where(PriceDaily.commodity_id == c.id)
                            .order_by(PriceDaily.trade_date.desc()).limit(1)
                        )).scalar_one_or_none()
                        if p:
                            items.append({
                                "symbol": cfg["symbol"],
                                "name_cn": cfg["name_cn"],
                                "category": cfg["category"],
                                "latest_price": float(p.close) if p.close else None,
                                "change_pct": float(p.change_pct) if p.change_pct else None,
                                "open": float(p.open) if p.open else None,
                                "settle": None,
                                "prev_close": None,
                                "volume": int(p.volume) if p.volume else None,
                                "open_interest": int(p.open_interest) if p.open_interest else None,
                                "updated_at": str(p.trade_date),
                            })
                            continue
                except Exception:
                    pass
                items.append({
                    "symbol": cfg["symbol"], "name_cn": cfg["name_cn"],
                    "category": cfg["category"], "latest_price": None,
                    "change_pct": None, "open": None, "settle": None,
                    "prev_close": None, "volume": None, "open_interest": None,
                    "updated_at": None,
                })
    except Exception as e:
        logger.warning(f"DB批量加载失败: {e}")
    return items


async def _refresh_loop():
    """Background loop: fetch all realtime prices sequentially.
    Sequential to avoid mini_racer (V8) thread-safety crash.
    Backs off to 60s when all akshare fetches fail (non-trading hours)."""
    await _load_commodity_configs()
    logger.info(f"实时行情后台任务启动，共 {len(_commodity_configs)} 个品种（顺序获取）")

    # First cycle: load from DB immediately so API has data right away
    db_items = await _fetch_all_from_db()
    if db_items:
        await cache_set("market:overview:realtime", db_items, ttl=120)
        logger.info(f"已从数据库加载 {len(db_items)} 个品种的历史价格到缓存")

    consecutive_failures = 0

    while True:
        try:
            items = []
            realtime_success = 0
            for cfg in _commodity_configs:
                try:
                    # Add timeout to prevent blocking too long
                    result = await asyncio.wait_for(_fetch_one(cfg), timeout=8)
                    if isinstance(result, dict):
                        items.append(result)
                        if result.get("updated_at") and "T" in str(result.get("updated_at", "")):
                            realtime_success += 1
                except asyncio.TimeoutError:
                    logger.debug(f"获取超时 {cfg['symbol']}")
                except Exception as e:
                    logger.debug(f"单品种获取异常 {cfg['symbol']}: {e}")

            if items:
                await cache_set("market:overview:realtime", items, ttl=120)

            # Back off if no realtime data (non-trading hours)
            if realtime_success == 0:
                consecutive_failures += 1
            else:
                consecutive_failures = 0

        except Exception as e:
            logger.warning(f"实时行情刷新异常: {e}")
            consecutive_failures += 1

        # Exponential backoff: 5s -> 30s -> 60s
        if consecutive_failures >= 3:
            sleep_time = 60
        elif consecutive_failures >= 1:
            sleep_time = 30
        else:
            sleep_time = 5
        await asyncio.sleep(sleep_time)


def start_realtime_task():
    """Start the background realtime refresh task"""
    global _task
    if _task is None or _task.done():
        _task = asyncio.create_task(_refresh_loop())
        logger.info("实时行情后台任务已创建")


def stop_realtime_task():
    """Stop the background task"""
    global _task
    if _task and not _task.done():
        _task.cancel()
        _task = None
        logger.info("实时行情后台任务已停止")
