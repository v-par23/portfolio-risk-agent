import numpy as np
import pandas as pd
import pytest

import tools.portfolio as portfolio


def _prices_from_returns(returns):
    growth = np.cumprod(1 + np.asarray(returns))
    return pd.DataFrame({"Close": np.concatenate([[100.0], 100 * growth])})


@pytest.fixture
def fake_market(monkeypatch):
    n = 252
    rng = np.random.default_rng(42)
    data = {
        "A": _prices_from_returns(rng.normal(0.0008, 0.02, n)),
        "B": _prices_from_returns(rng.normal(0.0005, 0.015, n)),
        "BND": _prices_from_returns(rng.normal(0.0001, 0.002, n)),
    }
    monkeypatch.setattr(portfolio, "get_price_history", lambda ticker, period="5y": data[ticker])
    return data


@pytest.mark.parametrize("tolerance,expected_risky_fraction", [
    ("conservative", 0.30),
    ("balanced", 0.60),
    ("aggressive", 0.90),
])
def test_risky_fraction_matches_preset(fake_market, tolerance, expected_risky_fraction):
    result = portfolio.optimize_allocation(["A", "B"], risk_tolerance=tolerance)
    assert result["risky_fraction"] == pytest.approx(expected_risky_fraction)
    assert result["safe_fraction"] == pytest.approx(1 - expected_risky_fraction)


def test_default_safe_bucket_splits_evenly_between_bnd_and_cash(fake_market):
    result = portfolio.optimize_allocation(["A", "B"], risk_tolerance="conservative")
    allocation = result["allocation_pct"]
    expected_each_pct = (1 - 0.30) / 2 * 100  # 35% each
    assert allocation["BND"] == pytest.approx(expected_each_pct, abs=0.5)
    assert allocation["CASH"] == pytest.approx(expected_each_pct, abs=0.5)


def test_allocation_sums_to_roughly_100_percent(fake_market):
    result = portfolio.optimize_allocation(["A", "B"], risk_tolerance="balanced")
    assert sum(result["allocation_pct"].values()) == pytest.approx(100, abs=0.5)


def test_risky_weights_sum_to_risky_fraction(fake_market):
    result = portfolio.optimize_allocation(["A", "B"], risk_tolerance="aggressive")
    risky_total_pct = result["allocation_pct"]["A"] + result["allocation_pct"]["B"]
    assert risky_total_pct == pytest.approx(90, abs=0.5)


def test_custom_safe_assets_without_cash(fake_market):
    result = portfolio.optimize_allocation(["A", "B"], risk_tolerance="conservative", safe_assets=["BND"])
    assert "CASH" not in result["allocation_pct"]
    assert result["allocation_pct"]["BND"] == pytest.approx(70.0, abs=0.5)
