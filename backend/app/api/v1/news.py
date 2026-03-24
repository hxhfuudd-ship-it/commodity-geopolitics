from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.news import NewsArticleOut, NewsListQuery, NewsListResponse, EventOut, SentimentTrendItem
from app.services import news_service

router = APIRouter(prefix="/news", tags=["新闻"])


@router.get("/articles")
async def list_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    commodity: Optional[str] = Query(None),
    sentiment: Optional[str] = Query(None),
    importance_min: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> NewsListResponse:
    query = NewsListQuery(
        page=page, page_size=page_size,
        commodity=commodity, sentiment=sentiment,
        importance_min=importance_min,
    )
    return await news_service.get_articles(db, query)


@router.get("/articles/{article_id}", response_model=NewsArticleOut)
async def get_article(article_id: int, db: AsyncSession = Depends(get_db)) -> NewsArticleOut:
    result = await news_service.get_article_detail(db, article_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"文章 {article_id} 不存在")
    return result


@router.get("/sentiment/trend", response_model=list[SentimentTrendItem])
async def sentiment_trend(
    commodity: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
) -> list[SentimentTrendItem]:
    return await news_service.get_sentiment_trend(db, commodity, days)


@router.get("/events", response_model=list[EventOut])
async def list_events(db: AsyncSession = Depends(get_db)) -> list[EventOut]:
    return await news_service.get_events(db)


@router.get("/events/timeline")
async def events_timeline(db: AsyncSession = Depends(get_db)) -> list:
    return await news_service.get_events_timeline(db)
