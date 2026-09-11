"""JSON-schema tool definitions passed to the Claude API, and the dispatch table behind them."""
from tools.market_data import get_fundamentals
from tools.risk import compute_risk_metrics
from tools.portfolio import optimize_allocation
from tools.compounding import simulate_growth, compare_reinvest_vs_cashout
from memory.store import (
    save_profile,
    get_profile,
    add_watchlist_ticker,
    get_watchlist,
)

TOOLS = [
    {
        "name": "get_stock_risk",
        "description": (
            "Computes historical risk metrics for a single stock/ETF ticker "
            "(annualized volatility, beta vs S&P 500, Sharpe ratio, max drawdown) "
            "and classifies it as low/medium/high risk."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Stock/ETF ticker symbol, e.g. AAPL"},
                "period": {
                    "type": "string",
                    "description": "Lookback window, e.g. '1y', '5y', '10y'. Defaults to '5y'.",
                },
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "get_fundamentals",
        "description": "Fetches basic fundamentals for a ticker: sector, market cap, dividend yield, P/E.",
        "input_schema": {
            "type": "object",
            "properties": {"ticker": {"type": "string"}},
            "required": ["ticker"],
        },
    },
    {
        "name": "optimize_portfolio",
        "description": (
            "Suggests a full portfolio allocation: splits between a max-Sharpe-weighted bundle "
            "of the given risky tickers and a safe bucket (bond ETFs / cash), sized according to "
            "risk_tolerance. Returns allocation percentages and the bundle's expected return/volatility/Sharpe."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "risky_tickers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tickers the user wants considered for the risky portion of the portfolio.",
                },
                "risk_tolerance": {
                    "type": "string",
                    "description": "'conservative', 'balanced', or 'aggressive'.",
                    "enum": ["conservative", "balanced", "aggressive"],
                },
                "safe_assets": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tickers for the safe bucket, e.g. ['BND']. Include 'CASH' to hold part as cash. Defaults to ['BND', 'CASH'].",
                },
            },
            "required": ["risky_tickers", "risk_tolerance"],
        },
    },
    {
        "name": "simulate_compounding",
        "description": (
            "Projects portfolio growth over time given an expected annual return, optional monthly "
            "contributions, and a dividend yield -- either reinvested (compounding) or paid out as cash."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "principal": {"type": "number", "description": "Starting investment amount."},
                "annual_return": {
                    "type": "number",
                    "description": "Expected annual price-appreciation rate as a decimal, e.g. 0.08 for 8%.",
                },
                "years": {"type": "integer", "description": "Number of years to project."},
                "monthly_contribution": {"type": "number", "description": "Additional amount invested each month. Defaults to 0."},
                "dividend_yield": {"type": "number", "description": "Annual dividend yield as a decimal. Defaults to 0."},
                "reinvest_dividends": {
                    "type": "boolean",
                    "description": "Whether dividends are reinvested (compounding) or cashed out. Defaults to true.",
                },
            },
            "required": ["principal", "annual_return", "years"],
        },
    },
    {
        "name": "compare_reinvest_vs_cashout",
        "description": (
            "Runs the compounding simulation both ways (reinvesting dividends vs. cashing them out) "
            "and reports the dollar gap between the two -- illustrates why letting gains keep working "
            "compounds faster than withdrawing them."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "principal": {"type": "number"},
                "annual_return": {"type": "number"},
                "years": {"type": "integer"},
                "monthly_contribution": {"type": "number", "description": "Defaults to 0."},
                "dividend_yield": {"type": "number", "description": "Defaults to 0.02."},
            },
            "required": ["principal", "annual_return", "years"],
        },
    },
    {
        "name": "save_user_profile",
        "description": "Persists the user's stated risk tolerance and notes so future sessions remember it.",
        "input_schema": {
            "type": "object",
            "properties": {
                "risk_tolerance": {"type": "string", "enum": ["conservative", "balanced", "aggressive"]},
                "notes": {"type": "string"},
            },
            "required": ["risk_tolerance"],
        },
    },
    {
        "name": "get_user_profile",
        "description": "Reads back the user's previously saved risk tolerance and notes, if any.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "add_to_watchlist",
        "description": "Adds a ticker to the user's persisted watchlist.",
        "input_schema": {
            "type": "object",
            "properties": {"ticker": {"type": "string"}},
            "required": ["ticker"],
        },
    },
    {
        "name": "get_watchlist",
        "description": "Reads back the user's persisted watchlist.",
        "input_schema": {"type": "object", "properties": {}},
    },
]


def _dispatch_get_stock_risk(args):
    return compute_risk_metrics(args["ticker"], args.get("period", "5y"))


def _dispatch_get_fundamentals(args):
    return get_fundamentals(args["ticker"])


def _dispatch_optimize_portfolio(args):
    return optimize_allocation(
        risky_tickers=args["risky_tickers"],
        risk_tolerance=args["risk_tolerance"],
        safe_assets=args.get("safe_assets"),
    )


def _dispatch_simulate_compounding(args):
    return simulate_growth(
        principal=args["principal"],
        annual_return=args["annual_return"],
        years=args["years"],
        monthly_contribution=args.get("monthly_contribution", 0.0),
        dividend_yield=args.get("dividend_yield", 0.0),
        reinvest_dividends=args.get("reinvest_dividends", True),
    )


def _dispatch_compare_reinvest_vs_cashout(args):
    return compare_reinvest_vs_cashout(
        principal=args["principal"],
        annual_return=args["annual_return"],
        years=args["years"],
        monthly_contribution=args.get("monthly_contribution", 0.0),
        dividend_yield=args.get("dividend_yield", 0.02),
    )


def _dispatch_save_user_profile(args):
    return save_profile(args["risk_tolerance"], args.get("notes"))


def _dispatch_get_user_profile(_args):
    return get_profile()


def _dispatch_add_to_watchlist(args):
    return {"watchlist": add_watchlist_ticker(args["ticker"])}


def _dispatch_get_watchlist(_args):
    return {"watchlist": get_watchlist()}


DISPATCH = {
    "get_stock_risk": _dispatch_get_stock_risk,
    "get_fundamentals": _dispatch_get_fundamentals,
    "optimize_portfolio": _dispatch_optimize_portfolio,
    "simulate_compounding": _dispatch_simulate_compounding,
    "compare_reinvest_vs_cashout": _dispatch_compare_reinvest_vs_cashout,
    "save_user_profile": _dispatch_save_user_profile,
    "get_user_profile": _dispatch_get_user_profile,
    "add_to_watchlist": _dispatch_add_to_watchlist,
    "get_watchlist": _dispatch_get_watchlist,
}
