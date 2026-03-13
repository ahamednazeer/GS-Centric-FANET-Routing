from __future__ import annotations

from app.config import DEFAULT_TIMING
from app.models import Packet, PacketStatus, PacketType
from app.models.packets import DataPacket
from app.modules.buffering.buffer_queue import PriorityQueueManager
from app.modules.forwarding.forwarding_engine import ForwardingEngine
from app.modules.monitoring.metrics import MetricsCollector


class DataPipelineManager:
    def __init__(
        self,
        forwarding_engine: ForwardingEngine,
        buffer_timeout=None,
        max_hops: int | None = None,
    ) -> None:
        self._forwarding = forwarding_engine
        self._buffer_queue = PriorityQueueManager()
        self._metrics = MetricsCollector()
        self._buffer_timeout = buffer_timeout or DEFAULT_TIMING.buffer_timeout
        self._max_hops = max_hops

    def send(self, session, packet: DataPacket, gs_id: str) -> tuple[str, int]:
        status, hops = self._forwarding.forward_to_gs(
            session,
            packet,
            gs_id,
            max_hops=self._max_hops,
        )
        packet_record = Packet(
            packet_id=packet.packet_id,
            packet_type=PacketType.DATA,
            source_id=packet.source_uav_id,
            destination_id=packet.destination_id,
            priority=packet.priority_level,
            payload_type=packet.payload_type,
            payload_size=packet.payload_size,
            hop_count=packet.hop_count,
            route_confidence_tag=packet.route_confidence_tag,
            ttl=packet.ttl,
            packet_meta={"payload": packet.payload},
        )

        if status == "DELIVERED":
            packet_record.status = PacketStatus.DELIVERED
            session.add(packet_record)
            session.commit()
            return status, hops

        if status == "BUFFER":
            packet_record.status = PacketStatus.BUFFERED
            session.add(packet_record)
            session.commit()
            self._buffer_queue.buffer_packet(
                session,
                node_id=packet.source_uav_id,
                packet_id=packet.packet_id,
                priority=packet.priority_level,
                timeout=self._buffer_timeout,
            )
            self._metrics.increment(session, "packet_buffered", node_id=packet.source_uav_id)
            return status, hops

        packet_record.status = PacketStatus.DROPPED
        session.add(packet_record)
        session.commit()
        self._metrics.increment(session, "packet_dropped", node_id=packet.source_uav_id)
        return status, hops
