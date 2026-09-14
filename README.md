# Portfolio Risk Agent

A command-line chat agent for exploring portfolio risk, allocation, and compounding --
backed by real historical market data and math, not guesses. Claude decides *which*
calculation your question needs; the actual numbers come from `numpy`/`scipy`/`yfinance`.

**Educational tool only.** All data is historical, all projections are estimates, and
none of this is financial advice. Consult a licensed financial advisor before acting on
it with real money.

## What it can do

Ask it things like:
- "Is TSLA risky? How does it compare to BND?"
- "Split $10k across AAPL, MSFT, and bonds for a balanced risk tolerance."
- "What's AAPL trading at right now?"
- "If I reinvest dividends vs. cash them out on $10k at 8%/yr for 20 years, what's the difference?"
- "I own 10 shares of AAPL at $150 cost basis -- remember that."

Available tools:

| Tool | What it does |
|---|---|
| `get_stock_risk` | Historical volatility, beta vs. S&P 500, Sharpe ratio, max drawdown, risk tier |
| `get_fundamentals` | Sector, market cap, dividend yield, P/E |
| `get_live_quote` | Live/delayed price, change vs. previous close, day range |
| `optimize_portfolio` | Max-Sharpe risky bundle blended with a safe bucket, sized by risk tolerance |
| `simulate_compounding` | Growth projection with contributions and reinvested/cashed-out dividends |
| `compare_reinvest_vs_cashout` | Runs both compounding scenarios and reports the dollar gap |
| `save_user_profile` / `get_user_profile` | Persists risk tolerance + notes across sessions |
| `add_to_watchlist` / `get_watchlist` | Persists a ticker watchlist |
| `record_holding` / `get_holdings` | Persists actual positions (ticker/shares/cost basis) |

## Setup

```bash
cd portfolio-risk-agent
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env   # then edit .env and add your real ANTHROPIC_API_KEY
```

## Running it

```bash
.venv/bin/python cli.py
```

Type your question, or `exit`/`quit` to leave.

## Running the tests

```bash
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest tests/ -v
```

These are fully isolated: they mock market data and use a throwaway SQLite file, so they
run in under a second with no network calls and never touch your real `memory.db`.

For a manual, human-run check against **live** yfinance data and your real local database:

```bash
.venv/bin/python tests/manual_smoke_check.py
```

## Project layout

```
cli.py                 REPL entry point
agent/loop.py           Hand-rolled Claude tool-use loop (no agent framework)
agent/tool_schemas.py   Tool definitions + dispatch table
tools/risk.py           Historical risk metrics
tools/portfolio.py      Mean-variance (max-Sharpe) allocation
tools/compounding.py    Growth simulations
tools/market_data.py    yfinance access (historical + live quotes), disk-cached
memory/store.py         SQLite-backed profile/watchlist/holdings persistence
tests/                  Automated pytest suite + manual_smoke_check.py
```

## Notes

- Historical price data is cached on disk (`.cache/`, 6-hour TTL) to avoid hammering
  `yfinance` on every request.
- Persistent user data (profile, watchlist, holdings) lives in `.data/memory.db`, gitignored.
- `PORTFOLIO_AGENT_MODEL` env var overrides the model (defaults to `claude-sonnet-5`).
