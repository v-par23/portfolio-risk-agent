"""Mean-variance portfolio allocation: splits a risky-asset bundle against safe assets/cash."""
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from tools.market_data import get_price_history
from tools.risk import RISK_FREE_RATE

CASH_RETURN = 0.02  # approximate money-market / high-yield-savings yield
CASH_TOKEN = "CASH"

RISK_TOLERANCE_PRESETS = {
    "conservative": 0.30,
    "balanced": 0.60,
    "aggressive": 0.90,
}


def _annualized_returns_and_cov(tickers: list, period: str = "5y"):
    price_frames = {t: get_price_history(t, period)["Close"] for t in tickers}
    prices = pd.DataFrame(price_frames).dropna(how="any")
    returns = prices.pct_change().dropna()
    mean_returns = returns.mean() * 252
    cov_matrix = returns.cov() * 252
    return mean_returns, cov_matrix


def _max_sharpe_weights(mean_returns: pd.Series, cov_matrix: pd.DataFrame) -> dict:
    n = len(mean_returns)
    if n == 1:
        return {mean_returns.index[0]: 1.0}

    def neg_sharpe(w):
        port_return = np.dot(w, mean_returns)
        port_vol = np.sqrt(w @ cov_matrix.values @ w)
        return -(port_return - RISK_FREE_RATE) / port_vol if port_vol > 0 else 1e6

    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
    bounds = [(0.0, 1.0)] * n
    x0 = np.repeat(1 / n, n)
    result = minimize(neg_sharpe, x0, method="SLSQP", bounds=bounds, constraints=constraints)
    weights = result.x if result.success else x0
    return {t: round(float(w), 4) for t, w in zip(mean_returns.index, weights)}


def optimize_allocation(
    risky_tickers: list,
    risk_tolerance="balanced",
    safe_assets: list = None,
    period: str = "5y",
) -> dict:
    """Suggests a full portfolio split: risky bundle (max-Sharpe weighted) vs. safe assets/cash.

    risk_tolerance: "conservative" | "balanced" | "aggressive", or a float 0-1
        (fraction of the portfolio allocated to risky assets).
    safe_assets: tickers for the safe bucket, e.g. ["BND"]. Include the literal
        string "CASH" to hold part of the safe bucket as uninvested cash.
    """
    safe_assets = safe_assets or ["BND", CASH_TOKEN]
    risky_fraction = (
        risk_tolerance if isinstance(risk_tolerance, (int, float))
        else RISK_TOLERANCE_PRESETS.get(risk_tolerance, 0.60)
    )
    risky_fraction = min(max(risky_fraction, 0.0), 1.0)
    safe_fraction = 1 - risky_fraction

    risky_mean, risky_cov = _annualized_returns_and_cov(risky_tickers, period)
    risky_weights = _max_sharpe_weights(risky_mean, risky_cov)

    real_safe_tickers = [t for t in safe_assets if t != CASH_TOKEN]
    has_cash = CASH_TOKEN in safe_assets
    n_safe_buckets = len(real_safe_tickers) + (1 if has_cash else 0)
    safe_bucket_share = safe_fraction / n_safe_buckets if n_safe_buckets else 0

    allocation = {t: round(w * risky_fraction, 4) for t, w in risky_weights.items()}
    for t in real_safe_tickers:
        allocation[t] = allocation.get(t, 0) + round(safe_bucket_share, 4)
    if has_cash:
        allocation[CASH_TOKEN] = allocation.get(CASH_TOKEN, 0) + round(safe_bucket_share, 4)

    all_tickers = list(risky_weights.keys()) + real_safe_tickers
    combined_mean, combined_cov = _annualized_returns_and_cov(all_tickers, period) if all_tickers else (pd.Series(dtype=float), pd.DataFrame())
    w_vector = np.array([allocation.get(t, 0.0) for t in combined_mean.index])
    portfolio_return = float(np.dot(w_vector, combined_mean)) + allocation.get(CASH_TOKEN, 0.0) * CASH_RETURN
    portfolio_vol = float(np.sqrt(w_vector @ combined_cov.values @ w_vector)) if len(combined_mean) else 0.0
    sharpe = (portfolio_return - RISK_FREE_RATE) / portfolio_vol if portfolio_vol > 0 else float("nan")

    return {
        "risk_tolerance": risk_tolerance,
        "risky_fraction": round(risky_fraction, 3),
        "safe_fraction": round(safe_fraction, 3),
        "allocation_pct": {k: round(v * 100, 2) for k, v in allocation.items()},
        "expected_annual_return": round(portfolio_return, 4),
        "expected_annual_volatility": round(portfolio_vol, 4),
        "expected_sharpe_ratio": round(sharpe, 3) if sharpe == sharpe else None,
    }
