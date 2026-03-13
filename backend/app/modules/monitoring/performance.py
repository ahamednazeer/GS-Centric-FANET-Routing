from __future__ import annotations

from sqlmodel import select

from app.models import Packet, PacketStatus


class PerformanceAnalyzer:
    def summary(self, session) -> dict:
        packets = session.exec(select(Packet)).all()
        total = len(packets)
        delivered = len([p for p in packets if p.status == PacketStatus.DELIVERED])
        forwarded = len([p for p in packets if p.status == PacketStatus.FORWARDED])
        dropped = len([p for p in packets if p.status == PacketStatus.DROPPED])
        buffered = len([p for p in packets if p.status == PacketStatus.BUFFERED])
        pdr = (delivered / total) if total > 0 else 0.0
        return {
            "total_packets": total,
            "delivered": delivered,
            "forwarded": forwarded,
            "buffered": buffered,
            "dropped": dropped,
            "packet_delivery_ratio": round(pdr, 4),
        }

