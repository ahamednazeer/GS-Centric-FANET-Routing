from __future__ import annotations

from app.modules.monitoring.events import EventLogger
from app.models.packets import DataPacket


class UnicastEngine:
    def __init__(self, logger: EventLogger) -> None:
        self._logger = logger

    def send(self, session, packet: DataPacket, from_id: str, to_id: str) -> None:
        self._logger.log(
            session,
            node_id=from_id,
            event_type="UNICAST_SEND",
            message=f"Forwarded packet {packet.packet_id} to {to_id}",
            data={"to": to_id, "hop_count": packet.hop_count},
        )

