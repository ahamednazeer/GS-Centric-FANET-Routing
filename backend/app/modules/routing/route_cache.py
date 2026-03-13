from __future__ import annotations

from datetime import datetime, timedelta
from sqlmodel import select

from app.models import RouteEntry


class RouteCache:
    def get_route(self, session, node_id: str, gs_id: str) -> RouteEntry | None:
        return session.exec(
            select(RouteEntry).where(RouteEntry.node_id == node_id, RouteEntry.gs_id == gs_id)
        ).first()

    def update_route(
        self,
        session,
        node_id: str,
        gs_id: str,
        next_hop_id: str,
        hop_count: int,
        route_confidence: float,
        link_quality_score: float,
        expiry: timedelta,
    ) -> RouteEntry:
        now = datetime.utcnow()
        entry = self.get_route(session, node_id, gs_id)
        if entry is None:
            entry = RouteEntry(
                node_id=node_id,
                gs_id=gs_id,
                next_hop_id=next_hop_id,
                hop_count=hop_count,
                last_updated=now,
                route_confidence=route_confidence,
                link_quality_score=link_quality_score,
                expires_at=now + expiry,
            )
        else:
            entry.next_hop_id = next_hop_id
            entry.hop_count = hop_count
            entry.last_updated = now
            entry.route_confidence = route_confidence
            entry.link_quality_score = link_quality_score
            entry.expires_at = now + expiry
        session.add(entry)
        session.commit()
        return entry

    def expire_routes(self, session) -> int:
        now = datetime.utcnow()
        routes = session.exec(select(RouteEntry)).all()
        expired = [route for route in routes if route.expires_at <= now]
        for route in expired:
            session.delete(route)
        if expired:
            session.commit()
        return len(expired)

