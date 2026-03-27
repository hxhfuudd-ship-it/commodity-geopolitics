import asyncio
from loguru import logger
from sqlalchemy import select

from app.database import async_session
from app.models.analysis import MacroIndicator
from app.data_sources.akshare_client import fetch_macro_indicator
from app.core.lock import acquire_lock, release_lock


# yfinance 指标放最后，之间加延迟防限流
MACRO_CODES = {
    "USDCNY": "人民币汇率",
    "US10Y": "美国10年期国债收益率",
    "CN10Y": "中国10年期国债收益率",
    "BDI": "波罗的海干散货指数",
    "DXY": "美元指数",
    "FED_RATE": "美联储利率",
}

# 使用 yfinance 的指标，需要加延迟
_YFINANCE_CODES = {"DXY", "FED_RATE"}


async def fetch_macro_data():
    lock_name = "lock:task:fetch_macro_data"
    if not await acquire_lock(lock_name, timeout=600):
        logger.debug("宏观数据拉取任务已被锁定，跳过")
        return

    try:
        async with async_session() as db:
            for code, name in MACRO_CODES.items():
                try:
                    # yfinance 指标之间加 5s 延迟防限流
                    if code in _YFINANCE_CODES:
                        await asyncio.sleep(5)

                    df = await fetch_macro_indicator(code)
                    if df is None or df.empty:
                        logger.info(f"宏观指标 {code} 无数据")
                        continue

                    count = 0
                    for _, row in df.iterrows():
                        d = row.get("date")
                        v = row.get("value")
                        if d is None or v is None:
                            continue

                        existing = await db.execute(
                            select(MacroIndicator).where(
                                MacroIndicator.indicator_code == code,
                                MacroIndicator.report_date == d,
                            )
                        )
                        if existing.scalar_one_or_none():
                            continue

                        db.add(MacroIndicator(
                            indicator_code=code,
                            indicator_name=name,
                            value=float(v),
                            report_date=d,
                        ))
                        count += 1

                    await db.commit()
                    if count:
                        logger.info(f"宏观指标 {code} 新增 {count} 条")

                except Exception as e:
                    logger.warning(f"宏观指标 {code} 拉取失败: {e}")
                    continue

    except Exception as e:
        logger.error(f"宏观数据拉取任务异常: {e}")
    finally:
        await release_lock(lock_name)
