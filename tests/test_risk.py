import numpy as np
import pandas as pd
import pytest

import tools.risk as risk


def _prices_from_returns(returns):
    """Builds a Close-price series that will pct_change() back into exactly `returns`."""
    growth = np.cumprod(1 + np.asarray(returns))
    return pd.DataFrame({"Close": np.concatenate([[100.0], 100 * growth])})


def test_low_volatility_ticker_classified_low(monkeypatch):
    n = 300
    bench_returns = np.random.default_rng(1).normal(0, 0.01, n)
    ticker_returns = np.full(n, 0.0003)  # essentially flat and uncorrelated with the benchmark

    prices = {"^GSPC": _prices_from_returns(bench_returns), "STABLECO": _prices_from_returns(ticker_returns)}
    monkeypatch.setattr(risk, "get_price_history", lambda ticker, period: prices[ticker])

    result = risk.compute_risk_metrics("STABLECO", period="1y")
    assert result["risk_tier"] == "low"
    assert result["annualized_volatility"] < 0.01


def test_high_volatility_ticker_classified_high(monkeypatch):
    n = 252
    bench_returns = np.random.default_rng(2).normal(0, 0.01, n)
    ticker_returns = np.array([0.10 if i % 2 == 0 else -0.10 for i in range(n)])

    prices = {"^GSPC": _prices_from_returns(bench_returns), "WILDCO": _prices_from_returns(ticker_returns)}
    monkeypatch.setattr(risk, "get_price_history", lambda ticker, period: prices[ticker])

    result = risk.compute_risk_metrics("WILDCO", period="1y")
    assert result["risk_tier"] == "high"
    assert result["annualized_volatility"] > 0.35


def test_beta_matches_known_scale_factor(monkeypatch):
    # If a ticker's returns are exactly 1.5x the benchmark's every day, its beta must be 1.5 --
    # a property of covariance/variance that holds regardless of the actual data.
    n = 252
    bench_returns = np.random.default_rng(3).normal(0.0005, 0.01, n)
    ticker_returns = 1.5 * bench_returns

    prices = {"^GSPC": _prices_from_returns(bench_returns), "SCALEDCO": _prices_from_returns(ticker_returns)}
    monkeypatch.setattr(risk, "get_price_history", lambda ticker, period: prices[ticker])

    result = risk.compute_risk_metrics("SCALEDCO", period="1y")
    assert result["beta_vs_sp500"] == pytest.approx(1.5, abs=0.01)
