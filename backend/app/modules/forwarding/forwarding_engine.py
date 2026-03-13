from __future__ import annotations

from app.config import DEFAULT_TIMING
from app.models import Packet, PacketStatus
from app.models.packets import DataPacket
from app.modules.forwarding.loop_protection import LoopProtection
from app.modules.forwarding.ttl import TTLController
from app.modules.communication.unicast import UnicastEngine
from app.modules.monitoring.metrics import MetricsCollector
from app.modules.monitoring.events import EventLogger
from app.modules.routing.route_cache import RouteCache


class NextHopResolver:
    def __init__(self) -> None:
        self._cache = RouteCache()

    def resolve(self, session, node_id: str, gs_id: str):
        return self._cache.get_route(session, node_id, gs_id)


class ForwardingEngine:
    def __init__(self, unicast: UnicastEngine) -> None:
        self._resolver = NextHopResolver()
        self._loop = LoopProtection()
        self._ttl = TTLController()
        self._metrics = MetricsCollector()
        self._logger = EventLogger()
        self._unicast = unicast

    def forward_to_gs(
        self,
        session,
        packet: DataPacket,
        gs_id: str,
        confidence_threshold: float = 0.4,
        max_hops: int | None = None,
    ) -> tuple[str, int]:
        hops = 0
        current = packet.source_uav_id
        hop_limit = max_hops if max_hops is not None else DEFAULT_TIMING.max_hops

        while True:
            if self._loop.seen(current, packet.packet_id):
                self._metrics.increment(session, "packet_drop_loop", node_id=current)
                return "DROPPED_LOOP", hops

            if current == gs_id:
                self._metrics.increment(session, "packet_delivered", node_id=current)
                return "DELIVERED", hops

            route = self._resolver.resolve(session, current, gs_id)
            if route is None or route.route_confidence < confidence_threshold:
                return "BUFFER", hops

            if hops >= hop_limit:
                self._metrics.increment(session, "packet_drop_max_hops", node_id=current)
                return "DROPPED_HOPS", hops

            if not self._ttl.decrement(packet):
                self._metrics.increment(session, "packet_drop_ttl", node_id=current)
                return "DROPPED_TTL", hops

            next_hop = route.next_hop_id
            packet.hop_count += 1
            self._unicast.send(session, packet, from_id=current, to_id=next_hop)
            self._metrics.increment(session, "packet_forwarded", node_id=current)
            self._logger.log(
                session,
                current,
                "FORWARD",
                f"Forwarding to {next_hop}",
                data={"packet_id": packet.packet_id, "hop": packet.hop_count},
            )
            hops += 1
            current = next_hop
