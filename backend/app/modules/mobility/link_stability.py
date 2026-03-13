from __future__ import annotations

from sqlmodel import select

from app.models import Neighbor


class LinkStabilityAnalyzer:
    def _normalize_rssi(self, rssi: float | None) -> float:
        if rssi is None:
            return 0.5
        return max(0.0, min(1.0, (rssi + 100.0) / 70.0))

    def link_quality(self, session, node_id: str, neighbor_id: str) -> float:
        record = session.exec(
            select(Neighbor).where(Neighbor.node_id == node_id, Neighbor.neighbor_id == neighbor_id)
        ).first()
        if record is None:
            return 0.5
        rssi_score = self._normalize_rssi(record.rssi)
        loss_score = 1.0 - (record.packet_loss_rate or 0.0)
        stability = (0.6 * rssi_score) + (0.4 * loss_score)
        record.link_stability = stability
        session.add(record)
        session.commit()
        return stability

    def average_link_quality(self, session, node_id: str) -> float:
        neighbors = session.exec(select(Neighbor).where(Neighbor.node_id == node_id)).all()
        if not neighbors:
            return 0.4
        scores = [self.link_quality(session, node_id, n.neighbor_id) for n in neighbors]
        return sum(scores) / len(scores)

