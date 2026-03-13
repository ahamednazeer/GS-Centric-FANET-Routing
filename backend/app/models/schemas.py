from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.core import NodeRole, PriorityLevel, ControlType


class NodeCreate(BaseModel):
    id: str
    role: NodeRole


class NodeResponse(BaseModel):
    id: str
    role: NodeRole
    created_at: datetime
    last_seen: datetime
    lat: Optional[float] = None
    lng: Optional[float] = None
    alt: Optional[float] = None


class NeighborSnapshot(BaseModel):
    neighbor_id: str
    rssi: Optional[float] = None
    packet_loss_rate: Optional[float] = None
    mobility_vector: Optional[str] = None


class NeighborUpdateRequest(BaseModel):
    neighbors: List[NeighborSnapshot]


class FloodEmitRequest(BaseModel):
    gs_id: str
    flood_ttl: Optional[int] = None


class FloodEmitResponse(BaseModel):
    flood_sequence_number: int
    propagated_nodes: int
    accepted_nodes: int
    dropped_nodes: int


class DataGenerateRequest(BaseModel):
    source_uav_id: str
    gs_id: Optional[str] = None
    payload_type: str
    payload_size: int
    priority_level: PriorityLevel = PriorityLevel.STANDARD
    payload: Optional[str] = None
    ttl: Optional[int] = None


class DataSendResponse(BaseModel):
    packet_id: str
    status: str
    hops: int
    buffered_at: Optional[str] = None


class ControlPacketRequest(BaseModel):
    control_type: ControlType
    source_id: str
    destination_id: str
    detail: Optional[str] = None
    data: dict = Field(default_factory=dict)


class ConfigUpdateRequest(BaseModel):
    flood_interval_seconds: Optional[int] = None
    route_expiry_seconds: Optional[int] = None
    buffer_timeout_seconds: Optional[int] = None
    satellite_activation_delay_seconds: Optional[int] = None
    flood_ttl: Optional[int] = None
    max_hops: Optional[int] = None
    retry_interval_seconds: Optional[int] = None
    buffer_max_size: Optional[int] = None
    buffer_high_watermark: Optional[float] = None
    buffer_emergency_watermark: Optional[float] = None
    neighbor_min_threshold: Optional[int] = None


class TickResponse(BaseModel):
    expired_routes: int
    buffered_retries: int
    satellite_activations: int


class TickRequest(BaseModel):
    gs_id: Optional[str] = None


class SimSeedRequest(BaseModel):
    gs_id: str = "GS-CORE"
    uav_count: int = 12
    uav_prefix: str = "UAV"
    neighbor_degree: int = 2
    topology: str = "ring"
    reset: bool = True
    auto_flood: bool = True
    auto_data: bool = True
    sample_packets: int = 4


class SimSeedResponse(BaseModel):
    gs_id: str
    uav_count: int
    neighbors_created: int
    nodes_created: int
    topology: str
    flood_sequence: int | None = None
    flood_propagated: int | None = None
    sample_packets_sent: int = 0
    sample_packets_delivered: int = 0
    sample_packets_buffered: int = 0


class SimRunRequest(BaseModel):
    gs_id: str = "GS-CORE"
    duration_seconds: int = 0
    tick_interval_seconds: float = 2.0
    flood_interval_seconds: float = 10.0
    data_interval_seconds: float = 5.0
    uav_count: int = 12
    uav_prefix: str = "UAV"
    neighbor_degree: int = 2
    topology: str = "ring"
    reset: bool = True
    auto_flood: bool = True
    auto_data: bool = True
    sample_packets: int = 4


class SimStatusResponse(BaseModel):
    running: bool
    started_at: Optional[datetime] = None
    elapsed_seconds: float = 0.0
    last_tick_at: Optional[datetime] = None
    last_flood_at: Optional[datetime] = None
    last_data_at: Optional[datetime] = None
    ticks: int = 0
    config: Optional[dict] = None
