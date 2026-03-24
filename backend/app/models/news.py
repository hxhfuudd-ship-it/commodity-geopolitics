from sqlalchemy import Column, Integer, BigInteger, String, Text, SmallInteger, Numeric, DateTime, ForeignKey, Index
from app.database import Base


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    content = Column(Text)
    summary = Column(Text, nullable=True)
    source = Column(String(100))
    source_url = Column(String(1000), unique=True)
    published_at = Column(DateTime, nullable=False)
    sentiment = Column(String(10), nullable=True)
    sentiment_score = Column(Numeric(4, 3), nullable=True)
    importance = Column(SmallInteger, nullable=True)

    __table_args__ = (
        Index("ix_news_published_at", published_at.desc()),
        Index("ix_news_sentiment", "sentiment"),
    )


class NewsCommodityRel(Base):
    __tablename__ = "news_commodity_rel"

    news_id = Column(BigInteger, ForeignKey("news_articles.id"), primary_key=True)
    commodity_id = Column(Integer, ForeignKey("commodities.id"), primary_key=True)
    relevance_score = Column(Numeric(4, 3))
    impact_direction = Column(String(10))
