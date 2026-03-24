from typing import AsyncGenerator, Optional
from openai import AsyncOpenAI
from loguru import logger
from app.config import settings

_client: Optional[AsyncOpenAI] = None


def get_llm_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
        )
    return _client


async def chat_completion(messages: list[dict], stream: bool = False):
    client = get_llm_client()
    try:
        response = await client.chat.completions.create(
            model=settings.DEEPSEEK_MODEL,
            messages=messages,
            stream=stream,
            temperature=0.7,
            max_tokens=2048,
        )
        if stream:
            return response
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"LLM 调用失败: {e}")
        raise


async def chat_completion_stream(messages: list[dict]) -> AsyncGenerator[str, None]:
    client = get_llm_client()
    try:
        response = await client.chat.completions.create(
            model=settings.DEEPSEEK_MODEL,
            messages=messages,
            stream=True,
            temperature=0.7,
            max_tokens=2048,
        )
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        logger.error(f"LLM 流式调用失败: {e}")
        raise


async def analyze_news(title: str, content: str) -> dict:
    prompt = f"""分析以下新闻，返回 JSON 格式：
{{
    "summary": "100字以内摘要",
    "sentiment": "bullish 或 bearish 或 neutral",
    "sentiment_score": 0.0到1.0之间的数值（0=极度利空, 0.5=中性, 1.0=极度利多）,
    "related_commodities": ["从以下品种代码中选择所有相关的，可多选"],
    "importance": 1到5的整数（1=低，5=极高）
}}

可选品种代码（必须严格使用以下代码）：
- 金属：AU(黄金), AG(白银), CU(铜), AL(铝), NI(镍), FE(铁矿石)
- 能源：SC(上海原油/国际原油), FU(燃料油), PG(LPG液化气)
- 农产品：A(大豆), M(豆粕), Y(豆油), P(棕榈油), C(玉米), CF(棉花), SR(白糖), RU(橡胶)
- 化工：TA(PTA), MA(甲醇), PP(聚丙烯)

注意：
- 原油相关新闻（WTI、Brent、OPEC、油价等）请归类为 SC
- 天然气/LNG 相关请归类为 PG
- 燃料油相关请归类为 FU
- 一条新闻可以关联多个品种，比如地缘冲突可能同时影响 SC 和 AU

标题：{title}
内容：{content[:2000]}"""

    try:
        import json
        import re
        result = await chat_completion([
            {"role": "system", "content": "你是一个大宗商品市场分析师，擅长分析地缘政治事件对商品价格的影响。请严格返回 JSON 格式。"},
            {"role": "user", "content": prompt},
        ])
        # 去掉 markdown 代码块包裹
        cleaned = re.sub(r'^```(?:json)?\s*', '', result.strip())
        cleaned = re.sub(r'\s*```$', '', cleaned)
        return json.loads(cleaned)
    except Exception as e:
        logger.error(f"新闻分析失败: {e}")
        return {
            "summary": title,
            "sentiment": "neutral",
            "sentiment_score": 0.5,
            "related_commodities": [],
            "importance": 1,
        }


async def generate_report(market_data: dict, news_data: list) -> str:
    news_text = "\n".join([f"- {n.get('title', '')}: {n.get('summary', '')}" for n in news_data[:10]])
    market_text = "\n".join([f"- {k}: {v}" for k, v in market_data.items()])

    prompt = f"""基于以下市场数据和新闻，生成一份简洁的大宗商品市场日报：

## 市场数据
{market_text}

## 今日要闻
{news_text}

请包含：市场概况、重点品种分析、地缘政治影响、后市展望。控制在800字以内。"""

    try:
        result = await chat_completion([
            {"role": "system", "content": "你是一个专业的大宗商品市场分析师，负责撰写每日市场报告。"},
            {"role": "user", "content": prompt},
        ])
        return result
    except Exception as e:
        logger.error(f"日报生成失败: {e}")
        return "日报生成失败，请稍后重试。"
