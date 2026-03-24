from datetime import datetime
from typing import Optional
import httpx
import feedparser
import re
from loguru import logger

RSS_SOURCES = [
    # 专业财经媒体
    {
        "name": "CNBC Commodities",
        "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100727362",
        "category": "commodity",
    },
    {
        "name": "CNBC World",
        "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100727362",
        "category": "general",
    },
    {
        "name": "FT Commodities",
        "url": "https://www.ft.com/commodities?format=rss",
        "category": "commodity",
    },
    {
        "name": "Investing.com Commodities",
        "url": "https://www.investing.com/rss/news_301.rss",
        "category": "commodity",
    },
    {
        "name": "Investing.com Economy",
        "url": "https://www.investing.com/rss/news_14.rss",
        "category": "general",
    },
    # Google News 大宗商品
    {
        "name": "Google News Commodities",
        "url": "https://news.google.com/rss/search?q=commodity+oil+gold+energy&hl=en-US&gl=US&ceid=US:en",
        "category": "commodity",
    },
    {
        "name": "Google News Business",
        "url": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en",
        "category": "general",
    },
    # Google News 按品种细分
    {
        "name": "Google News Metals",
        "url": "https://news.google.com/rss/search?q=gold+silver+copper+iron+ore+aluminum+nickel+price&hl=en-US&gl=US&ceid=US:en",
        "category": "commodity",
    },
    {
        "name": "Google News Agriculture",
        "url": "https://news.google.com/rss/search?q=soybean+corn+wheat+cotton+sugar+palm+oil+price&hl=en-US&gl=US&ceid=US:en",
        "category": "commodity",
    },
    {
        "name": "Google News Crude Oil",
        "url": "https://news.google.com/rss/search?q=crude+oil+OPEC+petroleum+barrel&hl=en-US&gl=US&ceid=US:en",
        "category": "commodity",
    },
    {
        "name": "Google News Gold",
        "url": "https://news.google.com/rss/search?q=gold+price+bullion+precious+metals&hl=en-US&gl=US&ceid=US:en",
        "category": "commodity",
    },
    # Google News 地缘政治/宏观
    {
        "name": "Google News Geopolitics",
        "url": "https://news.google.com/rss/search?q=geopolitics+sanctions+tariff+OPEC+Iran+trade+war&hl=en-US&gl=US&ceid=US:en",
        "category": "general",
    },
    {
        "name": "Google News Trade",
        "url": "https://news.google.com/rss/search?q=trade+war+tariff+sanctions+embargo+supply+chain&hl=en-US&gl=US&ceid=US:en",
        "category": "general",
    },
    {
        "name": "Google News Fed",
        "url": "https://news.google.com/rss/search?q=federal+reserve+interest+rate+inflation+CPI+dollar&hl=en-US&gl=US&ceid=US:en",
        "category": "general",
    },
    # Google News 代理 Reuters/Bloomberg
    {
        "name": "Reuters Commodities",
        "url": "https://news.google.com/rss/search?q=site:reuters.com+commodity+OR+oil+OR+gold+OR+copper&hl=en-US&gl=US&ceid=US:en",
        "category": "commodity",
    },
    {
        "name": "Bloomberg Markets",
        "url": "https://news.google.com/rss/search?q=site:bloomberg.com+commodities+OR+crude+OR+metals&hl=en-US&gl=US&ceid=US:en",
        "category": "commodity",
    },
    {
        "name": "WSJ Markets",
        "url": "https://news.google.com/rss/search?q=site:wsj.com+commodities+OR+oil+OR+gold+OR+copper&hl=en-US&gl=US&ceid=US:en",
        "category": "commodity",
    },
    {
        "name": "MarketWatch Commodities",
        "url": "https://news.google.com/rss/search?q=site:marketwatch.com+commodity+OR+gold+OR+oil+OR+futures&hl=en-US&gl=US&ceid=US:en",
        "category": "commodity",
    },
]

# 大宗商品相关关键词及权重
COMMODITY_KEYWORDS = {
    # 品种
    "gold": 3, "silver": 3, "copper": 3, "aluminum": 3, "aluminium": 3,
    "nickel": 3, "iron ore": 3, "steel": 2,
    "oil": 3, "crude": 3, "brent": 3, "wti": 3, "natural gas": 3, "lng": 2, "coal": 2,
    "soybean": 3, "corn": 3, "wheat": 3, "cotton": 3, "sugar": 3, "rubber": 2,
    "palm oil": 3, "soy": 2, "grain": 2,
    "pta": 2, "methanol": 2, "polypropylene": 2,
    # 地缘/宏观
    "opec": 3, "sanctions": 3, "tariff": 3, "trade war": 3, "embargo": 3,
    "geopolitical": 2, "iran": 2, "russia": 2, "ukraine": 2, "middle east": 2,
    "hormuz": 3, "strait": 2, "pipeline": 2, "supply chain": 2,
    # 市场
    "commodity": 2, "commodities": 2, "futures": 2, "mining": 2, "refinery": 2,
    "fed": 2, "interest rate": 2, "inflation": 2, "dollar": 2, "cpi": 2,
    "rally": 1, "surge": 1, "plunge": 1, "crash": 1, "soar": 1,
}

_KW_PATTERN = re.compile(
    "|".join(re.escape(k) for k in sorted(COMMODITY_KEYWORDS, key=len, reverse=True)),
    re.IGNORECASE,
)


def _relevance_score(title: str, content: str) -> int:
    text = f"{title} {content}"
    score = 0
    for match in _KW_PATTERN.finditer(text):
        kw = match.group().lower()
        # 找到最长匹配的关键词
        for k, w in COMMODITY_KEYWORDS.items():
            if kw == k.lower():
                score += w
                break
    return score


async def fetch_rss_news(source_url: Optional[str] = None, max_articles: int = 80) -> list[dict]:
    all_articles = []
    sources = RSS_SOURCES if source_url is None else [{"name": "custom", "url": source_url, "category": "general"}]

    async with httpx.AsyncClient(
        timeout=15.0,
        follow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"},
    ) as client:
        for source in sources:
            try:
                response = await client.get(source["url"])
                if response.status_code != 200:
                    logger.warning(f"RSS 获取失败 {source['name']}: HTTP {response.status_code}")
                    continue

                feed = feedparser.parse(response.text)
                for entry in feed.entries[:20]:
                    published = None
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        published = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                        published = datetime(*entry.updated_parsed[:6])
                    else:
                        published = datetime.now()

                    title = entry.get("title", "")
                    content = entry.get("summary", entry.get("description", ""))
                    score = _relevance_score(title, content)

                    # commodity 源给额外加分
                    if source["category"] == "commodity":
                        score += 1

                    article = {
                        "title": title,
                        "content": content,
                        "source": source["name"],
                        "source_url": entry.get("link", ""),
                        "published_at": published,
                        "relevance": score,
                    }
                    if article["title"] and article["source_url"]:
                        all_articles.append(article)

                logger.info(f"RSS 抓取成功 {source['name']}: {len(feed.entries)} 条")

            except Exception as e:
                logger.warning(f"RSS 抓取异常 {source['name']}: {e}")
                continue

    # 去重
    seen_urls = set()
    unique = []
    for article in all_articles:
        if article["source_url"] not in seen_urls:
            seen_urls.add(article["source_url"])
            unique.append(article)

    # 按相关性降序，取前 max_articles 条
    unique.sort(key=lambda a: a["relevance"], reverse=True)
    result = unique[:max_articles]

    logger.info(f"RSS 抓取完成，共 {len(unique)} 条，筛选保留 {len(result)} 条 (相关性 >= {result[-1]['relevance'] if result else 0})")
    return result
