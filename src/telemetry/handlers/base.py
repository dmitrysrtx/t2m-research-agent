from abc import ABC, abstractmethod
from src.telemetry.events import TelemetryEvent


class BaseHandler(ABC):
    """
    Abstract base sink for all telemetry handlers.
    Each handler is responsible for consuming TelemetryEvent instances.
    """

    @abstractmethod
    def handle(self, event: TelemetryEvent) -> None:
        """Process a single telemetry event."""
        pass

    def close(self) -> None:
        """Optional cleanup or flush operation on shutdown."""
        pass
