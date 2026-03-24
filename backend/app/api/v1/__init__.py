from fastapi import APIRouter
from app.api.v1.market import router as market_router
from app.api.v1.news import router as news_router
from app.api.v1.analysis import router as analysis_router
from app.api.v1.ai import router as ai_router
from app.api.v1.backtest import router as backtest_router

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(market_router)
v1_router.include_router(news_router)
v1_router.include_router(analysis_router)
v1_router.include_router(ai_router)
v1_router.include_router(backtest_router)
