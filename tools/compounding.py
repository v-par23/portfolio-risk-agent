"""Models the effect of reinvesting gains/dividends vs. cashing them out over time."""


def simulate_growth(
    principal: float,
    annual_return: float,
    years: int,
    monthly_contribution: float = 0.0,
    dividend_yield: float = 0.0,
    reinvest_dividends: bool = True,
) -> dict:
    """Month-by-month compounding simulation.

    annual_return: expected annual price-appreciation rate (e.g. from optimize_allocation).
    dividend_yield: annual dividend yield paid out on top of price appreciation.
    reinvest_dividends: if True, dividends are added back to the balance and keep compounding
        (this is the "successful investors let money keep working" behavior). If False,
        dividends are paid out as cash and tracked separately, not compounded.
    """
    monthly_growth_rate = (1 + annual_return) ** (1 / 12) - 1
    monthly_dividend_rate = dividend_yield / 12

    balance = principal
    total_contributed = principal
    cash_collected = 0.0
    yearly_snapshots = []

    for month in range(1, years * 12 + 1):
        balance += monthly_contribution
        total_contributed += monthly_contribution

        balance *= (1 + monthly_growth_rate)
        dividend_amount = balance * monthly_dividend_rate
        if reinvest_dividends:
            balance += dividend_amount
        else:
            cash_collected += dividend_amount

        if month % 12 == 0:
            yearly_snapshots.append({
                "year": month // 12,
                "balance": round(balance, 2),
                "cash_collected_to_date": round(cash_collected, 2),
            })

    return {
        "years": years,
        "reinvest_dividends": reinvest_dividends,
        "final_balance": round(balance, 2),
        "total_contributed": round(total_contributed, 2),
        "total_growth": round(balance - total_contributed, 2),
        "cash_collected_not_reinvested": round(cash_collected, 2),
        "yearly_snapshots": yearly_snapshots,
    }


def compare_reinvest_vs_cashout(
    principal: float,
    annual_return: float,
    years: int,
    monthly_contribution: float = 0.0,
    dividend_yield: float = 0.02,
) -> dict:
    """Runs the simulation both ways to quantify the gap reinvestment makes over time."""
    reinvested = simulate_growth(
        principal, annual_return, years, monthly_contribution, dividend_yield, reinvest_dividends=True
    )
    cashed_out = simulate_growth(
        principal, annual_return, years, monthly_contribution, dividend_yield, reinvest_dividends=False
    )
    reinvested_total = reinvested["final_balance"]
    cashed_out_total = cashed_out["final_balance"] + cashed_out["cash_collected_not_reinvested"]

    return {
        "years": years,
        "reinvested_final_balance": reinvested_total,
        "cashed_out_final_balance_plus_cash": round(cashed_out_total, 2),
        "advantage_of_reinvesting": round(reinvested_total - cashed_out_total, 2),
        "reinvested_detail": reinvested,
        "cashed_out_detail": cashed_out,
    }
