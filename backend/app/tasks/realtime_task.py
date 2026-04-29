import asyncio
import json
from datetime import datetime, date, timedelta
from decimal import Decimal
from loguru import logger

from app.core.cache import cache_set, cache_get, get_redis
from app.data_sources.akshare_client import fetch_realtime_price, fetch_realtime_all_push2
from app.database import async_session
from app.models.commodity import Commodity
from app.models.price import PriceDaily
from sqlalchemy import select

# All commodity configs for realtime fetching
_commodity_configs: list[dict] = []
_task: asyncio.Task | None = None
# Track whether we've saved today's close to DB
_today_saved: set[str] = set()
_today_date: date | None = None
# Track last successful realtime update for staleness detection
_last_realtime_success: datetime | None = None


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
            settle = rt.get("settle")
            # 实时接口通常不返回settle，回退查DB最近有settle的记录
            if not settle:
                try:
                    async with async_session() as db:
                        c = (await db.execute(
                            select(Commodity).where(Commodity.symbol == cfg["symbol"])
                        )).scalar_one_or_none()
                        if c:
                            prev_s = (await db.execute(
                                select(PriceDaily).where(
                                    PriceDaily.commodity_id == c.id,
                                    PriceDaily.settle.isnot(None),
                                ).order_by(PriceDaily.trade_date.desc()).limit(1)
                            )).scalar_one_or_none()
                            if prev_s:
                                settle = float(prev_s.settle)
                except Exception:
                    pass
            return {
                "symbol": cfg["symbol"],
                "name_cn": cfg["name_cn"],
                "category": cfg["category"],
                "latest_price": rt["price"],
                "change_pct": rt.get("change_pct"),
                "open": rt.get("open"),
                "settle": settle,
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
                    settle = float(p.settle) if p.settle else None
                    # 如果最新记录没有settle，回退取前一天的
                    if not settle:
                        prev = (await db.execute(
                            select(PriceDaily).where(
                                PriceDaily.commodity_id == c.id,
                                PriceDaily.settle.isnot(None),
                            ).order_by(PriceDaily.trade_date.desc()).limit(1)
                        )).scalar_one_or_none()
                        if prev:
                            settle = float(prev.settle)
                    return {
                        "symbol": cfg["symbol"],
                        "name_cn": cfg["name_cn"],
                        "category": cfg["category"],
                        "latest_price": float(p.close) if p.close else None,
                        "change_pct": float(p.change_pct) if p.change_pct else None,
                        "open": float(p.open) if p.open else None,
                        "settle": settle,
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
                            settle = float(p.settle) if p.settle else None
                            # 如果最新记录没有settle，回退取前一天的
                            if not settle:
                                prev_s = (await db.execute(
                                    select(PriceDaily).where(
                                        PriceDaily.commodity_id == c.id,
                                        PriceDaily.settle.isnot(None),
                                    ).order_by(PriceDaily.trade_date.desc()).limit(1)
                                )).scalar_one_or_none()
                                if prev_s:
                                    settle = float(prev_s.settle)
                            items.append({
                                "symbol": cfg["symbol"],
                                "name_cn": cfg["name_cn"],
                                "category": cfg["category"],
                                "latest_price": float(p.close) if p.close else None,
                                "change_pct": float(p.change_pct) if p.change_pct else None,
                                "open": float(p.open) if p.open else None,
                                "settle": settle,
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


async def _save_realtime_to_db(items: list[dict]):
    """将实时获取的价格写入 DB 作为当日日线数据，收盘后仍可展示今日价格"""
    global _today_saved, _today_date
    today = date.today()

    # 日期变了，重置记录
    if _today_date != today:
        _today_saved = set()
        _today_date = today

    # 筛选有实时数据且今天还没写入的品种
    to_save = [it for it in items
               if it.get("latest_price") and it["symbol"] not in _today_saved
               and it.get("updated_at") and "T" in str(it.get("updated_at", ""))]
    if not to_save:
        return

    try:
        async with async_session() as db:
            for it in to_save:
                sym = it["symbol"]
                c = (await db.execute(
                    select(Commodity).where(Commodity.symbol == sym)
                )).scalar_one_or_none()
                if not c:
                    continue

                # 查看今天是否已有记录
                existing = (await db.execute(
                    select(PriceDaily).where(
                        PriceDaily.commodity_id == c.id,
                        PriceDaily.trade_date == today,
                    )
                )).scalar_one_or_none()

                price = it["latest_price"]
                open_p = it.get("open")
                volume = it.get("volume")
                oi = it.get("open_interest")
                chg = it.get("change_pct")
                settle = it.get("settle")

                if existing:
                    # 更新今日记录（用最新价覆盖 close）
                    existing.close = Decimal(str(price))
                    if open_p:
                        existing.open = Decimal(str(open_p))
                    # high/low: 取极值
                    if existing.high is None or Decimal(str(price)) > existing.high:
                        existing.high = Decimal(str(price))
                    if existing.low is None or Decimal(str(price)) < existing.low:
                        existing.low = Decimal(str(price))
                    if volume:
                        existing.volume = volume
                    if oi:
                        existing.open_interest = oi
                    if chg is not None:
                        existing.change_pct = Decimal(str(chg))
                    if settle and settle > 0:
                        existing.settle = Decimal(str(settle))
                else:
                    # 新建今日记录
                    db.add(PriceDaily(
                        commodity_id=c.id,
                        trade_date=today,
                        open=Decimal(str(open_p)) if open_p else Decimal(str(price)),
                        high=Decimal(str(price)),
                        low=Decimal(str(price)),
                        close=Decimal(str(price)),
                        settle=Decimal(str(settle)) if settle and settle > 0 else None,
                        volume=volume,
                        open_interest=oi,
                        change_pct=Decimal(str(chg)) if chg is not None else None,
                    ))
                _today_saved.add(sym)

            await db.commit()
            logger.info(f"已将 {len(to_save)} 个品种的实时价格写入DB (日期: {today})")
    except Exception as e:
        logger.warning(f"实时价格写入DB失败: {e}")


async def _refresh_loop():
    """Background loop: batch-fetch all realtime prices via push2 API.
    One HTTP request for all 20 commodities, updates cache immediately.
    Falls back to individual fetch if push2 fails."""
    global _last_realtime_success

    await _load_commodity_configs()
    logger.info(f"实时行情后台任务启动，共 {len(_commodity_configs)} 个品种（push2 批量获取）")

    # First cycle: load from DB immediately so API has data right away
    db_items = await _fetch_all_from_db()
    if db_items:
        await cache_set("market:overview:realtime", db_items, ttl=7200)
        logger.info(f"已从数据库加载 {len(db_items)} 个品种的历史价格到缓存")

    consecutive_failures = 0

    # 维护一份完整的品种数据快照
    snapshot: dict[str, dict] = {}
    for item in db_items:
        snapshot[item["symbol"]] = item

    def _update_snapshot(sym: str, new_data: dict):
        """更新 snapshot，settle 和 open_interest 不允许被 None/0 覆盖"""
        old = snapshot.get(sym, {})
        if not new_data.get("settle"):
            new_data["settle"] = old.get("settle")
        if not new_data.get("open_interest"):
            new_data["open_interest"] = old.get("open_interest") or 0
        snapshot[sym] = new_data

    # 构建 akshare_symbol -> cfg 的映射
    cfg_map = {cfg["akshare_symbol"]: cfg for cfg in _commodity_configs}

    while True:
        try:
            realtime_success = 0

            # 优先用 push2 批量接口（一次请求拿所有品种）
            push2_data = await fetch_realtime_all_push2()

            if push2_data:
                for ak_sym, rt in push2_data.items():
                    cfg = cfg_map.get(ak_sym)
                    if not cfg:
                        continue
                    # push2 不返回结算价和持仓量，_update_snapshot 会保留旧值
                    _update_snapshot(cfg["symbol"], {
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
                    })
                    realtime_success += 1

                # 批量更新完立即写缓存
                await cache_set("market:overview:realtime", list(snapshot.values()), ttl=300)
            else:
                logger.warning("push2 批量获取返回空数据，回退到逐个获取")
                # push2 失败，回退到逐个获取
                for cfg in _commodity_configs:
                    try:
                        result = await asyncio.wait_for(_fetch_one(cfg), timeout=8)
                        if isinstance(result, dict):
                            _update_snapshot(cfg["symbol"], result)
                            if result.get("updated_at") and "T" in str(result.get("updated_at", "")):
                                realtime_success += 1
                    except asyncio.TimeoutError:
                        logger.debug(f"获取超时 {cfg['symbol']}")
                    except Exception as e:
                        logger.debug(f"单品种获取异常 {cfg['symbol']}: {e}")

            items = list(snapshot.values())
            if items and realtime_success > 0:
                await cache_set("market:overview:realtime", items, ttl=300)
                await _save_realtime_to_db(items)
                _last_realtime_success = datetime.now()
                consecutive_failures = 0
            elif items:
                existing_cache = await cache_get("market:overview:realtime")
                if not existing_cache:
                    await cache_set("market:overview:realtime", items, ttl=7200)
                consecutive_failures += 1
            else:
                consecutive_failures += 1

            # Staleness detection: if no realtime success for 10+ minutes, force DB refresh
            if consecutive_failures > 0 and consecutive_failures % 20 == 0:
                logger.warning(f"实时行情连续失败 {consecutive_failures} 次，强制从DB刷新缓存")
                db_items = await _fetch_all_from_db()
                if db_items:
                    for item in db_items:
                        _update_snapshot(item["symbol"], item)
                    await cache_set("market:overview:realtime", list(snapshot.values()), ttl=7200)

            if consecutive_failures > 0 and consecutive_failures % 5 == 0:
                logger.warning(f"实时行情连续失败 {consecutive_failures} 次，sleep_time 已增加")

        except Exception as e:
            logger.warning(f"实时行情刷新异常: {e}")
            consecutive_failures += 1

        # 交易时段 3s，非交易时段退避
        if consecutive_failures >= 3:
            sleep_time = 60
        elif consecutive_failures >= 1:
            sleep_time = 30
        else:
            sleep_time = 3
        await asyncio.sleep(sleep_time)


async def prefill_cache():
    """启动时预热缓存，确保用户打开页面立即有数据"""
    await _load_commodity_configs()
    db_items = await _fetch_all_from_db()
    if db_items:
        await cache_set("market:overview:realtime", db_items, ttl=7200)
        logger.info(f"预热缓存完成: {len(db_items)} 个品种")


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
