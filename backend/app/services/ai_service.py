import json
import uuid
from datetime import datetime
from typing import AsyncGenerator, Optional
from loguru import logger

from sqlalchemy import select, text
from app.core.cache import get_redis
from app.database import async_session
from app.core.llm import chat_completion_stream
from app.schemas.ai import ChatMessage


MAX_HISTORY_ROUNDS = 20


async def create_session() -> str:
    session_id = str(uuid.uuid4())
    r = get_redis()
    await r.set(f"chat:session:{session_id}", json.dumps([]), ex=7200)
    return session_id


async def get_history(session_id: str) -> list[ChatMessage]:
    r = get_redis()
    data = await r.get(f"chat:session:{session_id}")
    if not data:
        return []
    messages = json.loads(data)
    return [ChatMessage(**m) for m in messages]


async def _save_message(session_id: str, role: str, content: str):
    r = get_redis()
    key = f"chat:session:{session_id}"
    data = await r.get(key)
    messages = json.loads(data) if data else []
    messages.append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat(),
    })
    if len(messages) > MAX_HISTORY_ROUNDS * 2:
        messages = messages[-(MAX_HISTORY_ROUNDS * 2):]
    await r.set(key, json.dumps(messages), ex=7200)


async def _build_context() -> str:
    market_info = ""
    trend_info = ""
    news_info = ""
    sentiment_info = ""

    try:
        async with async_session() as db:
            # 1. 最新收盘价
            rows = (await db.execute(text("""
                SELECT c.symbol, c.name_cn, p.close, p.trade_date
                FROM commodities c
                JOIN price_daily p ON p.commodity_id = c.id
                WHERE p.trade_date = (SELECT MAX(trade_date) FROM price_daily WHERE commodity_id = c.id)
                ORDER BY c.symbol
            """))).fetchall()
            if rows:
                market_info = "\n".join(f"{r[1]}({r[0]}): {r[2]} ({r[3]})" for r in rows)

            # 2. 近5日/20日涨跌幅
            trend_rows = (await db.execute(text("""
                WITH ranked AS (
                    SELECT c.symbol, c.name_cn, p.close, p.trade_date,
                           ROW_NUMBER() OVER (PARTITION BY c.id ORDER BY p.trade_date DESC) AS rn
                    FROM commodities c
                    JOIN price_daily p ON p.commodity_id = c.id
                )
                SELECT a.symbol, a.name_cn, a.close AS latest,
                       b.close AS close_5d, d.close AS close_20d
                FROM ranked a
                LEFT JOIN ranked b ON a.symbol = b.symbol AND b.rn = 6
                LEFT JOIN ranked d ON a.symbol = d.symbol AND d.rn = 21
                WHERE a.rn = 1
                ORDER BY a.symbol
            """))).fetchall()
            if trend_rows:
                lines = []
                for r in trend_rows:
                    latest, c5, c20 = float(r[2]) if r[2] else 0, r[3], r[4]
                    parts = [f"{r[1]}({r[0]})"]
                    if c5 and float(c5) > 0:
                        pct5 = (latest - float(c5)) / float(c5) * 100
                        parts.append(f"5日{pct5:+.2f}%")
                    if c20 and float(c20) > 0:
                        pct20 = (latest - float(c20)) / float(c20) * 100
                        parts.append(f"20日{pct20:+.2f}%")
                    lines.append(" | ".join(parts))
                trend_info = "\n".join(lines)

            # 3. 近3天重要新闻 (top 8)
            news_rows = (await db.execute(text("""
                SELECT title, sentiment, importance, published_at::date
                FROM news_articles
                WHERE published_at >= NOW() - INTERVAL '3 days'
                  AND importance >= 3
                ORDER BY importance DESC, published_at DESC
                LIMIT 8
            """))).fetchall()
            if news_rows:
                sentiment_map = {"bullish": "利多", "bearish": "利空", "neutral": "中性"}
                news_info = "\n".join(
                    f"[{sentiment_map.get(r[1], '中性')}] {r[0]} (重要性{r[2]}, {r[3]})"
                    for r in news_rows
                )

            # 4. 近7天整体情绪统计
            sent_rows = (await db.execute(text("""
                SELECT sentiment, COUNT(*) as cnt
                FROM news_articles
                WHERE published_at >= NOW() - INTERVAL '7 days'
                  AND sentiment IS NOT NULL
                GROUP BY sentiment
            """))).fetchall()
            if sent_rows:
                total = sum(r[1] for r in sent_rows)
                parts = []
                for r in sent_rows:
                    label = {"bullish": "利多", "bearish": "利空", "neutral": "中性"}.get(r[0], r[0])
                    parts.append(f"{label}{r[1]}条({r[1]/total*100:.0f}%)")
                sentiment_info = f"近7天新闻情绪: {', '.join(parts)}"

    except Exception as e:
        logger.warning(f"构建AI上下文失败: {e}")

    return f"""你是一个专业的大宗商品与地缘政治分析助手。你可以帮助用户分析：
- 大宗商品价格走势与涨跌原因
- 地缘政治事件对商品价格的影响
- 品种间的相关性和比价关系
- 宏观经济指标与商品价格的关联

## 当前市场最新收盘价
{market_info if market_info else "暂无数据"}

## 近期涨跌趋势
{trend_info if trend_info else "暂无数据"}

## 近3天重要新闻
{news_info if news_info else "暂无重要新闻"}

## 市场情绪
{sentiment_info if sentiment_info else "暂无数据"}

请基于以上实时数据回答用户问题。用中文回答，分析要专业但易懂。不要使用emoji表情。善用markdown格式组织内容：用标题(###)分段，用加粗(**重点**)突出关键数据，用列表整理要点，保持层次清晰。"""


async def chat(session_id: Optional[str], user_message: str) -> AsyncGenerator[str, None]:
    if not session_id:
        session_id = await create_session()

    await _save_message(session_id, "user", user_message)

    system_prompt = await _build_context()
    history = await get_history(session_id)

    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        messages.append({"role": msg.role, "content": msg.content})

    full_response = ""
    try:
        async for chunk in chat_completion_stream(messages):
            full_response += chunk
            yield chunk
    except Exception as e:
        error_msg = f"AI 服务暂时不可用: {str(e)}"
        yield error_msg
        full_response = error_msg

    await _save_message(session_id, "assistant", full_response)
