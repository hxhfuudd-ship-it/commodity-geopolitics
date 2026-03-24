from datetime import date, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.commodity import Commodity
from app.models.price import PriceDaily
from app.models.geopolitical_event import GeopoliticalEvent


async def get_backtest_events(db: AsyncSession) -> list[dict]:
    result = await db.execute(
        select(GeopoliticalEvent).order_by(GeopoliticalEvent.start_date.desc())
    )
    events = result.scalars().all()
    return [
        {
            "id": e.id,
            "title": e.title,
            "event_type": e.event_type,
            "start_date": e.start_date.isoformat(),
            "severity": e.severity,
        }
        for e in events
    ]


async def run_backtest(
    db: AsyncSession,
    event_id: int,
    commodities: list[str],
    before_days: int = 30,
    after_days: int = 30,
) -> dict:
    event_result = await db.execute(
        select(GeopoliticalEvent).where(GeopoliticalEvent.id == event_id)
    )
    event = event_result.scalar_one_or_none()
    if not event:
        return {"error": "事件不存在"}

    event_date = event.start_date
    start = event_date - timedelta(days=before_days)
    end = event_date + timedelta(days=after_days)

    event_dict = {
        "id": event.id,
        "title": event.title,
        "description": event.description or "",
        "event_type": event.event_type,
        "region": event.region,
        "country_codes": event.country_codes or "",
        "start_date": event.start_date.isoformat(),
        "end_date": event.end_date.isoformat() if event.end_date else None,
        "severity": event.severity,
        "latitude": float(event.latitude) if event.latitude else 0,
        "longitude": float(event.longitude) if event.longitude else 0,
    }

    data = {}
    for symbol in commodities:
        commodity_result = await db.execute(
            select(Commodity).where(Commodity.symbol == symbol)
        )
        commodity = commodity_result.scalar_one_or_none()
        if not commodity:
            continue

        price_result = await db.execute(
            select(PriceDaily)
            .where(
                PriceDaily.commodity_id == commodity.id,
                PriceDaily.trade_date >= start,
                PriceDaily.trade_date <= end,
            )
            .order_by(PriceDaily.trade_date.asc())
        )
        prices = price_result.scalars().all()
        if not prices:
            continue

        dates = [p.trade_date.isoformat() for p in prices]
        close_prices = [float(p.close) if p.close else None for p in prices]

        # Normalize: base = last close on or before event date
        base_price = None
        for p in prices:
            if p.trade_date <= event_date and p.close:
                base_price = float(p.close)
        if base_price and base_price > 0:
            normalized = [(c / base_price * 100) if c else None for c in close_prices]
        else:
            normalized = close_prices

        data[symbol] = {
            "dates": dates,
            "prices": normalized,
            "raw_prices": close_prices,
            "base_price": base_price,
        }

    return {"event": event_dict, "data": data}


async def compare_events(
    db: AsyncSession,
    event_ids: list[int],
    commodity: str = "AU",
    before_days: int = 30,
    after_days: int = 30,
) -> dict:
    events = []
    for eid in event_ids:
        bt = await run_backtest(db, eid, [commodity], before_days, after_days)
        if commodity in bt.get("data", {}):
            events.append({
                "event": bt["event"],
                "dates": bt["data"][commodity]["dates"],
                "prices": bt["data"][commodity]["prices"],
            })
    return {"commodity": commodity, "events": events}
