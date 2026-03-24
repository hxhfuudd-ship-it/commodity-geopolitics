from datetime import date, datetime, timedelta
from typing import Optional
from sqlalchemy import select, func, and_, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.news import NewsArticle, NewsCommodityRel
from app.models.geopolitical_event import GeopoliticalEvent
from app.models.commodity import Commodity
from app.schemas.news import NewsArticleOut, NewsListQuery, EventOut, SentimentTrendItem
from app.core.llm import analyze_news
from app.core.cache import cache_get, cache_set


async def get_articles(db: AsyncSession, query: NewsListQuery) -> dict:
    stmt = select(NewsArticle)

    # 只显示30天内的新闻，且必须已被 AI 分析过（过滤广告）
    one_month_ago = datetime.now() - timedelta(days=30)
    stmt = stmt.where(NewsArticle.published_at >= one_month_ago)
    stmt = stmt.where(NewsArticle.sentiment.isnot(None))

    if query.sentiment:
        stmt = stmt.where(NewsArticle.sentiment == query.sentiment)
    if query.importance_min:
        stmt = stmt.where(NewsArticle.importance >= query.importance_min)
    if query.commodity:
        stmt = stmt.join(NewsCommodityRel, NewsCommodityRel.news_id == NewsArticle.id)
        stmt = stmt.join(Commodity, Commodity.id == NewsCommodityRel.commodity_id)
        stmt = stmt.where(Commodity.symbol == query.commodity)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # 按天降序，同日按重要性降序
    stmt = stmt.order_by(
        cast(NewsArticle.published_at, Date).desc(),
        NewsArticle.importance.desc().nullslast(),
        NewsArticle.published_at.desc(),
    )
    stmt = stmt.offset((query.page - 1) * query.page_size).limit(query.page_size)

    result = await db.execute(stmt)
    articles = result.scalars().all()

    items = []
    for a in articles:
        rel_result = await db.execute(
            select(Commodity.symbol)
            .join(NewsCommodityRel, NewsCommodityRel.commodity_id == Commodity.id)
            .where(NewsCommodityRel.news_id == a.id)
        )
        related = [r[0] for r in rel_result.all()]
        items.append(NewsArticleOut(
            id=a.id, title=a.title, summary=a.summary, source=a.source,
            source_url=a.source_url, published_at=a.published_at,
            sentiment=a.sentiment, sentiment_score=a.sentiment_score,
            importance=a.importance, related_commodities=related,
        ))

    return {"total": total, "page": query.page, "page_size": query.page_size, "items": items}


async def get_article_detail(db: AsyncSession, article_id: int) -> Optional[NewsArticleOut]:
    result = await db.execute(select(NewsArticle).where(NewsArticle.id == article_id))
    a = result.scalar_one_or_none()
    if not a:
        return None

    rel_result = await db.execute(
        select(Commodity.symbol)
        .join(NewsCommodityRel, NewsCommodityRel.commodity_id == Commodity.id)
        .where(NewsCommodityRel.news_id == a.id)
    )
    related = [r[0] for r in rel_result.all()]

    return NewsArticleOut(
        id=a.id, title=a.title, summary=a.summary, source=a.source,
        source_url=a.source_url, published_at=a.published_at,
        sentiment=a.sentiment, sentiment_score=a.sentiment_score,
        importance=a.importance, related_commodities=related,
    )


async def get_sentiment_trend(db: AsyncSession, commodity: Optional[str] = None, days: int = 30) -> list[SentimentTrendItem]:
    start = datetime.now() - timedelta(days=days)
    stmt = select(
        cast(NewsArticle.published_at, Date).label("date"),
        func.count().filter(NewsArticle.sentiment == "bullish").label("bullish_count"),
        func.count().filter(NewsArticle.sentiment == "bearish").label("bearish_count"),
        func.count().filter(NewsArticle.sentiment == "neutral").label("neutral_count"),
        func.avg(NewsArticle.sentiment_score).label("avg_score"),
    ).where(NewsArticle.published_at >= start)

    if commodity:
        stmt = stmt.join(NewsCommodityRel, NewsCommodityRel.news_id == NewsArticle.id)
        stmt = stmt.join(Commodity, Commodity.id == NewsCommodityRel.commodity_id)
        stmt = stmt.where(Commodity.symbol == commodity)

    stmt = stmt.group_by(cast(NewsArticle.published_at, Date)).order_by(cast(NewsArticle.published_at, Date))

    result = await db.execute(stmt)
    rows = result.all()
    return [
        SentimentTrendItem(
            date=r.date, bullish_count=r.bullish_count or 0,
            bearish_count=r.bearish_count or 0, neutral_count=r.neutral_count or 0,
            avg_score=float(r.avg_score) if r.avg_score else None,
        )
        for r in rows
    ]


async def get_events(db: AsyncSession) -> list[EventOut]:
    result = await db.execute(
        select(GeopoliticalEvent).order_by(GeopoliticalEvent.start_date.desc())
    )
    rows = result.scalars().all()
    return [EventOut.model_validate(r) for r in rows]


async def get_events_timeline(db: AsyncSession) -> list[dict]:
    result = await db.execute(
        select(GeopoliticalEvent).order_by(GeopoliticalEvent.start_date.asc())
    )
    rows = result.scalars().all()
    return [
        {
            "id": e.id,
            "title": e.title,
            "description": e.description or "",
            "event_type": e.event_type,
            "region": e.region,
            "country_codes": e.country_codes or "",
            "start_date": e.start_date.isoformat(),
            "end_date": e.end_date.isoformat() if e.end_date else None,
            "severity": e.severity,
            "latitude": float(e.latitude) if e.latitude else None,
            "longitude": float(e.longitude) if e.longitude else None,
        }
        for e in rows
    ]


async def process_news_with_ai(db: AsyncSession, article_id: int):
    result = await db.execute(select(NewsArticle).where(NewsArticle.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        return

    if article.summary and article.sentiment:
        return

    try:
        analysis = await analyze_news(article.title, article.content or "")
        article.summary = analysis.get("summary", article.title)
        article.sentiment = analysis.get("sentiment", "neutral")
        article.sentiment_score = analysis.get("sentiment_score", 0.5)
        article.importance = analysis.get("importance", 1)

        related_symbols = analysis.get("related_commodities", [])
        for symbol in related_symbols:
            commodity_result = await db.execute(
                select(Commodity).where(Commodity.symbol == symbol)
            )
            commodity = commodity_result.scalar_one_or_none()
            if commodity:
                existing = await db.execute(
                    select(NewsCommodityRel).where(
                        and_(NewsCommodityRel.news_id == article.id, NewsCommodityRel.commodity_id == commodity.id)
                    )
                )
                if not existing.scalar_one_or_none():
                    rel = NewsCommodityRel(
                        news_id=article.id, commodity_id=commodity.id,
                        relevance_score=0.8, impact_direction=article.sentiment or "neutral",
                    )
                    db.add(rel)

        await db.commit()
        logger.info(f"新闻 AI 分析完成: {article.title[:50]}")
    except Exception as e:
        logger.error(f"新闻 AI 分析失败: {e}")
        await db.rollback()
