from __future__ import annotations

from app.models.packets import DataPacket


class TTLController:
    def decrement(self, packet: DataPacket) -> bool:
        if packet.ttl <= 0:
            return False
        packet.ttl -= 1
        return packet.ttl >= 0

