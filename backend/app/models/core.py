from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel, Column, JSON


class NodeRole(str, Enum):
    GS = "GS"
    UAV = "UAV"


class PacketType(str, Enum):
    FLOOD = "FLOOD"
    DATA = "DATA"
    CONTROL = "CONTROL"


class PacketStatus(str, Enum):
    CREATED = "CREATED"
    BUFFERED = "BUFFERED"
    FORWARDED = "FORWARDED"
    DELIVERED = "DELIVERED"
    DROPPED = "DROPPED"


class ControlType(str, Enum):
    ROUTE_ERROR = "ROUTE_ERROR"
    BUFFER_STATUS = "BUFFER_STATUS"
    SATELLITE_NOTICE = "SATELLITE_ACTIVATION_NOTICE"


class PriorityLevel(str, Enum):
    EMERGENCY = "EMERGENCY"
    HIGH = "HIGH"
    STANDARD = "STANDARD"


class Node(SQLModel, table=True):
    id: str = Field(primary_key=True)
    role: NodeRole = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow, index=True)
    lat: Optional[float] = None
    lng: Optional[float] = None
    alt: Optional[float] = None
    vx: Optional[float] = None
    vy: Optional[float] = None
    vz: Optional[float] = None


class Neighbor(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    node_id: str = Field(index=True)
    neighbor_id: str = Field(index=True)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    rssi: Optional[float] = None
    packet_loss_rate: Optional[float] = None
    mobility_vector: Optional[str] = None
    link_stability: Optional[float] = None


class RouteEntry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    node_id: str = Field(index=True)
    gs_id: str = Field(index=True)
    next_hop_id: str = Field(index=True)
    hop_count: int
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    route_confidence: float = 0.0
    link_quality_score: float = 0.0
    expires_at: datetime = Field(default_factory=datetime.utcnow)


class FloodState(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    node_id: str = Field(index=True)
    gs_id: str = Field(index=True)
    last_sequence: int = 0
    last_flood_at: Optional[datetime] = None


class Packet(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    packet_id: str = Field(index=True)
    packet_type: PacketType = Field(index=True)
    source_id: str = Field(index=True)
    destination_id: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    priority: Optional[PriorityLevel] = None
    payload_type: Optional[str] = None
    payload_size: Optional[int] = None
    hop_count: int = 0
    route_confidence_tag: Optional[float] = None
    ttl: int = 0
    status: PacketStatus = Field(index=True, default=PacketStatus.CREATED)
    packet_meta: dict = Field(default_factory=dict, sa_column=Column("metadata", JSON))


class BufferEntry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    node_id: str = Field(index=True)
    packet_id: str = Field(index=True)
    priority: PriorityLevel
    expiry_time: datetime = Field(index=True)
    retry_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class EventLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    node_id: Optional[str] = Field(index=True, default=None)
    event_type: str = Field(index=True)
    message: str
    data: dict = Field(default_factory=dict, sa_column=Column(JSON))


class Metric(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    key: str = Field(index=True)
    value: float
    node_id: Optional[str] = Field(default=None, index=True)


class SatelliteState(SQLModel, table=True):
    node_id: str = Field(primary_key=True)
    active: bool = False
    activated_at: Optional[datetime] = None
    last_switch: Optional[datetime] = None
    usage_rate: float = 0.0


class SystemConfig(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    flood_interval_seconds: int = 10
    route_expiry_seconds: int = 30
    buffer_timeout_seconds: int = 120
    satellite_activation_delay_seconds: int = 45
    flood_ttl: int = 6
    max_hops: int = 12
    retry_interval_seconds: int = 8
    buffer_max_size: int = 500
    buffer_high_watermark: float = 0.8
    buffer_emergency_watermark: float = 0.95
    neighbor_min_threshold: int = 1
