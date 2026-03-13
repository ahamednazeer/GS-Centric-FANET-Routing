from __future__ import annotations

from sqlmodel import select

from app.config import DEFAULT_BUFFER
from app.models import BufferEntry
from app.modules.buffering.drop_policy import DropPolicyManager


class CongestionController:
    def __init__(
        self,
        max_size: int | None = None,
        high_watermark: float | None = None,
        emergency_watermark: float | None = None,
    ) -> None:
        self._drop_policy = DropPolicyManager()
        self._max_size = max_size or DEFAULT_BUFFER.max_size
        self._high_watermark = high_watermark or DEFAULT_BUFFER.high_watermark
        self._emergency_watermark = emergency_watermark or DEFAULT_BUFFER.emergency_watermark

    def enforce(self, session) -> int:
        entries = session.exec(select(BufferEntry)).all()
        size = len(entries)
        if size == 0:
            return 0
        occupancy = size / self._max_size
        if occupancy >= self._emergency_watermark:
            return self._drop_policy.purge_emergency(session)
        if occupancy >= self._high_watermark:
            return self._drop_policy.drop_lowest_priority(session)
        return 0
