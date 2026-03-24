import asyncio
import pandas as pd
from loguru import logger
from sqlalchemy import select

from app.database import async_session
from app.models.commodity import Commodity
from app.models.price import PriceDaily
from app.data_sources.akshare_client import fetch_commodity_daily, fetch_realtime_price
from app.core.cache import cache_set
from app.core.lock import acquire_lock, release_lock


async def fetch_market_data():
    lock_name = "lock:task:fetch_market_data"
    if not await acquire_lock(lock_name, timeout=280):
        logger.debug("行情拉取任务已被其他实例锁定，跳过")
        return

    try:
        async with async_session() as db:
            result = await db.execute(select(Commodity))
            commodities = result.scalars().all()

            for commodity in commodities:
                try:
                    daily_data = await fetch_commodity_daily(commodity.akshare_symbol)
                    if daily_data is None or daily_data.empty:
                        continue

                    for _, row in daily_data.iterrows():
                        existing = await db.execute(
                            select(PriceDaily).where(
                                PriceDaily.commodity_id == commodity.id,
                                PriceDaily.trade_date == row.get("date"),
                            )
                        )
                        if existing.scalar_one_or_none():
                            continue

                        price = PriceDaily(
                            commodity_id=commodity.id,
                            trade_date=row.get("date"),
                            open=row.get("open"),
                            high=row.get("high"),
                            low=row.get("low"),
                            close=row.get("close"),
                            volume=row.get("volume"),
                            open_interest=row.get("open_interest"),
                            change_pct=row.get("change_pct") if pd.notna(row.get("change_pct")) else None,
                        )
                        db.add(price)

                    await db.commit()

                    # 更新 Redis 缓存
                    if not daily_data.empty:
                        latest = daily_data.iloc[-1]
                        cache_data = {
                            "symbol": commodity.symbol,
                            "name_cn": commodity.name_cn,
                            "price": float(latest.get("close", 0)),
                            "change_pct": float(latest.get("change_pct", 0)),
                            "trade_date": str(latest.get("date", "")),
                            "open": float(latest.get("open", 0)) if pd.notna(latest.get("open")) else None,
                            "high": float(latest.get("high", 0)) if pd.notna(latest.get("high")) else None,
                            "low": float(latest.get("low", 0)) if pd.notna(latest.get("low")) else None,
                            "volume": int(latest.get("volume", 0)) if pd.notna(latest.get("volume")) else None,
                        }
                        await cache_set(f"market:realtime:{commodity.symbol}", cache_data, ttl=300)

                    logger.info(f"行情更新完成: {commodity.symbol}")

                except Exception as e:
                    logger.warning(f"品种 {commodity.symbol} 行情拉取失败: {e}")
                    continue

    except Exception as e:
        logger.error(f"行情拉取任务异常: {e}")
    finally:
        await release_lock(lock_name)
