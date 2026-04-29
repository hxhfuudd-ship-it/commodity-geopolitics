from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from sqlalchemy import select

from app.api.v1 import v1_router
from app.core.cache import init_redis, close_redis
from app.core.exceptions import register_exception_handlers
from app.database import engine
from app.models import Base
from app.services.market_service import init_commodities
from app.database import async_session
from app.tasks.scheduler import init_scheduler, shutdown_scheduler
from app.tasks.realtime_task import start_realtime_task, stop_realtime_task, prefill_cache
from app.tasks.news_tasks import fetch_news_data, process_news_ai
from app.tasks.market_tasks import fetch_market_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动
    logger.info("应用启动中...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("数据库表创建完成")

    await init_redis()

    async with async_session() as db:
        await init_commodities(db)

    init_scheduler()

    # Startup: immediately refresh daily market data (populates settle prices)
    try:
        logger.info("启动时立即刷新日线数据（含结算价）...")
        await fetch_market_data()
        logger.info("启动日线数据刷新完成")
    except Exception as e:
        logger.warning(f"启动日线数据刷新失败: {e}")

    await prefill_cache()
    start_realtime_task()

    # Startup news backfill: fetch immediately if DB has no recent news
    try:
        from app.models.news import NewsArticle
        from datetime import timedelta
        async with async_session() as db:
            cutoff = datetime.now() - timedelta(days=1)
            recent = (await db.execute(
                select(NewsArticle).where(NewsArticle.published_at >= cutoff).limit(1)
            )).scalar_one_or_none()
            if not recent:
                logger.info("数据库无近期新闻，启动时立即抓取...")
                await fetch_news_data()
                await process_news_ai()
                logger.info("启动新闻补抓完成")
    except Exception as e:
        logger.warning(f"启动新闻补抓失败: {e}")

    logger.info("应用启动完成")

    yield

    # 关闭
    stop_realtime_task()
    shutdown_scheduler()
    await close_redis()
    await engine.dispose()
    logger.info("应用已关闭")


app = FastAPI(
    title="大宗商品地缘政治数据平台",
    description="聚焦大宗商品与地缘政治事件的关联分析平台",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
app.include_router(v1_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "commodity-geopolitics-api"}
