from __future__ import annotations

from app.models import EventLog


class EventLogger:
    def log(self, session, node_id: str | None, event_type: str, message: str, data: dict | None = None) -> None:
        event = EventLog(node_id=node_id, event_type=event_type, message=message, data=data or {})
        session.add(event)
        session.commit()

