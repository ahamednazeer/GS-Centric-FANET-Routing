from __future__ import annotations

from sqlmodel import select

from app.models import BufferEntry, PriorityLevel


class DropPolicyManager:
    def drop_lowest_priority(self, session, max_drop: int = 1) -> int:
        dropped = 0
        for priority in [PriorityLevel.STANDARD, PriorityLevel.HIGH, PriorityLevel.EMERGENCY]:
            entries = session.exec(
                select(BufferEntry)
                .where(BufferEntry.priority == priority)
                .order_by(BufferEntry.created_at)
            ).all()
            for entry in entries:
                session.delete(entry)
                dropped += 1
                if dropped >= max_drop:
                    session.commit()
                    return dropped
        if dropped:
            session.commit()
        return dropped

    def purge_emergency(self, session) -> int:
        entries = session.exec(select(BufferEntry).order_by(BufferEntry.created_at)).all()
        for entry in entries:
            session.delete(entry)
        if entries:
            session.commit()
        return len(entries)

