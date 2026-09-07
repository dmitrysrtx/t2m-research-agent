import sys
from typing import Optional, Any
from src.telemetry.events import TelemetryEvent, EventType
from src.telemetry.handlers.base import BaseHandler

try:
    from rich.console import Console
    _CONSOLE = Console(highlight=False)
except ImportError:
    _CONSOLE = None


class TerminalHandler(BaseHandler):
    """
    Outputs clean, concise, 1-line progress messages to the terminal using Rich.
    Prevents raw JSON dumps, trace clutter, and duplicate log lines.
    """

    def __init__(self, console: Optional[Any] = None):
        self.console = console or _CONSOLE

    def _format_summary(self, text: str, max_len: int = 100) -> str:
        clean = " ".join(str(text).split())
        return clean[:max_len] + ("..." if len(clean) > max_len else "")

    def handle(self, event: TelemetryEvent) -> None:
        etype = event.event_type
        src = event.source
        payload = event.payload or {}

        if self.console:
            self._handle_rich(etype, src, payload)
        else:
            self._handle_plain(etype, src, payload)

    def _handle_rich(self, etype: str, src: str, payload: dict) -> None:
        if etype == EventType.THINKING.value:
            thought = payload.get("thought") or payload.get("message", "")
            summary = self._format_summary(thought)
            self.console.print(f"[dim cyan]🤔 [{src}][/dim cyan] {summary}")

        elif etype == EventType.TOOL_CALL.value:
            tool = payload.get("tool", "tool")
            args = payload.get("args") or payload.get("query", "")
            summary = self._format_summary(args, max_len=80)
            self.console.print(f"[bold blue]🔍 [{src}][/bold blue] Calling [cyan]{tool}[/cyan] ({summary})")

        elif etype == EventType.TOOL_RESULT.value:
            tool = payload.get("tool", "tool")
            res = payload.get("result") or payload.get("summary", "OK")
            duration = payload.get("duration")
            dur_str = f" [dim]({duration:.2f}s)[/dim]" if duration is not None else ""
            summary = self._format_summary(res, max_len=90)
            self.console.print(f"[bold green]✅ [{src}][/bold green] [cyan]{tool}[/cyan] -> {summary}{dur_str}")

        elif etype == EventType.ERROR.value:
            err = payload.get("error") or payload.get("message", "Unknown error")
            summary = self._format_summary(err, max_len=120)
            self.console.print(f"[bold red]❌ [{src}][/bold red] {summary}")

        elif etype == EventType.RESPONSE.value:
            resp = payload.get("content") or payload.get("summary", "Generated response")
            tokens = payload.get("tokens")
            tok_str = f" [dim](tokens: {tokens})[/dim]" if tokens else ""
            summary = self._format_summary(resp, max_len=90)
            self.console.print(f"[bold magenta]📝 [{src}][/bold magenta] {summary}{tok_str}")

    def _handle_plain(self, etype: str, src: str, payload: dict) -> None:
        msg = payload.get("thought") or payload.get("result") or payload.get("error") or payload.get("content") or ""
        summary = self._format_summary(msg, max_len=100)
        sys.stdout.write(f"[{etype}] [{src}] {summary}\n")
        sys.stdout.flush()


if __name__ == "__main__":
    print("==================================================")
    print("🖥️ TerminalHandler Standalone Test")
    print("==================================================")
    handler = TerminalHandler()
    handler.handle(TelemetryEvent(EventType.THINKING, {"thought": "Extracting key findings from literature"}, "sub_agent:kinematic"))
    handler.handle(TelemetryEvent(EventType.TOOL_CALL, {"tool": "fetch_ieee_papers", "query": "text to motion"}, "ieee_fetcher"))
    handler.handle(TelemetryEvent(EventType.TOOL_RESULT, {"tool": "fetch_ieee_papers", "result": "Retrieved 5 papers", "duration": 1.45}, "ieee_fetcher"))
    handler.handle(TelemetryEvent(EventType.ERROR, {"error": "Cookie token missing ERIGHTS"}, "auth"))
    handler.handle(TelemetryEvent(EventType.RESPONSE, {"content": "Comprehensive synthesis completed successfully.", "tokens": 1250}, "orchestrator"))
    print("==================================================")
