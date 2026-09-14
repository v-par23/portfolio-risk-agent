import pytest

import tools.market_data as market_data


class _FakeTicker:
    def __init__(self, fast_info):
        self.fast_info = fast_info


def test_get_current_quote_computes_change_and_pct_change(monkeypatch):
    fake_info = {
        "lastPrice": 110.0,
        "previousClose": 100.0,
        "dayHigh": 112.0,
        "dayLow": 108.0,
        "currency": "USD",
        "exchange": "NMS",
    }
    monkeypatch.setattr(market_data.yf, "Ticker", lambda ticker: _FakeTicker(fake_info))

    result = market_data.get_current_quote("aapl")
    assert result["ticker"] == "AAPL"
    assert result["last_price"] == 110.0
    assert result["previous_close"] == 100.0
    assert result["change"] == 10.0
    assert result["pct_change"] == pytest.approx(0.10)
    assert result["day_high"] == 112.0
    assert result["day_low"] == 108.0
    assert result["currency"] == "USD"


def test_get_current_quote_raises_on_missing_price(monkeypatch):
    monkeypatch.setattr(market_data.yf, "Ticker", lambda ticker: _FakeTicker({}))

    with pytest.raises(ValueError):
        market_data.get_current_quote("BOGUS")
