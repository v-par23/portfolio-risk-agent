def test_profile_round_trip(isolated_db):
    assert isolated_db.get_profile() == {"risk_tolerance": None, "notes": None, "updated_at": None}

    saved = isolated_db.save_profile("balanced", notes="prefers tech + broad index exposure")
    assert saved["risk_tolerance"] == "balanced"

    fetched = isolated_db.get_profile()
    assert fetched["risk_tolerance"] == "balanced"
    assert fetched["notes"] == "prefers tech + broad index exposure"


def test_save_profile_overwrites_previous(isolated_db):
    isolated_db.save_profile("aggressive", notes="first")
    isolated_db.save_profile("conservative", notes="changed my mind")

    fetched = isolated_db.get_profile()
    assert fetched["risk_tolerance"] == "conservative"
    assert fetched["notes"] == "changed my mind"


def test_watchlist_round_trip(isolated_db):
    assert isolated_db.get_watchlist() == []

    isolated_db.add_watchlist_ticker("nvda")  # lowercase on purpose
    isolated_db.add_watchlist_ticker("AAPL")
    assert isolated_db.get_watchlist() == ["NVDA", "AAPL"]


def test_watchlist_ignores_duplicates(isolated_db):
    isolated_db.add_watchlist_ticker("AAPL")
    isolated_db.add_watchlist_ticker("AAPL")
    assert isolated_db.get_watchlist() == ["AAPL"]


def test_holdings_round_trip(isolated_db):
    assert isolated_db.get_holdings() == []

    isolated_db.upsert_holding("AAPL", shares=10, cost_basis=150.0)
    holdings = isolated_db.get_holdings()
    assert holdings == [{"ticker": "AAPL", "shares": 10.0, "cost_basis": 150.0}]


def test_holdings_upsert_updates_existing_ticker(isolated_db):
    isolated_db.upsert_holding("AAPL", shares=10, cost_basis=150.0)
    isolated_db.upsert_holding("AAPL", shares=15, cost_basis=140.0)

    holdings = isolated_db.get_holdings()
    assert holdings == [{"ticker": "AAPL", "shares": 15.0, "cost_basis": 140.0}]
