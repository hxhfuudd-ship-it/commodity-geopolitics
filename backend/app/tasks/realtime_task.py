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


async def _refresh_loop():
    """Background loop: fetch all realtime prices sequentially every 5 seconds.
    Sequential to avoid mini_racer (V8) thread-safety crash."""
    await _load_commodity_configs()
    logger.info(f"实时行情后台任务启动，共 {len(_commodity_configs)} 个品种（顺序获取）")

    while True:
        try:
            items = []
            for cfg in _commodity_configs:
                try:
                    result = await _fetch_one(cfg)
                    if isinstance(result, dict):
                        items.append(result)
                except Exception as e:
                    logger.debug(f"单品种获取异常 {cfg['symbol']}: {e}")

            if items:
                await cache_set("market:overview:realtime", items, ttl=30)

        except Exception as e:
            logger.warning(f"实时行情刷新异常: {e}")

        await asyncio.sleep(5)


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
