from datetime import datetime
from typing import Optional
import httpx
import feedparser
import re
import json
from loguru import logger

# 国内可访问的新闻源（优先）+ 国际源（备用）
RSS_SOURCES = [
    # === 国内源（大陆服务器可访问）===
    {
        "name": "新浪财经期货",
        "url": "https://feed.mix.sina.com.cn/api/roll/get?pageid=155&lid=1543&num=30&versionNumber=1.2.4",
        "category": "commodity",
        "type": "sina_api",
    },
    {
        "name": "新浪财经宏观",
        "url": "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2516&num=30&versionNumber=1.2.4",
        "category": "general",
        "type": "sina_api",
    },
    {
        "name": "东方财富期货",
        "url": "https://newsapi.eastmoney.com/kuaixun/v1/getlist_102_ajaxResult_50_1_.html",
        "category": "commodity",
        "type": "eastmoney_api",
    },
    {
        "name": "东方财富全球",
        "url": "https://newsapi.eastmoney.com/kuaixun/v1/getlist_106_ajaxResult_50_1_.html",
        "category": "general",
        "type": "eastmoney_api",
    },
    {
        "name": "金十数据",
        "url": "https://flash-api.jin10.com/get_flash_list?channel=-8200&vip=0&max_time=&_=",
        "category": "commodity",
        "type": "jin10_api",
    },
    # === 国际源（备用，大陆可能无法访问）===
    {
        "name": "CNBC Commodities",
        "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100727362",
        "category": "commodity",
        "type": "rss",
    },
    {
        "name": "Investing.com Commodities",
        "url": "https://www.investing.com/rss/news_301.rss",
        "category": "commodity",
        "type": "rss",
    },
]

COMMODITY_KEYWORDS = {
    # 中文关键词
    "黄金": 3, "白银": 3, "铜": 3, "铝": 3, "镍": 3, "铁矿": 3, "钢铁": 2,
    "原油": 3, "石油": 3, "燃油": 2, "天然气": 3, "液化气": 2, "煤炭": 2,
    "大豆": 3, "豆粕": 3, "豆油": 3, "棕榈油": 3, "玉米": 3, "棉花": 3, "白糖": 3, "橡胶": 3,
    "PTA": 2, "甲醇": 2, "聚丙烯": 2,
    "期货": 2, "大宗商品": 3, "OPEC": 3, "欧佩克": 3,
    "关税": 3, "制裁": 3, "贸易战": 3, "地缘": 2, "中东": 2,
    "美联储": 3, "加息": 2, "降息": 2, "通胀": 2, "CPI": 2, "美元": 2, "人民币": 2,
    "供应链": 2, "减产": 3, "增产": 3, "库存": 2, "交割": 2, "主力合约": 2,
    # English keywords
    "gold": 3, "silver": 3, "copper": 3, "aluminum": 3, "aluminium": 3,
    "nickel": 3, "iron ore": 3, "steel": 2,
    "oil": 3, "crude": 3, "brent": 3, "wti": 3, "natural gas": 3,
    "soybean": 3, "corn": 3, "wheat": 3, "cotton": 3, "sugar": 3, "rubber": 2,
    "palm oil": 3, "opec": 3, "sanctions": 3, "tariff": 3, "trade war": 3,
    "commodity": 2, "commodities": 2, "futures": 2,
    "fed": 2, "interest rate": 2, "inflation": 2, "dollar": 2,
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
        for k, w in COMMODITY_KEYWORDS.items():
            if kw == k.lower():
                score += w
                break
    return score


async def _fetch_sina_api(client: httpx.AsyncClient, source: dict) -> list[dict]:
    """新浪财经滚动新闻 API"""
    articles = []
    try:
        resp = await client.get(source["url"])
        if resp.status_code != 200:
            return []
        text = resp.text
        # Sina API returns JS callback, extract JSON
        if text.startswith("var "):
            text = text.split("=", 1)[1].strip().rstrip(";")
        data = json.loads(text)
        items = data.get("result", {}).get("data", [])
        for item in items[:30]:
            title = item.get("title", "")
            content = item.get("summary", "") or item.get("intro", "") or ""
            url = item.get("url", "")
            pub_time = item.get("ctime", "") or item.get("createTime", "")
            published = None
            if pub_time:
                try:
                    published = datetime.strptime(pub_time, "%Y-%m-%d %H:%M:%S")
                except Exception:
                    try:
                        published = datetime.strptime(pub_time, "%Y年%m月%d日 %H:%M")
                    except Exception:
                        published = datetime.now()
            else:
                published = datetime.now()

            if title and url:
                articles.append({
                    "title": title,
                    "content": content,
                    "source": source["name"],
                    "source_url": url,
                    "published_at": published,
                })
        logger.info(f"新浪API抓取成功 {source['name']}: {len(articles)} 条")
    except Exception as e:
        logger.warning(f"新浪API抓取异常 {source['name']}: {e}")
    return articles


async def _fetch_eastmoney_api(client: httpx.AsyncClient, source: dict) -> list[dict]:
    """东方财富快讯 API"""
    articles = []
    try:
        resp = await client.get(source["url"])
        if resp.status_code != 200:
            return []
        text = resp.text.strip()
        # Remove JSONP wrapper or var assignment
        if text.startswith("var "):
            text = text.split("=", 1)[1].strip().rstrip(";")
        elif "(" in text and text.endswith(")"):
            text = text[text.index("(") + 1:text.rindex(")")]
        elif text.startswith("[") or text.startswith("{"):
            pass
        else:
            # Try to find JSON in the response
            for start_char in ["{", "["]:
                idx = text.find(start_char)
                if idx >= 0:
                    text = text[idx:]
                    break

        data = json.loads(text)
        items = []
        if isinstance(data, dict):
            items = data.get("LivesList", []) or data.get("list", []) or data.get("data", {}).get("list", [])
        elif isinstance(data, list):
            items = data

        for item in items[:30]:
            title = item.get("title", "") or item.get("Title", "")
            content = item.get("digest", "") or item.get("Content", "") or item.get("summary", "") or ""
            url = item.get("url_w", "") or item.get("Url", "") or item.get("url", "")
            pub_time = item.get("showtime", "") or item.get("ShowTime", "") or item.get("time", "")
            published = None
            if pub_time:
                for fmt in ["%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%m-%d %H:%M"]:
                    try:
                        published = datetime.strptime(pub_time, fmt)
                        if published.year == 1900:
                            published = published.replace(year=datetime.now().year)
                        break
                    except Exception:
                        continue
            if not published:
                published = datetime.now()

            if not url and item.get("code"):
                url = f"https://finance.eastmoney.com/a/{item['code']}.html"

            if title and url:
                articles.append({
                    "title": title,
                    "content": content,
                    "source": source["name"],
                    "source_url": url,
                    "published_at": published,
                })
        logger.info(f"东方财富API抓取成功 {source['name']}: {len(articles)} 条")
    except Exception as e:
        logger.warning(f"东方财富API抓取异常 {source['name']}: {e}")
    return articles


async def _fetch_jin10_api(client: httpx.AsyncClient, source: dict) -> list[dict]:
    """金十数据快讯 API"""
    articles = []
    try:
        url = source["url"] + str(int(datetime.now().timestamp() * 1000))
        headers = {
            "x-app-id": "bVBF4FyRTn5NJF5n",
            "x-version": "1.0.0",
            "Referer": "https://www.jin10.com/",
        }
        resp = await client.get(url, headers=headers)
        if resp.status_code != 200:
            return []
        data = resp.json()
        items = data.get("data", [])
        for item in items[:30]:
            content = item.get("data", {})
            title = content.get("title", "") or content.get("content", "")
            if not title:
                continue
            # Strip HTML tags
            title = re.sub(r"<[^>]+>", "", title).strip()
            if len(title) < 8:
                continue
            pub_time = item.get("time", "")
            published = None
            if pub_time:
                try:
                    published = datetime.strptime(pub_time, "%Y-%m-%d %H:%M:%S")
                except Exception:
                    published = datetime.now()
            else:
                published = datetime.now()

            source_url = f"https://www.jin10.com/flash_detail/{item.get('id', '')}.html"
            articles.append({
                "title": title[:500],
                "content": title,
                "source": source["name"],
                "source_url": source_url,
                "published_at": published,
            })
        logger.info(f"金十API抓取成功 {source['name']}: {len(articles)} 条")
    except Exception as e:
        logger.warning(f"金十API抓取异常 {source['name']}: {e}")
    return articles


async def _fetch_rss(client: httpx.AsyncClient, source: dict) -> list[dict]:
    """标准 RSS 源抓取"""
    articles = []
    try:
        response = await client.get(source["url"])
        if response.status_code != 200:
            logger.warning(f"RSS 获取失败 {source['name']}: HTTP {response.status_code}")
            return []

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

            article = {
                "title": title,
                "content": content,
                "source": source["name"],
                "source_url": entry.get("link", ""),
                "published_at": published,
            }
            if article["title"] and article["source_url"]:
                articles.append(article)

        logger.info(f"RSS 抓取成功 {source['name']}: {len(feed.entries)} 条")
    except Exception as e:
        logger.warning(f"RSS 抓取异常 {source['name']}: {e}")
    return articles


_FETCH_MAP = {
    "sina_api": _fetch_sina_api,
    "eastmoney_api": _fetch_eastmoney_api,
    "jin10_api": _fetch_jin10_api,
    "rss": _fetch_rss,
}


async def fetch_rss_news(source_url: Optional[str] = None, max_articles: int = 80) -> list[dict]:
    all_articles = []

    if source_url:
        sources = [{"name": "custom", "url": source_url, "category": "general", "type": "rss"}]
    else:
        sources = RSS_SOURCES

    async with httpx.AsyncClient(
        timeout=15.0,
        follow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"},
    ) as client:
        for source in sources:
            fetcher = _FETCH_MAP.get(source.get("type", "rss"), _fetch_rss)
            try:
                articles = await fetcher(client, source)
                for article in articles:
                    score = _relevance_score(article["title"], article["content"])
                    if source["category"] == "commodity":
                        score += 1
                    article["relevance"] = score
                all_articles.extend(articles)
            except Exception as e:
                logger.warning(f"新闻源抓取异常 {source['name']}: {e}")
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

    logger.info(f"新闻抓取完成，共 {len(unique)} 条，筛选保留 {len(result)} 条 (相关性 >= {result[-1]['relevance'] if result else 0})")
    return result
