"""Streaming markdown renderer for LLM output.

Uses Rich Live display to incrementally render markdown as LLM tokens arrive.
Inspired by Aider's MarkdownStream.
"""

from __future__ import annotations

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown


class MarkdownStream:
    """Incrementally render LLM output as markdown in real-time."""

    def __init__(self, console: Console, min_interval: float = 0.05):
        self._console = console
        self._text = ""
        self._live = Live(
            Markdown(""),
            console=console,
            refresh_per_second=8,
            transient=True,
        )
        self._live.start()

    def update(self, token: str) -> None:
        """Append a token and refresh the display."""
        self._text += token
        self._live.update(Markdown(self._text))

    def finish(self) -> None:
        """Stop the live display and print the final rendered markdown."""
        self._live.stop()
        # Print the final markdown so it stays in the terminal
        self._console.print(Markdown(self._text))

    @property
    def text(self) -> str:
        return self._text
