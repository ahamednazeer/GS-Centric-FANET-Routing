from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from app.models.packets import GSFloodPacket, DataPacket, ControlPacket
from app.models.core import PriorityLevel, ControlType
from app.modules.security.auth import FloodAuthentication
from app.modules.security.encryption import LightweightEncryption


class PacketEngine:
    def __init__(self) -> None:
        self._auth = FloodAuthentication()
        self._crypto = LightweightEncryption()

    def _canonical_flood_payload(self, gs_id: str, sequence: int, timestamp: datetime, flood_ttl: int) -> str:
        return f"{gs_id}|{sequence}|{timestamp.isoformat()}|{flood_ttl}"

    def create_flood_packet(
        self,
        gs_id: str,
        sequence: int,
        flood_ttl: int,
    ) -> GSFloodPacket:
        timestamp = datetime.utcnow()
        signature_payload = self._canonical_flood_payload(gs_id, sequence, timestamp, flood_ttl)
        signature = self._auth.sign(signature_payload)
        return GSFloodPacket(
            gs_id=gs_id,
            flood_sequence_number=sequence,
            hop_count=0,
            timestamp=timestamp,
            flood_ttl=flood_ttl,
            digital_signature=signature,
        )

    def verify_flood_packet(self, packet: GSFloodPacket) -> bool:
        signature_payload = self._canonical_flood_payload(
            packet.gs_id,
            packet.flood_sequence_number,
            packet.timestamp,
            packet.flood_ttl,
        )
        return self._auth.verify(signature_payload, packet.digital_signature)

    def create_data_packet(
        self,
        source_uav_id: str,
        destination_id: str,
        priority_level: PriorityLevel,
        payload_type: str,
        payload_size: int,
        route_confidence_tag: float,
        ttl: int,
        payload: Optional[str] = None,
    ) -> DataPacket:
        packet_id = f"pkt-{uuid4().hex[:12]}"
        encrypted_payload = self._crypto.encrypt(payload) if payload else None
        return DataPacket(
            packet_id=packet_id,
            source_uav_id=source_uav_id,
            destination_id=destination_id,
            creation_timestamp=datetime.utcnow(),
            priority_level=priority_level,
            payload_type=payload_type,
            payload_size=payload_size,
            hop_count=0,
            route_confidence_tag=route_confidence_tag,
            ttl=ttl,
            payload=encrypted_payload,
        )

    def decrypt_payload(self, payload: Optional[str]) -> Optional[str]:
        if payload is None:
            return None
        return self._crypto.decrypt(payload)

    def create_control_packet(
        self,
        control_type: ControlType,
        source_id: str,
        destination_id: str,
        detail: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> ControlPacket:
        return ControlPacket(
            control_type=control_type,
            source_id=source_id,
            destination_id=destination_id,
            timestamp=datetime.utcnow(),
            detail=detail,
            data=data or {},
        )

