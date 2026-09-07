import logging
import os
from typing import Optional, Dict, Any
from src.telemetry.events import TelemetryEvent, EventType
from src.telemetry.handlers.base import BaseHandler

# Silence all langfuse output so it NEVER pollutes stdout
_lf_logger = logging.getLogger("langfuse")
_lf_logger.setLevel(logging.CRITICAL)
_lf_logger.propagate = False

try:
    from langfuse import Langfuse, observe
    _LANGFUSE_AVAILABLE = True
except ImportError:
    Langfuse = None
    observe = None
    _LANGFUSE_AVAILABLE = False


class LangfuseHandler(BaseHandler):
    """
    Asynchronous background telemetry sink for self-hosted Langfuse v3.
    Processes events without printing anything to stdout.
    Gracefully degrades to a no-op if unconfigured or unreachable.
    """

    def __init__(
        self,
        host: Optional[str] = None,
        public_key: Optional[str] = None,
        secret_key: Optional[str] = None,
    ):
        self.host = host or os.getenv("LANGFUSE_HOST", "http://192.168.68.53:3005")
        self.public_key = public_key or os.getenv("LANGFUSE_PUBLIC_KEY", "")
        self.secret_key = secret_key or os.getenv("LANGFUSE_SECRET_KEY", "")
        self._enabled = False
        self.client: Optional[Any] = None
        self._active_spans: Dict[str, Any] = {}

        self._init_client()

    def _init_client(self) -> None:
        if not _LANGFUSE_AVAILABLE:
            return
        if not self.public_key or not self.secret_key:
            return

        try:
            self.client = Langfuse(
                public_key=self.public_key,
                secret_key=self.secret_key,
                host=self.host,
                debug=False,
            )
            # Lightweight verification: auth_check can be skipped or tested safely
            self._enabled = True
        except Exception:
            self._enabled = False
            self.client = None

    @property
    def is_enabled(self) -> bool:
        return self._enabled and self.client is not None

    def handle(self, event: TelemetryEvent) -> None:
        if not self.is_enabled:
            return

        etype = event.event_type
        src = event.source
        payload = event.payload or {}

        try:
            if etype == EventType.THINKING.value:
                thought = payload.get("thought") or payload.get("message") or ""
                self.client.create_event(
                    name=f"thinking:{src}",
                    input={"thought": thought, **payload},
                    metadata={"source": src}
                )

            elif etype == EventType.TOOL_CALL.value:
                tool_name = payload.get("tool", f"tool_{src}")
                span_key = f"{src}:{tool_name}"
                span = self.client.start_observation(
                    name=tool_name,
                    as_type="tool",
                    input=payload,
                    metadata={"source": src}
                )
                self._active_spans[span_key] = span

            elif etype == EventType.TOOL_RESULT.value:
                tool_name = payload.get("tool", f"tool_{src}")
                span_key = f"{src}:{tool_name}"
                span = self._active_spans.pop(span_key, None)
                if span:
                    span.update(output=payload.get("result", payload))
                    span.end()
                else:
                    self.client.create_event(
                        name=f"result:{tool_name}",
                        output=payload,
                        metadata={"source": src}
                    )

            elif etype == EventType.ERROR.value:
                err_msg = payload.get("error") or payload.get("message", "Error")
                self.client.create_event(
                    name=f"error:{src}",
                    level="ERROR",
                    status_message=str(err_msg),
                    output=payload,
                    metadata={"source": src}
                )

            elif etype == EventType.RESPONSE.value:
                content = payload.get("content", "")
                tokens = payload.get("tokens")
                usage = {"total": tokens} if tokens else None
                self.client.start_observation(
                    name=f"response:{src}",
                    as_type="generation",
                    output=content[:2000] if isinstance(content, str) else content,
                    usage_details=usage,
                    metadata={"source": src}
                ).end()

        except Exception:
            # Absolute safety: Langfuse issues must never crash agent execution or print to stdout
            pass

    def close(self) -> None:
        """Flushes buffered events asynchronously."""
        if self.is_enabled and self.client:
            try:
                for span in self._active_spans.values():
                    span.end()
                self._active_spans.clear()
                self.client.flush()
            except Exception:
                pass


if __name__ == "__main__":
    print("==================================================")
    print("📡 LangfuseHandler Standalone Test")
    print("==================================================")
    handler = LangfuseHandler()
    print(f"[*] Handler active: {handler.is_enabled}")
    print(f"[*] Target Host: {handler.host}")
    handler.handle(TelemetryEvent("THINKING", {"thought": "Verifying Langfuse sink"}, "test"))
    handler.close()
    print("==================================================")
