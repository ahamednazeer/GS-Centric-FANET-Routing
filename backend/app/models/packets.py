from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field

from app.models.core import ControlType, PriorityLevel


class GSFloodPacket(BaseModel):
    packet_type: Literal["FLOOD"] = "FLOOD"
    gs_id: str
    flood_sequence_number: int
    hop_count: int
    timestamp: datetime
    flood_ttl: int
    digital_signature: str


class DataPacket(BaseModel):
    packet_type: Literal["DATA"] = "DATA"
    packet_id: str
    source_uav_id: str
    destination_id: str
    creation_timestamp: datetime
    priority_level: PriorityLevel
    payload_type: str
    payload_size: int
    hop_count: int
    route_confidence_tag: float
    ttl: int
    payload: Optional[str] = None


class ControlPacket(BaseModel):
    packet_type: Literal["CONTROL"] = "CONTROL"
    control_type: ControlType
    source_id: str
    destination_id: str
    timestamp: datetime
    detail: Optional[str] = None
    data: dict = Field(default_factory=dict)


class PacketEnvelope(BaseModel):
    packet: dict
    received_by: Optional[str] = None
    received_from: Optional[str] = None

