from __future__ import annotations

from datetime import datetime
from sqlmodel import select

from app.config import DEFAULT_TIMING
from app.models import RouteEntry
from app.modules.mobility.link_stability import LinkStabilityAnalyzer


class RouteConfidenceScorer:
    def __init__(self) -> None:
        self._link_stability = LinkStabilityAnalyzer()

    def score(self, session, node_id: str, gs_id: str, link_quality: float | None = None) -> float:
        route = session.exec(
            select(RouteEntry).where(RouteEntry.node_id == node_id, RouteEntry.gs_id == gs_id)
        ).first()
        now = datetime.utcnow()
        freshness = 1.0
        if route is not None:
            age = (now - route.last_updated).total_seconds()
            freshness = max(0.0, 1.0 - (age / DEFAULT_TIMING.route_expiry_seconds))
        if link_quality is None:
            link_quality = self._link_stability.average_link_quality(session, node_id)
        mobility_score = 0.8  # placeholder for mobility variance analysis
        confidence = (0.4 * link_quality) + (0.3 * freshness) + (0.2 * mobility_score) + 0.1
        return max(0.0, min(1.0, confidence))

