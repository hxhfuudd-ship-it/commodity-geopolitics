import asyncio
import pandas as pd
from datetime import date, datetime
from decimal import Decimal
from loguru import logger
from sqlalchemy import select

from app.database import async_session
from app.models.commodity import Commodity
from app.models.price import PriceDaily
from app.data_sources.akshare_client import fetch_commodity_daily, fetch_realtime_price, _EASTMONEY_NAME_MAP
from app.core.cache import cache_set
from app.core.lock import acquire_lock, release_lock


def _is_trading_day() -> bool:
    """简单判断：周一到周五为交易日（不含节假日）"""
    return date.today().weekday() < 5


async def _supplement_today_from_eastmoney(db, commodity):
    """如果新浪日线没有今天数据，尝试用东方财富实时接口补充"""
    today = date.today()
    if not _is_trading_day():
        return

    # 检查 DB 是否已有今天数据
    existing = (await db.execute(
        select(PriceDaily).where(
            PriceDaily.commodity_id == commodity.id,
            PriceDaily.trade_date == today,
        )
    )).scalar_one_or_none()
    if existing:
        return  # 已有今天数据，跳过

    # 尝试东方财富实时接口
    em_name = _EASTMONEY_NAME_MAP.get(commodity.akshare_symbol)
    if not em_name:
        return

    try:
        import akshare as ak

        def _fetch():
            try:
                df = ak.futures_zh_realtime(symbol=em_name)
                if df is None or df.empty:
                    return None
                match = df[df["symbol"] == commodity.akshare_symbol]
                if match.empty:
                    match = df.head(1)
                row = match.iloc[0]
                trade_date_str = str(row.get("tradedate", ""))
                if trade_date_str and trade_date_str != str(today):
                    return None  # 不是今天的数据
                return row
            except Exception:
                return None

        row = await asyncio.get_event_loop().run_in_executor(None, _fetch)
        if row is None:
            return

        price = float(row.get("trade", 0))
        if price <= 0:
            return

        settle_val = float(row.get("settlement", 0)) if row.get("settlement") else 0

        # 获取昨日收盘价计算涨跌幅
        prev = (await db.execute(
            select(PriceDaily).where(PriceDaily.commodity_id == commodity.id)
            .order_by(PriceDaily.trade_date.desc()).limit(1)
        )).scalar_one_or_none()
        prev_close = float(prev.close) if prev and prev.close else 0
        change_pct = ((price - prev_close) / prev_close * 100) if prev_close > 0 else 0.0

        db.add(PriceDaily(
            commodity_id=commodity.id,
            trade_date=today,
            open=Decimal(str(row.get("open", price))),
            high=Decimal(str(row.get("high", price))),
            low=Decimal(str(row.get("low", price))),
            close=Decimal(str(price)),
            settle=Decimal(str(settle_val)) if settle_val > 0 else None,
            volume=int(float(row.get("volume", 0))) if row.get("volume") else None,
            open_interest=int(float(row.get("position", 0))) if row.get("position") else None,
            change_pct=Decimal(str(round(change_pct, 4))),
        ))
        await db.commit()
        logger.info(f"东方财富补充今日数据: {commodity.symbol} close={price} chg={change_pct:.2f}%")
    except Exception as e:
        logger.debug(f"东方财富补充 {commodity.symbol} 失败: {e}")


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
                    has_today = False

                    if daily_data is not None and not daily_data.empty:
                        for _, row in daily_data.iterrows():
                            result_row = await db.execute(
                                select(PriceDaily).where(
                                    PriceDaily.commodity_id == commodity.id,
                                    PriceDaily.trade_date == row.get("date"),
                                )
                            )
                            existing_price = result_row.scalar_one_or_none()
                            if existing_price:
                                # Update settle if missing
                                if not existing_price.settle and pd.notna(row.get("settle")):
                                    existing_price.settle = row.get("settle")
                                if row.get("date") == date.today():
                                    has_today = True
                                continue

                            price = PriceDaily(
                                commodity_id=commodity.id,
                                trade_date=row.get("date"),
                                open=row.get("open"),
                                high=row.get("high"),
                                low=row.get("low"),
                                close=row.get("close"),
                                settle=row.get("settle") if pd.notna(row.get("settle")) else None,
                                volume=row.get("volume"),
                                open_interest=row.get("open_interest"),
                                change_pct=row.get("change_pct") if pd.notna(row.get("change_pct")) else None,
                            )
                            db.add(price)
                            if row.get("date") == date.today():
                                has_today = True

                        await db.commit()

                        # 更新 Redis 缓存
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

                    # 如果新浪没有今日数据，用东方财富补充
                    if not has_today and _is_trading_day():
                        await _supplement_today_from_eastmoney(db, commodity)

                    logger.info(f"行情更新完成: {commodity.symbol}")

                except Exception as e:
                    logger.warning(f"品种 {commodity.symbol} 行情拉取失败: {e}")
                    continue

    except Exception as e:
        logger.error(f"行情拉取任务异常: {e}")
    finally:
        await release_lock(lock_name)
