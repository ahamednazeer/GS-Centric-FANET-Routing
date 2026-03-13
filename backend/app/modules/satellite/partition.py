from __future__ import annotations

from datetime import datetime, timedelta
from sqlmodel import select

from app.config import DEFAULT_MOBILITY, DEFAULT_TIMING
from app.models import FloodState, RouteEntry, Neighbor


class PartitionDetector:
    def is_partitioned(
        self,
        session,
        node_id: str,
        gs_id: str,
        activation_delay=None,
        neighbor_threshold=None,
    ) -> bool:
        state = session.exec(
            select(FloodState).where(FloodState.node_id == node_id, FloodState.gs_id == gs_id)
        ).first()
        last_flood = state.last_flood_at if state else None
        if last_flood is None:
            flood_gap = True
        else:
            delay = activation_delay or DEFAULT_TIMING.satellite_activation_delay
            flood_gap = datetime.utcnow() - last_flood > delay

        route = session.exec(
            select(RouteEntry).where(RouteEntry.node_id == node_id, RouteEntry.gs_id == gs_id)
        ).first()
        route_missing = route is None

        neighbors = session.exec(select(Neighbor).where(Neighbor.node_id == node_id)).all()
        threshold = neighbor_threshold if neighbor_threshold is not None else DEFAULT_MOBILITY.neighbor_min_threshold
        neighbor_count_low = len(neighbors) < threshold

        return flood_gap and route_missing and neighbor_count_low
