from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.commodity import Commodity
from app.models.price import PriceDaily
from app.models.analysis import CftcPosition
from app.schemas.market import CommodityOut, PriceDailyOut, MarketOverviewItem
from app.core.cache import cache_get, cache_set

INIT_COMMODITIES = [
    # 金属
    {"symbol": "AU", "name_cn": "黄金", "category": "metal", "exchange": "SHFE", "unit": "元/克", "akshare_symbol": "AU0"},
    {"symbol": "AG", "name_cn": "白银", "category": "metal", "exchange": "SHFE", "unit": "元/千克", "akshare_symbol": "AG0"},
    {"symbol": "CU", "name_cn": "铜", "category": "metal", "exchange": "SHFE", "unit": "元/吨", "akshare_symbol": "CU0"},
    {"symbol": "AL", "name_cn": "铝", "category": "metal", "exchange": "SHFE", "unit": "元/吨", "akshare_symbol": "AL0"},
    {"symbol": "NI", "name_cn": "镍", "category": "metal", "exchange": "SHFE", "unit": "元/吨", "akshare_symbol": "NI0"},
    {"symbol": "FE", "name_cn": "铁矿石", "category": "metal", "exchange": "DCE", "unit": "元/吨", "akshare_symbol": "I0"},
    # 能源
    {"symbol": "SC", "name_cn": "上海原油", "category": "energy", "exchange": "INE", "unit": "元/桶", "akshare_symbol": "SC0"},
    {"symbol": "FU", "name_cn": "燃料油", "category": "energy", "exchange": "SHFE", "unit": "元/吨", "akshare_symbol": "FU0"},
    {"symbol": "PG", "name_cn": "LPG液化气", "category": "energy", "exchange": "DCE", "unit": "元/吨", "akshare_symbol": "PG0"},
    # 农产品
    {"symbol": "A", "name_cn": "大豆", "category": "agriculture", "exchange": "DCE", "unit": "元/吨", "akshare_symbol": "A0"},
    {"symbol": "M", "name_cn": "豆粕", "category": "agriculture", "exchange": "DCE", "unit": "元/吨", "akshare_symbol": "M0"},
    {"symbol": "Y", "name_cn": "豆油", "category": "agriculture", "exchange": "DCE", "unit": "元/吨", "akshare_symbol": "Y0"},
    {"symbol": "P", "name_cn": "棕榈油", "category": "agriculture", "exchange": "DCE", "unit": "元/吨", "akshare_symbol": "P0"},
    {"symbol": "C", "name_cn": "玉米", "category": "agriculture", "exchange": "DCE", "unit": "元/吨", "akshare_symbol": "C0"},
    {"symbol": "CF", "name_cn": "棉花", "category": "agriculture", "exchange": "ZCE", "unit": "元/吨", "akshare_symbol": "CF0"},
    {"symbol": "SR", "name_cn": "白糖", "category": "agriculture", "exchange": "ZCE", "unit": "元/吨", "akshare_symbol": "SR0"},
    {"symbol": "RU", "name_cn": "橡胶", "category": "agriculture", "exchange": "SHFE", "unit": "元/吨", "akshare_symbol": "RU0"},
    # 化工
    {"symbol": "TA", "name_cn": "PTA", "category": "chemical", "exchange": "ZCE", "unit": "元/吨", "akshare_symbol": "TA0"},
    {"symbol": "MA", "name_cn": "甲醇", "category": "chemical", "exchange": "ZCE", "unit": "元/吨", "akshare_symbol": "MA0"},
    {"symbol": "PP", "name_cn": "聚丙烯", "category": "chemical", "exchange": "DCE", "unit": "元/吨", "akshare_symbol": "PP0"},
]


async def init_commodities(db: AsyncSession):
    result = await db.execute(select(func.count()).select_from(Commodity))
    count = result.scalar()
    if count and count > 0:
        logger.info(f"品种数据已存在 ({count} 条)，跳过初始化")
        return

    for item in INIT_COMMODITIES:
        commodity = Commodity(**item)
        db.add(commodity)
    await db.commit()
    logger.info(f"品种数据初始化完成，共 {len(INIT_COMMODITIES)} 个品种")


async def get_commodities(db: AsyncSession, category: Optional[str] = None) -> list[CommodityOut]:
    query = select(Commodity)
    if category:
        query = query.where(Commodity.category == category)
    result = await db.execute(query)
    rows = result.scalars().all()
    return [CommodityOut.model_validate(r) for r in rows]


async def get_commodity_price(db: AsyncSession, symbol: str) -> dict:
    cache_key = f"market:realtime:{symbol}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    result = await db.execute(
        select(Commodity).where(Commodity.symbol == symbol)
    )
    commodity = result.scalar_one_or_none()
    if not commodity:
        return {}

    price_result = await db.execute(
        select(PriceDaily)
        .where(PriceDaily.commodity_id == commodity.id)
        .order_by(PriceDaily.trade_date.desc())
        .limit(1)
    )
    price = price_result.scalar_one_or_none()
    if not price:
        return {"symbol": symbol, "name_cn": commodity.name_cn, "price": None}

    data = {
        "symbol": symbol,
        "name_cn": commodity.name_cn,
        "price": float(price.close) if price.close else None,
        "change_pct": float(price.change_pct) if price.change_pct else None,
        "trade_date": price.trade_date.isoformat(),
        "open": float(price.open) if price.open else None,
        "high": float(price.high) if price.high else None,
        "low": float(price.low) if price.low else None,
        "volume": price.volume,
    }
    await cache_set(cache_key, data, ttl=300)
    return data


async def get_kline(
    db: AsyncSession, symbol: str, period: str = "day",
    start_date: Optional[date] = None, end_date: Optional[date] = None
) -> list[PriceDailyOut]:
    result = await db.execute(
        select(Commodity).where(Commodity.symbol == symbol)
    )
    commodity = result.scalar_one_or_none()
    if not commodity:
        return []

    query = select(PriceDaily).where(PriceDaily.commodity_id == commodity.id)
    if start_date:
        query = query.where(PriceDaily.trade_date >= start_date)
    if end_date:
        query = query.where(PriceDaily.trade_date <= end_date)
    query = query.order_by(PriceDaily.trade_date.asc())

    result = await db.execute(query)
    rows = result.scalars().all()
    return [PriceDailyOut.model_validate(r) for r in rows]


async def get_compare_data(db: AsyncSession, symbols: list[str], normalize: bool = True) -> dict:
    data = {}
    for symbol in symbols:
        kline = await get_kline(db, symbol)
        if not kline:
            continue
        prices = [float(k.close) for k in kline if k.close]
        dates = [k.trade_date.isoformat() for k in kline if k.close]
        if normalize and prices:
            base = prices[0]
            prices = [p / base * 100 for p in prices] if base else prices
        data[symbol] = {"dates": dates, "prices": prices}
    return data


async def get_overview(db: AsyncSession) -> list[MarketOverviewItem]:
    """Get market overview. Uses DB data directly (no akshare calls) to avoid blocking.
    Realtime prices are handled by the background task and cached separately."""
    cache_key = "market:overview"
    cached = await cache_get(cache_key)
    if cached:
        return [MarketOverviewItem(**item) for item in cached]

    commodities = await db.execute(select(Commodity))
    items = []
    for c in commodities.scalars().all():
        # Use latest daily close from DB (fast, no external calls)
        price_result = await db.execute(
            select(PriceDaily)
            .where(PriceDaily.commodity_id == c.id)
            .order_by(PriceDaily.trade_date.desc())
            .limit(1)
        )
        price = price_result.scalar_one_or_none()
        item = MarketOverviewItem(
            symbol=c.symbol,
            name_cn=c.name_cn,
            category=c.category,
            latest_price=price.close if price else None,
            change_pct=price.change_pct if price else None,
            open=price.open if price else None,
            volume=price.volume if price else None,
            open_interest=price.open_interest if price else None,
            updated_at=datetime.combine(price.trade_date, datetime.min.time()) if price else None,
        )
        items.append(item)

    await cache_set(cache_key, [item.model_dump() for item in items], ttl=60)
    return items


async def get_cftc(db: AsyncSession, symbol: str) -> list[dict]:
    result = await db.execute(
        select(Commodity).where(Commodity.symbol == symbol)
    )
    commodity = result.scalar_one_or_none()
    if not commodity:
        return []

    result = await db.execute(
        select(CftcPosition)
        .where(CftcPosition.commodity_id == commodity.id)
        .order_by(CftcPosition.report_date.desc())
        .limit(52)
    )
    rows = result.scalars().all()
    return [
        {
            "report_date": r.report_date.isoformat(),
            "long_positions": r.long_positions,
            "short_positions": r.short_positions,
            "net_positions": r.net_positions,
        }
        for r in reversed(rows)
    ]
