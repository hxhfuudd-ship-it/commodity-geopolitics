import asyncio
from typing import Optional
from datetime import datetime
import pandas as pd
from loguru import logger


async def _run_sync(func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: func(*args, **kwargs))


async def fetch_commodity_daily(
    akshare_symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None
) -> pd.DataFrame:
    """获取期货日线数据，自动区分内盘/外盘"""
    try:
        import akshare as ak

        # 外盘品种用 futures_foreign_hist
        foreign_symbols = {"CL", "NG"}

        def _fetch():
            try:
                if akshare_symbol in foreign_symbols:
                    df = ak.futures_foreign_hist(symbol=akshare_symbol)
                    if df is not None and not df.empty:
                        df["date"] = pd.to_datetime(df["date"]).dt.date
                        if "position" in df.columns:
                            df = df.rename(columns={"position": "open_interest"})
                        if "close" in df.columns and len(df) > 1:
                            df["change_pct"] = df["close"].pct_change() * 100
                        else:
                            df["change_pct"] = 0.0
                        return df
                    return pd.DataFrame()

                # 内盘品种用 futures_main_sina
                df = ak.futures_main_sina(symbol=akshare_symbol)
                if df is not None and not df.empty:
                    col_map = {
                        "日期": "date", "开盘价": "open", "最高价": "high",
                        "最低价": "low", "收盘价": "close", "成交量": "volume",
                        "持仓量": "open_interest", "动态结算价": "settle",
                    }
                    df = df.rename(columns=col_map)
                    if "date" in df.columns:
                        df["date"] = pd.to_datetime(df["date"]).dt.date
                    if "close" in df.columns and len(df) > 1:
                        df["change_pct"] = df["close"].pct_change() * 100
                    else:
                        df["change_pct"] = 0.0
                    return df
                return pd.DataFrame()
            except Exception as e:
                logger.warning(f"主接口失败 {akshare_symbol}: {e}")
                return pd.DataFrame()

        result = await _run_sync(_fetch)
        if result is not None and not result.empty:
            if start_date and "date" in result.columns:
                result = result[result["date"] >= pd.to_datetime(start_date).date()]
            if end_date and "date" in result.columns:
                result = result[result["date"] <= pd.to_datetime(end_date).date()]
        return result if result is not None else pd.DataFrame()
    except Exception as e:
        logger.error(f"AKShare 日线数据获取失败 {akshare_symbol}: {e}")
        return pd.DataFrame()


# akshare_symbol -> 东方财富 futures_zh_realtime 中文品种名映射
_EASTMONEY_NAME_MAP = {
    "AU0": "黄金", "AG0": "白银", "CU0": "沪铜", "AL0": "沪铝",
    "NI0": "沪镍", "I0": "铁矿石", "SC0": "原油",
    "A0": "豆一", "M0": "豆粕", "Y0": "豆油", "P0": "棕榈",
    "C0": "玉米", "CF0": "棉花", "SR0": "白糖", "RU0": "橡胶",
    "TA0": "PTA", "MA0": "郑醇", "PP0": "PP",
    "FU0": "燃油", "PG0": "液化石油气",
}


async def fetch_realtime_price(akshare_symbol: str) -> dict:
    """获取期货实时价格，内盘优先东方财富接口，失败回退新浪；外盘用 yfinance"""
    try:
        # 外盘品种用 yfinance
        _yfinance_map = {"CL": "CL=F", "NG": "NG=F", "BZ_F": "BZ=F"}
        if akshare_symbol in _yfinance_map:
            return await _fetch_yfinance_realtime(_yfinance_map[akshare_symbol])

        # ZC0 动力煤已退市，跳过实时（走 fallback）
        if akshare_symbol == "ZC0":
            return {}

        import akshare as ak

        # 优先使用东方财富接口（云服务器不被封）
        em_name = _EASTMONEY_NAME_MAP.get(akshare_symbol)
        if em_name:
            result = await _fetch_eastmoney_realtime(ak, akshare_symbol, em_name)
            if result and result.get("price"):
                return result

        # 回退到新浪接口（本地可用，云服务器可能被封）
        def _fetch_sina():
            try:
                df = ak.futures_zh_spot(symbol=akshare_symbol)
                if df is not None and not df.empty:
                    row = df.iloc[0]
                    price = float(row.get("current_price", 0))
                    settle = float(row.get("last_settle_price", 0))
                    change_pct = ((price - settle) / settle * 100) if settle > 0 else 0.0
                    return {
                        "price": price,
                        "change_pct": round(change_pct, 4),
                        "open": float(row.get("open", 0)),
                        "volume": int(row.get("volume", 0)),
                        "settle": settle,
                        "open_interest": int(row.get("hold", 0)),
                        "prev_close": float(row.get("last_close", 0)),
                        "updated_at": datetime.now().isoformat(),
                    }
            except Exception as e:
                logger.debug(f"新浪实时价格获取失败 {akshare_symbol}: {e}")
            return {}

        return await _run_sync(_fetch_sina)
    except Exception as e:
        logger.error(f"实时价格获取失败 {akshare_symbol}: {e}")
        return {}


async def _fetch_eastmoney_realtime(ak, akshare_symbol: str, em_name: str) -> dict:
    """通过东方财富 futures_zh_realtime 获取实时价格"""
    def _fetch():
        try:
            df = ak.futures_zh_realtime(symbol=em_name)
            if df is None or df.empty:
                return {}
            # 匹配连续合约（symbol == akshare_symbol）
            match = df[df["symbol"] == akshare_symbol]
            if match.empty:
                match = df.head(1)
            row = match.iloc[0]
            price = float(row.get("trade", 0))
            presettle = float(row.get("presettlement", 0) or row.get("prevsettlement", 0) or 0)
            change_pct = float(row.get("changepercent", 0)) * 100
            return {
                "price": price,
                "change_pct": round(change_pct, 4),
                "open": float(row.get("open", 0)),
                "volume": int(float(row.get("volume", 0))),
                "settle": float(row.get("settlement", 0)),
                "open_interest": int(float(row.get("position", 0))),
                "prev_close": float(row.get("preclose", 0)),
                "updated_at": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.debug(f"东方财富实时价格获取失败 {em_name}({akshare_symbol}): {e}")
            return {}
    return await _run_sync(_fetch)


async def _fetch_yfinance_realtime(ticker: str) -> dict:
    """用 yfinance 获取外盘期货实时价格"""
    def _fetch():
        try:
            import yfinance as yf
            t = yf.Ticker(ticker)
            info = t.fast_info
            price = info.last_price
            prev = info.previous_close
            if price is None:
                return {}
            change_pct = ((price - prev) / prev * 100) if prev else 0.0
            return {
                "price": round(float(price), 4),
                "change_pct": round(change_pct, 4),
                "open": round(float(info.open), 4) if info.open else 0,
                "volume": int(info.last_volume) if info.last_volume else 0,
                "settle": 0,
                "open_interest": 0,
                "prev_close": round(float(prev), 4) if prev else 0,
                "updated_at": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.debug(f"yfinance 实时价格获取失败 {ticker}: {e}")
            return {}
    return await _run_sync(_fetch)


async def fetch_macro_indicator(indicator_code: str) -> pd.DataFrame:
    """获取宏观指标数据，返回统一格式 DataFrame (date, value)"""
    try:
        import akshare as ak

        def _fetch_dxy():
            """美元指数 (ICE DXY) — Yahoo Finance"""
            import yfinance as yf
            df = yf.download('DX-Y.NYB', start='2008-01-01', progress=False)
            if df is None or df.empty:
                return pd.DataFrame()
            df = df.reset_index()
            # yfinance returns MultiIndex columns, flatten
            if hasattr(df.columns, 'levels'):
                df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
            df = df.rename(columns={"Date": "date", "Close": "value"})
            df = df[["date", "value"]].dropna(subset=["value"])
            df["date"] = pd.to_datetime(df["date"]).dt.date
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
            return df.dropna().sort_values("date").reset_index(drop=True)

        def _fetch_usdcny():
            """人民币汇率 USD/CNY — 央行中间价"""
            df = ak.currency_boc_sina(symbol="美元", start_date="20080101", end_date=datetime.now().strftime("%Y%m%d"))
            if df is None or df.empty:
                return pd.DataFrame()
            df = df.rename(columns={"日期": "date", "央行中间价": "value"})
            df = df[["date", "value"]].dropna(subset=["value"])
            df["date"] = pd.to_datetime(df["date"]).dt.date
            df["value"] = pd.to_numeric(df["value"], errors="coerce") / 100  # 央行报价单位是分，转换为元
            return df.dropna().sort_values("date").reset_index(drop=True)

        def _fetch_us10y():
            """美国10年期国债收益率 — 中国债券信息网"""
            df = ak.bond_zh_us_rate(start_date="20080101")
            if df is None or df.empty:
                return pd.DataFrame()
            df = df.rename(columns={"日期": "date", "美国国债收益率10年": "value"})
            df = df[["date", "value"]].dropna(subset=["value"])
            df["date"] = pd.to_datetime(df["date"]).dt.date
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
            return df.dropna().sort_values("date").reset_index(drop=True)

        def _fetch_cn10y():
            """中国10年期国债收益率 — 中国债券信息网"""
            df = ak.bond_zh_us_rate(start_date="20080101")
            if df is None or df.empty:
                return pd.DataFrame()
            df = df.rename(columns={"日期": "date", "中国国债收益率10年": "value"})
            df = df[["date", "value"]].dropna(subset=["value"])
            df["date"] = pd.to_datetime(df["date"]).dt.date
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
            return df.dropna().sort_values("date").reset_index(drop=True)

        def _fetch_fed_rate():
            """美联储利率 — 13周美国国债收益率 (^IRX)，日度"""
            import yfinance as yf
            df = yf.download('^IRX', start='2008-01-01', progress=False)
            if df is None or df.empty:
                return pd.DataFrame()
            df = df.reset_index()
            if hasattr(df.columns, 'levels'):
                df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
            df = df.rename(columns={"Date": "date", "Close": "value"})
            df = df[["date", "value"]].dropna(subset=["value"])
            df["date"] = pd.to_datetime(df["date"]).dt.date
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
            return df.dropna().sort_values("date").reset_index(drop=True)

        def _fetch_bdi():
            """波罗的海干散货指数 — 已有数据，增量更新"""
            return pd.DataFrame()

        indicator_map = {
            "DXY": _fetch_dxy,
            "USDCNY": _fetch_usdcny,
            "US10Y": _fetch_us10y,
            "CN10Y": _fetch_cn10y,
            "FED_RATE": _fetch_fed_rate,
            "BDI": _fetch_bdi,
        }

        func = indicator_map.get(indicator_code)
        if func is None:
            return pd.DataFrame()

        return await _run_sync(func)
    except Exception as e:
        logger.error(f"AKShare 宏观指标获取失败 {indicator_code}: {e}")
        return pd.DataFrame()


async def fetch_cftc_positions(akshare_symbol: str) -> pd.DataFrame:
    try:
        import akshare as ak

        def _fetch():
            try:
                df = ak.futures_cot_detail(symbol=akshare_symbol)
                return df
            except Exception:
                return pd.DataFrame()

        return await _run_sync(_fetch)
    except Exception as e:
        logger.error(f"AKShare CFTC 数据获取失败 {akshare_symbol}: {e}")
        return pd.DataFrame()
