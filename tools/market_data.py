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
