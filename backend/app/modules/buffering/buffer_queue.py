from __future__ import annotations

from datetime import datetime, timedelta
from sqlmodel import select

from app.models import BufferEntry, PriorityLevel


class PriorityQueueManager:
    def buffer_packet(
        self,
        session,
        node_id: str,
        packet_id: str,
        priority: PriorityLevel,
        timeout: timedelta,
    ) -> BufferEntry:
        expiry = datetime.utcnow() + timeout
        entry = BufferEntry(
            node_id=node_id,
            packet_id=packet_id,
            priority=priority,
            expiry_time=expiry,
            retry_count=0,
        )
        session.add(entry)
        session.commit()
        return entry

    def get_buffered(self, session, node_id: str | None = None) -> list[BufferEntry]:
        statement = select(BufferEntry)
        if node_id:
            statement = statement.where(BufferEntry.node_id == node_id)
        return session.exec(statement).all()

    def remove_entry(self, session, entry: BufferEntry) -> None:
        session.delete(entry)
        session.commit()

