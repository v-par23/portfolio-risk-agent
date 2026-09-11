"""Computes risk metrics for a ticker and classifies it into a risk tier."""
import numpy as np
from tools.market_data import get_price_history

BENCHMARK = "^GSPC"
RISK_FREE_RATE = 0.04  # rough approximation of a risk-free rate (e.g. short-term Treasury yield)


def _daily_returns(ticker: str, period: str):
    close = get_price_history(ticker, period)["Close"]
    return close.pct_change().dropna()


def compute_risk_metrics(ticker: str, period: str = "5y") -> dict:
    returns = _daily_returns(ticker, period)
    bench_returns = _daily_returns(BENCHMARK, period)

    aligned = returns.align(bench_returns, join="inner")
    r, b = aligned[0], aligned[1]

    annualized_volatility = float(r.std() * np.sqrt(252))
    annualized_return = float((1 + r.mean()) ** 252 - 1)
    beta = float(np.cov(r, b)[0, 1] / np.var(b)) if len(r) > 1 else float("nan")
    sharpe_ratio = (
        (annualized_return - RISK_FREE_RATE) / annualized_volatility
        if annualized_volatility > 0
        else float("nan")
    )

    cumulative = (1 + r).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = float(drawdown.min())

    tier, reason = _classify(annualized_volatility, beta, max_drawdown)

    return {
        "ticker": ticker.upper(),
        "period": period,
        "annualized_volatility": round(annualized_volatility, 4),
        "annualized_return": round(annualized_return, 4),
        "beta_vs_sp500": round(beta, 3),
        "sharpe_ratio": round(sharpe_ratio, 3),
        "max_drawdown": round(max_drawdown, 4),
        "risk_tier": tier,
        "risk_tier_reason": reason,
    }


def _classify(vol: float, beta: float, max_dd: float) -> tuple:
    if vol < 0.15 and abs(max_dd) < 0.20 and beta < 1.0:
        return "low", f"Low volatility ({vol:.0%}), beta below market ({beta:.2f}), shallow max drawdown ({max_dd:.0%})."
    if vol < 0.35 and abs(max_dd) < 0.45:
        return "medium", f"Moderate volatility ({vol:.0%}), beta {beta:.2f}, max drawdown {max_dd:.0%}."
    return "high", f"High volatility ({vol:.0%}) and/or steep max drawdown ({max_dd:.0%}), beta {beta:.2f}."
