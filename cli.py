#!/usr/bin/env python3
"""REPL entry point for the portfolio risk agent."""
import os
import sys

import anthropic
from rich.console import Console
from rich.markdown import Markdown

from agent.loop import run_agent_turn, latest_text

console = Console()

BANNER = """[bold cyan]Portfolio Risk Agent[/bold cyan]
Educational tool -- historical data & simulations only. Not financial advice.
Type your question, or 'exit' to quit.
"""


def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        console.print("[red]Set ANTHROPIC_API_KEY in your environment before running this.[/red]")
        sys.exit(1)

    client = anthropic.Anthropic()
    messages = []
    console.print(BANNER)

    while True:
        try:
            user_input = console.input("[bold green]you>[/bold green] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\nbye.")
            break

        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            console.print("bye.")
            break

        messages.append({"role": "user", "content": user_input})
        with console.status("[dim]thinking...[/dim]"):
            run_agent_turn(client, messages)

        reply = latest_text(messages)
        console.print(Markdown(reply or "(no response)"))


if __name__ == "__main__":
    main()
