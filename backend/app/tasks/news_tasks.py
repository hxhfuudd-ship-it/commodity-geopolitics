from datetime import datetime, timedelta
from loguru import logger
from sqlalchemy import select, delete

from app.database import async_session
from app.models.news import NewsArticle, NewsCommodityRel
from app.models.commodity import Commodity
from app.data_sources.rss_client import fetch_rss_news
from app.core.llm import analyze_news
from app.core.cache import cache_get, cache_set
from app.core.lock import acquire_lock, release_lock


async def fetch_news_data():
    lock_name = "lock:task:fetch_news_data"
    if not await acquire_lock(lock_name, timeout=880):
        logger.debug("新闻抓取任务已被其他实例锁定，跳过")
        return

    try:
        articles = await fetch_rss_news()
        async with async_session() as db:
            added = 0
            for article in articles:
                existing = await db.execute(
                    select(NewsArticle).where(
                        NewsArticle.source_url == article["source_url"]
                    )
                )
                if existing.scalar_one_or_none():
                    continue

                news = NewsArticle(
                    title=article["title"],
                    content=article["content"],
                    source=article["source"],
                    source_url=article["source_url"],
                    published_at=article["published_at"],
                )
                db.add(news)
                added += 1

            await db.commit()
            logger.info(f"新闻抓取完成，新增 {added} 条")

    except Exception as e:
        logger.error(f"新闻抓取任务异常: {e}")
    finally:
        await release_lock(lock_name)


async def process_news_ai():
    lock_name = "lock:task:process_news_ai"
    if not await acquire_lock(lock_name, timeout=880):
        logger.debug("新闻AI处理任务已被其他实例锁定，跳过")
        return

    try:
        async with async_session() as db:
            result = await db.execute(
                select(NewsArticle)
                .where(NewsArticle.sentiment.is_(None))
                .order_by(NewsArticle.published_at.desc())
                .limit(80)
            )
            articles = result.scalars().all()

            for article in articles:
                processed_key = f"ai:news_processed:{article.id}"
                if await cache_get(processed_key):
                    continue

                try:
                    analysis = await analyze_news(article.title, article.content or "")
                    if analysis:
                        article.summary = analysis.get("summary", "")
                        article.sentiment = analysis.get("sentiment", "neutral")
                        article.sentiment_score = analysis.get("sentiment_score", 0.0)
                        article.importance = analysis.get("importance", 3)

                        # Create commodity relations
                        related = analysis.get("related_commodities", [])
                        if related:
                            sym_result = await db.execute(
                                select(Commodity).where(Commodity.symbol.in_(related))
                            )
                            for comm in sym_result.scalars().all():
                                existing_rel = await db.execute(
                                    select(NewsCommodityRel).where(
                                        NewsCommodityRel.news_id == article.id,
                                        NewsCommodityRel.commodity_id == comm.id,
                                    )
                                )
                                if not existing_rel.scalar_one_or_none():
                                    db.add(NewsCommodityRel(
                                        news_id=article.id,
                                        commodity_id=comm.id,
                                        relevance_score=0.8,
                                        impact_direction=analysis.get("sentiment", "neutral"),
                                    ))

                        await cache_set(processed_key, "1", ttl=86400)

                except Exception as e:
                    logger.warning(f"新闻AI处理失败 id={article.id}: {e}")
                    continue

            await db.commit()
            logger.info(f"新闻AI处理完成，处理 {len(articles)} 条")

    except Exception as e:
        logger.error(f"新闻AI处理任务异常: {e}")
    finally:
        await release_lock(lock_name)


async def cleanup_old_news():
    """删除30天前的新闻及其品种关联"""
    try:
        async with async_session() as db:
            cutoff = datetime.now() - timedelta(days=30)
            old_ids_result = await db.execute(
                select(NewsArticle.id).where(NewsArticle.published_at < cutoff)
            )
            old_ids = [r[0] for r in old_ids_result.all()]
            if not old_ids:
                return

            await db.execute(delete(NewsCommodityRel).where(NewsCommodityRel.news_id.in_(old_ids)))
            await db.execute(delete(NewsArticle).where(NewsArticle.id.in_(old_ids)))
            await db.commit()
            logger.info(f"清理过期新闻完成，删除 {len(old_ids)} 条")
    except Exception as e:
        logger.error(f"清理过期新闻异常: {e}")
