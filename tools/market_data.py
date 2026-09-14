"""Fetches and caches historical price data and fundamentals via yfinance."""
import os
import time
import pandas as pd
import yfinance as yf

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", ".cache")
CACHE_TTL_SECONDS = 6 * 60 * 60  # 6 hours


def _cache_path(key: str) -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    return os.path.join(CACHE_DIR, f"{key}.pkl")


def get_price_history(ticker: str, period: str = "5y") -> pd.DataFrame:
    """Daily OHLCV history for a ticker, cached on disk for CACHE_TTL_SECONDS."""
    key = f"{ticker.upper()}_{period}"
    path = _cache_path(key)
    if os.path.exists(path) and (time.time() - os.path.getmtime(path)) < CACHE_TTL_SECONDS:
        return pd.read_pickle(path)

    df = yf.Ticker(ticker).history(period=period, auto_adjust=False)
    if df.empty:
        raise ValueError(f"No price history found for ticker '{ticker}'")
    df.to_pickle(path)
    return df


def get_current_quote(ticker: str) -> dict:
    """Best-effort live/delayed quote snapshot: last price, day range, and change vs previous close."""
    fast = dict(yf.Ticker(ticker).fast_info)
    last_price = fast.get("lastPrice")
    if last_price is None:
        raise ValueError(f"No quote data found for ticker '{ticker}'")

    previous_close = fast.get("previousClose")
    change = last_price - previous_close if previous_close is not None else None
    pct_change = change / previous_close if change is not None and previous_close else None

    return {
        "ticker": ticker.upper(),
        "last_price": round(last_price, 2),
        "previous_close": round(previous_close, 2) if previous_close is not None else None,
        "change": round(change, 2) if change is not None else None,
        "pct_change": round(pct_change, 4) if pct_change is not None else None,
        "day_high": round(fast["dayHigh"], 2) if fast.get("dayHigh") is not None else None,
        "day_low": round(fast["dayLow"], 2) if fast.get("dayLow") is not None else None,
        "currency": fast.get("currency"),
        "exchange": fast.get("exchange"),
    }


def get_fundamentals(ticker: str) -> dict:
    """Best-effort snapshot of fundamentals: sector, market cap, dividend yield, beta (as reported)."""
    info = yf.Ticker(ticker).info
    return {
        "ticker": ticker.upper(),
        "name": info.get("shortName") or info.get("longName"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "market_cap": info.get("marketCap"),
        "dividend_yield": info.get("dividendYield"),
        "trailing_pe": info.get("trailingPE"),
        "reported_beta": info.get("beta"),
    }
