"""Quick manual smoke test for the math/data layer -- no Anthropic API key required."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.risk import compute_risk_metrics
from tools.portfolio import optimize_allocation
from tools.compounding import simulate_growth, compare_reinvest_vs_cashout
from memory.store import save_profile, get_profile, add_watchlist_ticker, get_watchlist


def main():
    print("=== risk metrics: AAPL ===")
    print(compute_risk_metrics("AAPL", period="2y"))

    print("\n=== risk metrics: BND (should be low risk) ===")
    print(compute_risk_metrics("BND", period="2y"))

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


if __name__ == "__main__":
    main()
