import time
import json
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict


class EventType(str, Enum):
    THINKING = "THINKING"
    TOOL_CALL = "TOOL_CALL"
    TOOL_RESULT = "TOOL_RESULT"
    ERROR = "ERROR"
    RESPONSE = "RESPONSE"


@dataclass
class TelemetryEvent:
    event_type: str
    payload: Dict[str, Any] = field(default_factory=dict)
    source: str = "agent"
    timestamp: float = field(default_factory=time.time)
    trace_id: Optional[str] = None
    parent_id: Optional[str] = None

    def __post_init__(self):
        # Normalize event_type if passed as Enum
        if isinstance(self.event_type, EventType):
            self.event_type = self.event_type.value
        else:
            self.event_type = str(self.event_type).upper()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "source": self.source,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "trace_id": self.trace_id,
            "parent_id": self.parent_id,
        }

    def to_sse(self) -> str:
        """Converts event to an SSE-compliant stream chunk."""
        content = self.payload.get("content") or self.payload.get("thought") or self.payload.get("message") or ""
        sse_data = {
            "type": self.event_type,
            "source": self.source,
            "content": content,
            "payload": self.payload,
            "timestamp": self.timestamp,
        }
        return f"data: {json.dumps(sse_data)}\n\n"


if __name__ == "__main__":
    print("==================================================")
    print("📡 Telemetry Event Standalone Test")
    print("==================================================")
    evt = TelemetryEvent(
        event_type=EventType.THINKING,
        source="test_agent",
        payload={"thought": "Synthesizing literature...", "tokens": 42}
    )
    print(f"[*] Dict: {evt.to_dict()}")
    print(f"[*] SSE: {evt.to_sse().strip()}")
    print("==================================================")
