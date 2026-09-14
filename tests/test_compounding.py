import pytest

from tools.compounding import simulate_growth, compare_reinvest_vs_cashout


def test_simulate_growth_no_contributions_no_dividends():
    # $10k at 10%/yr for 1 year, nothing else going on -> should just grow by ~10%.
    result = simulate_growth(principal=10000, annual_return=0.10, years=1)
    assert result["years"] == 1
    assert result["total_contributed"] == 10000
    assert result["final_balance"] == pytest.approx(11000, rel=1e-3)
    assert result["cash_collected_not_reinvested"] == 0.0
    assert len(result["yearly_snapshots"]) == 1


def test_simulate_growth_reinvest_beats_cashout():
    # Same inputs, only difference is what happens to dividends -- reinvesting should
    # never leave you worse off than cashing them out.
    kwargs = dict(principal=10000, annual_return=0.08, years=10, monthly_contribution=100, dividend_yield=0.03)
    reinvested = simulate_growth(**kwargs, reinvest_dividends=True)
    cashed_out = simulate_growth(**kwargs, reinvest_dividends=False)

    assert reinvested["final_balance"] > cashed_out["final_balance"]
    assert cashed_out["cash_collected_not_reinvested"] > 0
    assert reinvested["cash_collected_not_reinvested"] == 0.0
    # Both should have contributed the same principal + monthly amounts.
    assert reinvested["total_contributed"] == cashed_out["total_contributed"]


def test_simulate_growth_zero_return_just_tracks_contributions():
    result = simulate_growth(principal=1000, annual_return=0.0, years=2, monthly_contribution=50)
    assert result["total_contributed"] == 1000 + 50 * 24
    assert result["final_balance"] == pytest.approx(result["total_contributed"], rel=1e-9)


def test_compare_reinvest_vs_cashout_reports_positive_advantage():
    comparison = compare_reinvest_vs_cashout(principal=10000, annual_return=0.08, years=20, monthly_contribution=200)
    assert comparison["advantage_of_reinvesting"] > 0
    assert comparison["reinvested_final_balance"] > comparison["cashed_out_final_balance_plus_cash"]
    # The comparison's own totals should match what simulate_growth produces standalone.
    assert comparison["reinvested_detail"]["final_balance"] == comparison["reinvested_final_balance"]
