from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from app.config import settings
from app.tasks.market_tasks import fetch_market_data
from app.tasks.news_tasks import fetch_news_data, process_news_ai, cleanup_old_news
from app.tasks.macro_tasks import fetch_macro_data

scheduler = AsyncIOScheduler()


def init_scheduler():
    scheduler.add_job(
        fetch_market_data,
        "interval",
        seconds=settings.AKSHARE_FETCH_INTERVAL,
        id="fetch_market_data",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.add_job(
        fetch_news_data,
        "interval",
        seconds=settings.NEWS_FETCH_INTERVAL,
        id="fetch_news_data",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.add_job(
        process_news_ai,
        "interval",
        seconds=settings.NEWS_FETCH_INTERVAL + 60,
        id="process_news_ai",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.add_job(
        fetch_macro_data,
        "interval",
        hours=6,
        id="fetch_macro_data",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.add_job(
        cleanup_old_news,
        "interval",
        hours=12,
        id="cleanup_old_news",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.start()
    logger.info("APScheduler 已启动")


def shutdown_scheduler():
    scheduler.shutdown(wait=False)
    logger.info("APScheduler 已关闭")
