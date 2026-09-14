"""Hand-rolled tool-use loop against OpenAI's Chat Completions API: no agent framework, just the raw message/tool cycle."""
import json
import os
import traceback

from openai import OpenAI

from agent.tool_schemas import TOOLS, DISPATCH

MODEL = os.environ.get("PORTFOLIO_AGENT_MODEL", "gpt-4o-mini")
MAX_TOKENS = 2048
MAX_TOOL_ROUNDS = 8

SYSTEM_PROMPT = """You are a portfolio risk-analysis and education agent. You help the user \
understand which stocks are risky, how to spread money between risky and safe assets, and how \
reinvesting gains/dividends compounds over time versus cashing them out.

You have tools for: historical risk metrics, fundamentals, live/delayed price quotes, portfolio \
allocation (max-Sharpe risky bundle blended with a safe bucket), and compounding simulations \
(reinvest vs. cash out). You also have simple persistent memory for the user's risk tolerance, \
watchlist, and actual holdings (ticker/shares/cost basis) -- use it so you don't have to re-ask \
basic preferences every session. Check get_holdings before suggesting a new allocation so advice \
accounts for what the user already owns, and call record_holding whenever the user tells you what \
they hold.

Always use the tools to get real numbers rather than guessing at metrics or projections. When you \
present a recommendation, briefly explain the reasoning (e.g. why a ticker is high risk, why a \
given split matches the stated risk tolerance).

This is an educational/simulation tool. All data is historical and all projections are estimates, \
not guarantees. Always make clear this is not financial advice and the user should consult a \
licensed financial advisor before acting on it with real money.
"""


def _run_tool(name: str, tool_input: dict) -> dict:
    handler = DISPATCH.get(name)
    if handler is None:
        return {"error": f"Unknown tool '{name}'"}
    try:
        return handler(tool_input)
    except Exception as exc:  # noqa: BLE001 -- surfaced to the model as a tool error, not crashed
        return {"error": f"{type(exc).__name__}: {exc}", "trace": traceback.format_exc(limit=3)}


def run_agent_turn(client: OpenAI, messages: list) -> list:
    """Runs one user turn to completion (including any tool round-trips).

    `messages` holds only user/assistant/tool turns -- the system prompt is prepended fresh
    on every call rather than stored in the list. Mutates/extends `messages` in place, and
    returns the same list. The caller is expected to keep reusing `messages` as the history.
    """
    for _ in range(MAX_TOOL_ROUNDS):
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
            tools=TOOLS,
        )
        message = response.choices[0].message

        assistant_entry = {"role": "assistant", "content": message.content}
        if message.tool_calls:
            assistant_entry["tool_calls"] = [
                {
                    "id": call.id,
                    "type": "function",
                    "function": {"name": call.function.name, "arguments": call.function.arguments},
                }
                for call in message.tool_calls
            ]
        messages.append(assistant_entry)

        if not message.tool_calls:
            return messages

        for call in message.tool_calls:
            args = json.loads(call.function.arguments or "{}")
            result = _run_tool(call.function.name, args)
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": json.dumps(result, default=str),
            })

    messages.append({
        "role": "user",
        "content": "Tool round limit reached -- please give your best answer with what you have so far.",
    })
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
    )
    messages.append({"role": "assistant", "content": response.choices[0].message.content})
    return messages


def latest_text(messages: list) -> str:
    """Extracts the plain-text content of the most recent assistant message."""
    for msg in reversed(messages):
        if msg["role"] == "assistant":
            return msg.get("content") or ""
    return ""
