import queue
import asyncio
from typing import Generator, AsyncGenerator, Optional
from src.telemetry.events import TelemetryEvent
from src.telemetry.handlers.base import BaseHandler


class SSEHandler(BaseHandler):
    """
    Sinks telemetry events into a thread-safe Queue and converts them into
    SSE-compliant chunks (`data: {...}\n\n`) for OpenWebUI and FastAPI streaming.
    """

    _SENTINEL = object()

    def __init__(self, maxsize: int = 1000):
        self._queue = queue.Queue(maxsize=maxsize)
        self._closed = False

    def handle(self, event: TelemetryEvent) -> None:
        if self._closed:
            return
        sse_chunk = event.to_sse()
        try:
            self._queue.put_nowait(sse_chunk)
        except queue.Full:
            pass

    def stream(self, timeout: float = 0.5) -> Generator[str, None, None]:
        """
        Synchronous generator yielding SSE chunks as they arrive.
        Terminates when close() is called and queue is drained.
        """
        while True:
            try:
                item = self._queue.get(timeout=timeout)
                if item is self._SENTINEL:
                    yield "data: [DONE]\n\n"
                    break
                yield item
            except queue.Empty:
                if self._closed:
                    yield "data: [DONE]\n\n"
                    break
                continue

    async def async_stream(self, timeout: float = 0.5) -> AsyncGenerator[str, None]:
        """
        Asynchronous generator for FastAPI StreamingResponse endpoints.
        """
        loop = asyncio.get_event_loop()
        while True:
            try:
                item = await loop.run_in_executor(None, self._queue.get, True, timeout)
                if item is self._SENTINEL:
                    yield "data: [DONE]\n\n"
                    break
                yield item
            except queue.Empty:
                if self._closed:
                    yield "data: [DONE]\n\n"
                    break
                await asyncio.sleep(0.05)

    def close(self) -> None:
        """Closes the stream and signals consumers to finish."""
        if not self._closed:
            self._closed = True
            try:
                self._queue.put_nowait(self._SENTINEL)
            except queue.Full:
                pass


if __name__ == "__main__":
    print("==================================================")
    print("📡 SSEHandler Standalone Test")
    print("==================================================")
    handler = SSEHandler()
    handler.handle(TelemetryEvent("THINKING", {"thought": "Preparing research query"}, "sub_agent:rl"))
    handler.handle(TelemetryEvent("TOOL_CALL", {"tool": "arxiv_search", "query": "humanoid control"}, "arxiv"))
    handler.close()

    chunks = list(handler.stream(timeout=0.1))
    for i, c in enumerate(chunks):
        print(f"[{i+1}] {repr(c)}")
    print("==================================================")
