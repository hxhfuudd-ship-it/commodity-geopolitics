from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import Optional


class NewsArticleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    summary: Optional[str] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    published_at: datetime
    sentiment: Optional[str] = None
    sentiment_score: Optional[float] = None
    importance: Optional[int] = None
    related_commodities: list[str] = []


class NewsListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[NewsArticleOut]


class NewsListQuery(BaseModel):
    page: int = 1
    page_size: int = 20
    commodity: Optional[str] = None
    sentiment: Optional[str] = None
    importance_min: Optional[int] = None


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str] = None
    event_type: Optional[str] = None
    region: Optional[str] = None
    country_codes: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    severity: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class SentimentTrendItem(BaseModel):
    date: date
    bullish_count: int = 0
    bearish_count: int = 0
    neutral_count: int = 0
    avg_score: Optional[float] = None
