import time
from contextlib import contextmanager
from typing import List, Dict, Any, Optional
from src.telemetry.events import TelemetryEvent, EventType
from src.telemetry.handlers.base import BaseHandler
from src.telemetry.handlers.terminal import TerminalHandler
from src.telemetry.handlers.langfuse_sink import LangfuseHandler
import agent_config as config


class TelemetryManager:
    """
    Central Event Dispatcher coordinating all telemetry sinks.
    Decouples business logic from output sinks (Terminal, Langfuse, SSE).
    """

    def __init__(self, handlers: Optional[List[BaseHandler]] = None):
        self._handlers: List[BaseHandler] = handlers if handlers is not None else []

    def register_handler(self, handler: BaseHandler) -> None:
        if handler not in self._handlers:
            self._handlers.append(handler)

    def unregister_handler(self, handler: BaseHandler) -> None:
        if handler in self._handlers:
            self._handlers.remove(handler)

    def emit(
        self,
        event_type: str,
        payload: Optional[Dict[str, Any]] = None,
        source: str = "agent",
        trace_id: Optional[str] = None,
        parent_id: Optional[str] = None,
    ) -> TelemetryEvent:
        event = TelemetryEvent(
            event_type=event_type,
            payload=payload or {},
            source=source,
            trace_id=trace_id,
            parent_id=parent_id,
        )

        for handler in list(self._handlers):
            try:
                handler.handle(event)
            except Exception:
                # Isolated sink protection: handler failure must never disrupt agent execution
                pass

        return event

    def thinking(self, thought: str, source: str = "agent", **kwargs) -> TelemetryEvent:
        return self.emit(EventType.THINKING.value, {"thought": thought, **kwargs}, source=source)

    def tool_call(self, tool: str, args: Any = "", source: str = "agent", **kwargs) -> TelemetryEvent:
        return self.emit(EventType.TOOL_CALL.value, {"tool": tool, "args": args, **kwargs}, source=source)

    def tool_result(
        self, tool: str, result: Any = "OK", duration: Optional[float] = None, source: str = "agent", **kwargs
    ) -> TelemetryEvent:
        return self.emit(
            EventType.TOOL_RESULT.value,
            {"tool": tool, "result": result, "duration": duration, **kwargs},
            source=source,
        )

    def error(self, error: Any, source: str = "agent", **kwargs) -> TelemetryEvent:
        return self.emit(EventType.ERROR.value, {"error": str(error), **kwargs}, source=source)

    def response(
        self, content: str, tokens: Optional[int] = None, source: str = "agent", **kwargs
    ) -> TelemetryEvent:
        return self.emit(EventType.RESPONSE.value, {"content": content, "tokens": tokens, **kwargs}, source=source)

    @contextmanager
    def span(self, tool: str, args: Any = "", source: str = "agent"):
        """Context manager to measure tool/task execution duration automatically."""
        start_t = time.time()
        self.tool_call(tool=tool, args=args, source=source)
        try:
            yield
            duration = time.time() - start_t
            self.tool_result(tool=tool, result="Completed", duration=duration, source=source)
        except Exception as e:
            duration = time.time() - start_t
            self.error(error=e, source=source, tool=tool, duration=duration)
            raise

    def close(self) -> None:
        """Closes and flushes all registered handlers."""
        for handler in list(self._handlers):
            try:
                handler.close()
            except Exception:
                pass


_GLOBAL_TELEMETRY: Optional[TelemetryManager] = None


def get_telemetry() -> TelemetryManager:
    """Returns the default configured singleton TelemetryManager."""
    global _GLOBAL_TELEMETRY
    if _GLOBAL_TELEMETRY is None:
        mgr = TelemetryManager()
        if getattr(config, "ENABLE_CLI_LOGS", True):
            mgr.register_handler(TerminalHandler())
        if getattr(config, "LANGFUSE_PUBLIC_KEY", ""):
            mgr.register_handler(LangfuseHandler(
                host=getattr(config, "LANGFUSE_HOST", "http://192.168.68.53:3005"),
                public_key=getattr(config, "LANGFUSE_PUBLIC_KEY", ""),
                secret_key=getattr(config, "LANGFUSE_SECRET_KEY", "")
            ))
        _GLOBAL_TELEMETRY = mgr
    return _GLOBAL_TELEMETRY


if __name__ == "__main__":
    print("==================================================")
    print("🚀 TelemetryManager Standalone Test")
    print("==================================================")
    tm = TelemetryManager([TerminalHandler()])
    tm.thinking("Evaluating test hypothesis", source="tester")
    with tm.span("sample_tool", args="query=physics", source="tester"):
        time.sleep(0.05)
    tm.response("All tests passed.", tokens=100, source="tester")
    tm.close()
    print("==================================================")
