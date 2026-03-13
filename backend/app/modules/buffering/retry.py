from __future__ import annotations

from datetime import datetime

from sqlmodel import select

from app.models import BufferEntry, Packet, PacketStatus
from app.models.packets import DataPacket
from app.modules.buffering.buffer_queue import PriorityQueueManager
from app.modules.forwarding.forwarding_engine import ForwardingEngine


class RetryScheduler:
    def __init__(self, forwarding_engine: ForwardingEngine) -> None:
        self._queue = PriorityQueueManager()
        self._forwarding = forwarding_engine

    def retry(self, session, gs_id: str) -> int:
        entries = self._queue.get_buffered(session)
        processed = 0
        for entry in entries:
            if entry.expiry_time <= datetime.utcnow():
                session.delete(entry)
                processed += 1
                continue
            packet_record = session.exec(
                select(Packet).where(Packet.packet_id == entry.packet_id)
            ).first()
            if packet_record is None:
                session.delete(entry)
                processed += 1
                continue
            data_packet = DataPacket(
                packet_id=packet_record.packet_id,
                source_uav_id=packet_record.source_id,
                destination_id=packet_record.destination_id,
                creation_timestamp=packet_record.created_at,
                priority_level=packet_record.priority,
                payload_type=packet_record.payload_type or "unknown",
                payload_size=packet_record.payload_size or 0,
                hop_count=packet_record.hop_count,
                route_confidence_tag=packet_record.route_confidence_tag or 0.0,
                ttl=packet_record.ttl,
                payload=packet_record.packet_meta.get("payload"),
            )
            status, hops = self._forwarding.forward_to_gs(session, data_packet, gs_id)
            if status == "DELIVERED":
                packet_record.status = PacketStatus.DELIVERED
                session.add(packet_record)
                session.delete(entry)
                processed += 1
                session.commit()
            else:
                entry.retry_count += 1
                session.add(entry)
                session.commit()
        return processed
