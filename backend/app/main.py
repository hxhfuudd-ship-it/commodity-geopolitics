from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.v1 import v1_router
from app.core.cache import init_redis, close_redis
from app.core.exceptions import register_exception_handlers
from app.database import engine
from app.models import Base
from app.services.market_service import init_commodities
from app.database import async_session
from app.tasks.scheduler import init_scheduler, shutdown_scheduler
from app.tasks.realtime_task import start_realtime_task, stop_realtime_task, prefill_cache


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
    await prefill_cache()
    start_realtime_task()
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
