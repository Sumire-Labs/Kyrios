from abc import ABC, abstractmethod
from typing import Any, List, Dict, Optional
import logging
from datetime import datetime


class Observer(ABC):
    @abstractmethod
    async def update(self, event_type: str, data: Dict[str, Any]) -> None:
        pass


class Subject(ABC):
    def __init__(self):
        self._observers: List[Observer] = []
        self.logger = logging.getLogger(__name__)

    def attach(self, observer: Observer) -> None:
        if observer not in self._observers:
            self._observers.append(observer)
            self.logger.debug(f"Observer {observer.__class__.__name__} attached")

    def detach(self, observer: Observer) -> None:
        if observer in self._observers:
            self._observers.remove(observer)
            self.logger.debug(f"Observer {observer.__class__.__name__} detached")

    async def notify(self, event_type: str, data: Dict[str, Any]) -> None:
        for observer in self._observers:
            try:
                await observer.update(event_type, data)
            except Exception as e:
                self.logger.error(f"Observer {observer.__class__.__name__} failed to process event {event_type}: {e}")


class EventBus(Subject):
    def __init__(self):
        super().__init__()
        self._event_history: List[Dict[str, Any]] = []

    async def emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        event_data = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now(),
            "id": len(self._event_history)
        }

        self._event_history.append(event_data)
        await self.notify(event_type, event_data)
        self.logger.info(f"Event {event_type} emitted with data: {data}")

    def get_event_history(self, event_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        events = self._event_history
        if event_type:
            events = [e for e in events if e["type"] == event_type]

        return events[-limit:] if limit > 0 else events

    def clear_event_history(self) -> None:
        self._event_history.clear()
        self.logger.info("Event history cleared")


class LoggingObserver(Observer):
    def __init__(self):
        self.logger = logging.getLogger("EventLogger")

    async def update(self, event_type: str, data: Dict[str, Any]) -> None:
        timestamp = data.get("timestamp", datetime.now())
        event_data = data.get("data", {})
        self.logger.info(f"[{timestamp}] Event: {event_type} | Data: {event_data}")


class MetricsObserver(Observer):
    def __init__(self):
        self.event_counts: Dict[str, int] = {}
        self.logger = logging.getLogger("MetricsObserver")

    async def update(self, event_type: str, data: Dict[str, Any]) -> None:
        self.event_counts[event_type] = self.event_counts.get(event_type, 0) + 1
        self.logger.debug(f"Event {event_type} count: {self.event_counts[event_type]}")

    def get_metrics(self) -> Dict[str, int]:
        return self.event_counts.copy()

    def reset_metrics(self) -> None:
        self.event_counts.clear()
        self.logger.info("Metrics reset")