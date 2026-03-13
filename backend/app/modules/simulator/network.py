from __future__ import annotations

from collections import deque

from sqlmodel import select

from app.models import Neighbor
from app.models.packets import GSFloodPacket
from app.modules.routing.gs_flood import FloodReceiver
from app.modules.monitoring.metrics import MetricsCollector


class NetworkSimulator:
    def __init__(self, route_expiry=None) -> None:
        self._receiver = FloodReceiver()
        self._metrics = MetricsCollector()
        self._route_expiry = route_expiry

    def _neighbors_for(self, session, node_id: str) -> list[str]:
        neighbors = session.exec(select(Neighbor).where(Neighbor.node_id == node_id)).all()
        return [n.neighbor_id for n in neighbors]

    def propagate_flood(self, session, flood_packet: GSFloodPacket) -> dict:
        queue = deque([(flood_packet.gs_id, 0, flood_packet.flood_ttl)])
        accepted = 0
        dropped = 0
        propagated = 0

        while queue:
            sender_id, sender_hop, ttl = queue.popleft()
            if ttl <= 0:
                continue
            neighbors = self._neighbors_for(session, sender_id)
            for neighbor_id in neighbors:
                propagated += 1
                packet_copy = GSFloodPacket(
                    gs_id=flood_packet.gs_id,
                    flood_sequence_number=flood_packet.flood_sequence_number,
                    hop_count=sender_hop,
                    timestamp=flood_packet.timestamp,
                    flood_ttl=flood_packet.flood_ttl,
                    digital_signature=flood_packet.digital_signature,
                )
                should_rebroadcast, _ = self._receiver.process(
                    session,
                    receiver_id=neighbor_id,
                    sender_id=sender_id,
                    packet=packet_copy,
                    route_expiry=self._route_expiry,
                )
                if should_rebroadcast:
                    accepted += 1
                    queue.append((neighbor_id, sender_hop + 1, ttl - 1))
                else:
                    dropped += 1

        self._metrics.increment(session, "flood_propagated", propagated)
        return {
            "propagated_nodes": propagated,
            "accepted_nodes": accepted,
            "dropped_nodes": dropped,
        }
