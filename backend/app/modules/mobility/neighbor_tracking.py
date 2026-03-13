from __future__ import annotations

from datetime import datetime
from sqlmodel import select

from app.models import Neighbor


class NeighborTrackingEngine:
    def update_neighbors(self, session, node_id: str, neighbors: list[dict]) -> None:
        for neighbor in neighbors:
            record = session.exec(
                select(Neighbor).where(
                    Neighbor.node_id == node_id, Neighbor.neighbor_id == neighbor["neighbor_id"]
                )
            ).first()
            if record is None:
                record = Neighbor(node_id=node_id, neighbor_id=neighbor["neighbor_id"])
            record.last_seen = datetime.utcnow()
            record.rssi = neighbor.get("rssi")
            record.packet_loss_rate = neighbor.get("packet_loss_rate")
            record.mobility_vector = neighbor.get("mobility_vector")
            session.add(record)
        session.commit()

