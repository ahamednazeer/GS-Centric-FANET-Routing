from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Tuple


@dataclass(frozen=True)
class RoutingTiming:
    flood_interval_seconds: int = 10
    route_expiry_seconds: int = 30
    buffer_timeout_seconds: int = 120
    satellite_activation_delay_seconds: int = 45
    flood_ttl: int = 6
    max_hops: int = 12
    retry_interval_seconds: int = 8

    @property
    def flood_interval(self) -> timedelta:
        return timedelta(seconds=self.flood_interval_seconds)

    @property
    def route_expiry(self) -> timedelta:
        return timedelta(seconds=self.route_expiry_seconds)

    @property
    def buffer_timeout(self) -> timedelta:
        return timedelta(seconds=self.buffer_timeout_seconds)

    @property
    def satellite_activation_delay(self) -> timedelta:
        return timedelta(seconds=self.satellite_activation_delay_seconds)


@dataclass(frozen=True)
class BufferConfig:
    max_size: int = 500
    high_watermark: float = 0.8
    emergency_watermark: float = 0.95


@dataclass(frozen=True)
class MobilityConfig:
    mobility_speed_range_mps: Tuple[float, float] = (5.0, 35.0)
    avg_radio_range_m: float = 1500.0
    channel_bandwidth_mbps: float = 20.0
    expected_node_density: int = 50
    expected_gs_distance_m: float = 8000.0
    neighbor_min_threshold: int = 1


@dataclass(frozen=True)
class SecurityConfig:
    hmac_key_env: str = "FANET_HMAC_KEY"
    encryption_key_env: str = "FANET_ENC_KEY"


DEFAULT_TIMING = RoutingTiming()
DEFAULT_BUFFER = BufferConfig()
DEFAULT_MOBILITY = MobilityConfig()
DEFAULT_SECURITY = SecurityConfig()

