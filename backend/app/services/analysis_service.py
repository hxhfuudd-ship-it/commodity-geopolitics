from datetime import date, timedelta
from typing import Optional
import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.commodity import Commodity
from app.models.price import PriceDaily
from app.models.geopolitical_event import GeopoliticalEvent, EventImpact
from app.models.analysis import MacroIndicator
from app.schemas.analysis import CorrelationMatrixOut, EventImpactOut, MacroComparisonOut, RatioItem
from app.schemas.news import EventOut
from app.schemas.market import CommodityOut
from app.core.llm import generate_report
from app.services.market_service import get_overview
from app.services.news_service import get_articles
from app.schemas.news import NewsListQuery


PERIOD_MAP = {"30d": 30, "90d": 90, "180d": 180, "1y": 365}


async def get_correlation(db: AsyncSession, symbols: list[str], period: str = "90d") -> CorrelationMatrixOut:
    days = PERIOD_MAP.get(period, 90)
    start = date.today() - timedelta(days=days)

    price_data = {}
    for symbol in symbols:
        result = await db.execute(
            select(Commodity).where(Commodity.symbol == symbol)
        )
        commodity = result.scalar_one_or_none()
        if not commodity:
            continue

        result = await db.execute(
            select(PriceDaily.trade_date, PriceDaily.close)
            .where(PriceDaily.commodity_id == commodity.id, PriceDaily.trade_date >= start)
            .order_by(PriceDaily.trade_date.asc())
        )
        rows = result.all()
        price_data[symbol] = {r.trade_date: float(r.close) for r in rows if r.close}

    if len(price_data) < 2:
        return CorrelationMatrixOut(symbols=symbols, matrix=[[1.0] * len(symbols)] * len(symbols))

    # Find common dates across all symbols to keep alignment
    common_dates = sorted(set.intersection(*[set(d.keys()) for d in price_data.values()]))
    if len(common_dates) < 10:
        # Fallback: use pairwise common dates
        all_dates = sorted(set().union(*[set(d.keys()) for d in price_data.values()]))
        common_dates = all_dates

    valid_symbols = []
    matrix_data = []
    for symbol in symbols:
        if symbol not in price_data:
            continue
        prices = [price_data[symbol].get(d) for d in common_dates]
        # Forward-fill None gaps
        filled = []
        last = None
        for p in prices:
            if p is not None:
                last = p
            if last is not None:
                filled.append(last)
        if len(filled) > 10:
            valid_symbols.append(symbol)
            matrix_data.append(filled)

    if len(valid_symbols) < 2:
        return CorrelationMatrixOut(symbols=symbols, matrix=[[1.0] * len(symbols)] * len(symbols))

    min_len = min(len(p) for p in matrix_data)
    matrix_data = [p[:min_len] for p in matrix_data]
    arr = np.array(matrix_data)
    corr = np.corrcoef(arr)
    corr_matrix = [[round(float(corr[i][j]), 4) for j in range(len(valid_symbols))] for i in range(len(valid_symbols))]

    return CorrelationMatrixOut(symbols=valid_symbols, matrix=corr_matrix)


async def get_event_impact(db: AsyncSession, event_id: int) -> list[EventImpactOut]:
    event_result = await db.execute(
        select(GeopoliticalEvent).where(GeopoliticalEvent.id == event_id)
    )
    event = event_result.scalar_one_or_none()
    if not event:
        return []

    impact_result = await db.execute(
        select(EventImpact).where(EventImpact.event_id == event_id)
    )
    impacts = impact_result.scalars().all()

    items = []
    for imp in impacts:
        commodity_result = await db.execute(
            select(Commodity).where(Commodity.id == imp.commodity_id)
        )
        commodity = commodity_result.scalar_one_or_none()
        if not commodity:
            continue

        items.append(EventImpactOut(
            event=EventOut.model_validate(event),
            commodity=CommodityOut.model_validate(commodity),
            price_before=imp.price_before,
            price_after_1d=imp.price_after_1d,
            price_after_7d=imp.price_after_7d,
            price_after_30d=imp.price_after_30d,
            change_pct_1d=imp.change_pct_1d,
            change_pct_7d=imp.change_pct_7d,
            change_pct_30d=imp.change_pct_30d,
            ai_analysis=imp.ai_analysis,
        ))
    return items


async def get_macro_comparison(
    db: AsyncSession, indicator_code: str, commodity_symbol: str, period: str = "180d"
) -> MacroComparisonOut:
    days = PERIOD_MAP.get(period, 180)
    start = date.today() - timedelta(days=days)

    # Fetch indicators within range + the latest one before range (for forward-fill seed)
    seed_result = await db.execute(
        select(MacroIndicator)
        .where(MacroIndicator.indicator_code == indicator_code, MacroIndicator.report_date < start)
        .order_by(MacroIndicator.report_date.desc())
        .limit(1)
    )
    seed = seed_result.scalars().all()

    range_result = await db.execute(
        select(MacroIndicator)
        .where(MacroIndicator.indicator_code == indicator_code, MacroIndicator.report_date >= start)
        .order_by(MacroIndicator.report_date.asc())
    )
    indicators = seed + range_result.scalars().all()

    commodity_result = await db.execute(
        select(Commodity).where(Commodity.symbol == commodity_symbol)
    )
    commodity = commodity_result.scalar_one_or_none()

    prices = []
    if commodity:
        price_result = await db.execute(
            select(PriceDaily)
            .where(PriceDaily.commodity_id == commodity.id, PriceDaily.trade_date >= start)
            .order_by(PriceDaily.trade_date.asc())
        )
        prices = price_result.scalars().all()

    indicator_name = indicators[0].indicator_name if indicators else indicator_code

    # Use commodity trading dates as the base timeline
    price_map = {p.trade_date: float(p.close) for p in prices if p.close}
    indicator_map = {i.report_date: float(i.value) for i in indicators}

    # Also include indicator dates that predate the price range for forward-fill seed
    all_indicator_dates = sorted(indicator_map.keys())
    base_dates = sorted(price_map.keys()) if price_map else sorted(indicator_map.keys())

    # Forward-fill: for each base date, use the most recent indicator value
    indicator_values = []
    last_val = None
    # Pre-seed with the latest indicator value before our date range
    for d in all_indicator_dates:
        if base_dates and d < base_dates[0]:
            last_val = indicator_map[d]
        else:
            break

    for d in base_dates:
        if d in indicator_map:
            last_val = indicator_map[d]
        indicator_values.append(last_val)

    return MacroComparisonOut(
        indicator_code=indicator_code,
        indicator_name=indicator_name,
        commodity_symbol=commodity_symbol,
        dates=base_dates,
        indicator_values=indicator_values,
        commodity_prices=[price_map.get(d) for d in base_dates],
    )


async def get_ratios(db: AsyncSession, period: str = "1y") -> list[RatioItem]:
    # Parse period
    period_days = {"30d": 30, "90d": 90, "180d": 180, "1y": 365}
    days = period_days.get(period, 365)
    # Define ratio pairs: (name, numerator_symbol, denominator_symbol)
    ratio_defs = [
        ("金油比", "AU", "SC"),    # 黄金/原油 — 避险/风险偏好
        ("金银比", "AU", "AG"),    # 黄金/白银 — 贵金属套利
        ("铜金比", "CU", "AU"),    # 铜/黄金 — 经济预期
        ("铜油比", "CU", "SC"),    # 铜/原油 — 工业需求 vs 能源
        ("豆粕比", "A", "M"),      # 大豆/豆粕 — 压榨利润链
    ]

    # Load all needed symbols
    symbols_needed = set()
    for _, num, den in ratio_defs:
        symbols_needed.add(num)
        symbols_needed.add(den)

    result = await db.execute(select(Commodity).where(Commodity.symbol.in_(symbols_needed)))
    commodities = {c.symbol: c for c in result.scalars().all()}

    start = date.today() - timedelta(days=days)
    ratios = []

    # Pre-fetch all price data
    price_cache: dict[str, dict] = {}
    for sym, comm in commodities.items():
        prices = await db.execute(
            select(PriceDaily).where(PriceDaily.commodity_id == comm.id, PriceDaily.trade_date >= start)
            .order_by(PriceDaily.trade_date.asc())
        )
        price_cache[sym] = {p.trade_date: float(p.close) for p in prices.scalars().all() if p.close}

    for name, num_sym, den_sym in ratio_defs:
        num_map = price_cache.get(num_sym, {})
        den_map = price_cache.get(den_sym, {})
        if not num_map or not den_map:
            continue
        for d in sorted(set(num_map.keys()) & set(den_map.keys())):
            if den_map[d] > 0:
                ratios.append(RatioItem(date=d, ratio_name=name, value=round(num_map[d] / den_map[d], 4)))

    return ratios


async def get_daily_report(db: AsyncSession) -> str:
    from app.core.cache import cache_get, cache_set

    cache_key = "report:daily"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    overview = await get_overview(db)
    market_data = {item.symbol: f"{item.name_cn} {item.latest_price} ({item.change_pct}%)" for item in overview if item.latest_price}

    news_result = await get_articles(db, NewsListQuery(page=1, page_size=10))
    news_data = [{"title": n.title, "summary": n.summary} for n in news_result.get("items", [])]

    report = await generate_report(market_data, news_data)
    await cache_set(cache_key, report, ttl=3600)
    return report
