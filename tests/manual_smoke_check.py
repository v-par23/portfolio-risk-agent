"""Manual, human-run check against LIVE yfinance data and the real local memory.db.

Not part of the automated pytest suite (see tests/test_*.py for that) -- this hits the
network and writes real rows into your memory.db, so run it by hand when you want to
eyeball real output, e.g.: .venv/bin/python tests/manual_smoke_check.py

No Anthropic API key required (only exercises the math/data layer, not the LLM loop).
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.risk import compute_risk_metrics
from tools.market_data import get_current_quote
from tools.portfolio import optimize_allocation
from tools.compounding import simulate_growth, compare_reinvest_vs_cashout
from memory.store import (
    save_profile,
    get_profile,
    add_watchlist_ticker,
    get_watchlist,
    upsert_holding,
    get_holdings,
)


def main():
    print("=== risk metrics: AAPL ===")
    print(compute_risk_metrics("AAPL", period="2y"))

    print("\n=== risk metrics: BND (should be low risk) ===")
    print(compute_risk_metrics("BND", period="2y"))

    print("\n=== live quote: AAPL ===")
    print(get_current_quote("AAPL"))

    print("\n=== portfolio optimization: AAPL, TSLA, MSFT / balanced ===")
    print(optimize_allocation(["AAPL", "TSLA", "MSFT"], risk_tolerance="balanced"))

    print("\n=== compounding: $10k, 8%/yr, 20yr, reinvest dividends ===")
    print(simulate_growth(10000, 0.08, 20, monthly_contribution=200, dividend_yield=0.02))

    print("\n=== reinvest vs cash-out comparison ===")
    print(compare_reinvest_vs_cashout(10000, 0.08, 20, monthly_contribution=200))

    print("\n=== memory store ===")
    print(save_profile("balanced", notes="prefers tech + broad index exposure"))
    print(get_profile())
    print(add_watchlist_ticker("NVDA"))
    print(get_watchlist())
    print(upsert_holding("AAPL", shares=10, cost_basis=150.0))
    print(get_holdings())


if __name__ == "__main__":
    main()
