from __future__ import annotations

from app.config import DEFAULT_TIMING
from app.modules.mobility.link_stability import LinkStabilityAnalyzer


class DynamicFloodIntervalController:
    def __init__(self) -> None:
        self._link_stability = LinkStabilityAnalyzer()

    def recommended_interval(self, session, node_id: str) -> int:
        quality = self._link_stability.average_link_quality(session, node_id)
        if quality < 0.4:
            return max(3, int(DEFAULT_TIMING.flood_interval_seconds * 0.5))
        if quality > 0.8:
            return int(DEFAULT_TIMING.flood_interval_seconds * 1.5)
        return DEFAULT_TIMING.flood_interval_seconds

