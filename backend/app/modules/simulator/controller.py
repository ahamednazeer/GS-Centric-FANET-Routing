from __future__ import annotations

import threading
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

from sqlmodel import select

from app.config import DEFAULT_BUFFER, DEFAULT_MOBILITY, DEFAULT_TIMING
from app.db import init_db, get_session
from app.models import (
    Node,
    NodeRole,
    SystemConfig,
    PriorityLevel,
)
from app.modules.simulator.seed import seed_network
from app.modules.communication.packet_engine import PacketEngine
from app.modules.communication.broadcast import BroadcastManager
from app.modules.communication.unicast import UnicastEngine
from app.modules.forwarding.forwarding_engine import ForwardingEngine
from app.modules.forwarding.data_pipeline import DataPipelineManager
from app.modules.routing.gs_flood import GSFloodGenerator
from app.modules.simulator.network import NetworkSimulator
from app.modules.routing.expiry import RouteExpiryManager
from app.modules.buffering.retry import RetryScheduler
from app.modules.buffering.congestion import CongestionController
from app.modules.satellite.partition import PartitionDetector
from app.modules.satellite.activation import SatelliteActivationEngine
from app.modules.monitoring.events import EventLogger
from app.modules.mobility.route_confidence import RouteConfidenceScorer


@dataclass
class SimulationConfig:
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


class SimulationController:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._stop_event: threading.Event | None = None
        self._status: dict = {
            "running": False,
            "started_at": None,
            "elapsed_seconds": 0.0,
            "last_tick_at": None,
            "last_flood_at": None,
            "last_data_at": None,
            "ticks": 0,
            "config": None,
        }

    def start(self, config: SimulationConfig) -> dict:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return self._status
            self._stop_event = threading.Event()
            self._status.update(
                {
                    "running": True,
                    "started_at": datetime.utcnow(),
                    "elapsed_seconds": 0.0,
                    "last_tick_at": None,
                    "last_flood_at": None,
                    "last_data_at": None,
                    "ticks": 0,
                    "config": asdict(config),
                }
            )
            self._thread = threading.Thread(target=self._run, args=(config, self._stop_event), daemon=True)
            self._thread.start()
        return self._status

    def stop(self) -> dict:
        with self._lock:
            if self._stop_event:
                self._stop_event.set()
            self._status["running"] = False
        return self._status

    def status(self) -> dict:
        with self._lock:
            return dict(self._status)

    def _get_or_create_config(self, session) -> SystemConfig:
        config = session.exec(select(SystemConfig)).first()
        if config is None:
            config = SystemConfig(
                flood_interval_seconds=DEFAULT_TIMING.flood_interval_seconds,
                route_expiry_seconds=DEFAULT_TIMING.route_expiry_seconds,
                buffer_timeout_seconds=DEFAULT_TIMING.buffer_timeout_seconds,
                satellite_activation_delay_seconds=DEFAULT_TIMING.satellite_activation_delay_seconds,
                flood_ttl=DEFAULT_TIMING.flood_ttl,
                max_hops=DEFAULT_TIMING.max_hops,
                retry_interval_seconds=DEFAULT_TIMING.retry_interval_seconds,
                buffer_max_size=DEFAULT_BUFFER.max_size,
                buffer_high_watermark=DEFAULT_BUFFER.high_watermark,
                buffer_emergency_watermark=DEFAULT_BUFFER.emergency_watermark,
                neighbor_min_threshold=DEFAULT_MOBILITY.neighbor_min_threshold,
            )
            session.add(config)
            session.commit()
        return config

    def _run(self, config: SimulationConfig, stop_event: threading.Event) -> None:
        init_db()
        logger = EventLogger()
        packet_engine = PacketEngine()
        scorer = RouteConfidenceScorer()

        with get_session() as session:
            system_config = self._get_or_create_config(session)
            seed_payload = config
            seed_result = seed_network(session, seed_payload)
            uav_ids = seed_result["uav_ids"]

            if config.auto_flood:
                generator = GSFloodGenerator()
                simulator = NetworkSimulator(route_expiry=timedelta(seconds=system_config.route_expiry_seconds))
                broadcaster = BroadcastManager(simulator)
                flood_packet = generator.emit(session, gs_id=config.gs_id, flood_ttl=system_config.flood_ttl)
                broadcaster.broadcast_flood(session, flood_packet)
                self._status["last_flood_at"] = datetime.utcnow()

            if config.auto_data:
                forwarding_engine = ForwardingEngine(unicast=UnicastEngine(logger))
                pipeline = DataPipelineManager(
                    forwarding_engine=forwarding_engine,
                    buffer_timeout=timedelta(seconds=system_config.buffer_timeout_seconds),
                    max_hops=system_config.max_hops,
                )
                sample_count = max(0, min(config.sample_packets, len(uav_ids)))
                for i in range(sample_count):
                    source_id = uav_ids[i]
                    confidence = scorer.score(session, source_id, config.gs_id)
                    data_packet = packet_engine.create_data_packet(
                        source_uav_id=source_id,
                        destination_id=config.gs_id,
                        priority_level=PriorityLevel.STANDARD,
                        payload_type="telemetry",
                        payload_size=128,
                        route_confidence_tag=confidence,
                        ttl=system_config.max_hops,
                        payload="sample",
                    )
                    pipeline.send(session, data_packet, config.gs_id)
                self._status["last_data_at"] = datetime.utcnow()

        start_time = time.time()
        next_tick = start_time + config.tick_interval_seconds
        next_flood = start_time + config.flood_interval_seconds
        next_data = start_time + config.data_interval_seconds

        while not stop_event.is_set():
            now = time.time()
            elapsed = now - start_time
            if config.duration_seconds and elapsed >= config.duration_seconds:
                break

            with get_session() as session:
                system_config = self._get_or_create_config(session)

                if now >= next_flood:
                    generator = GSFloodGenerator()
                    simulator = NetworkSimulator(route_expiry=timedelta(seconds=system_config.route_expiry_seconds))
                    broadcaster = BroadcastManager(simulator)
                    flood_packet = generator.emit(session, gs_id=config.gs_id, flood_ttl=system_config.flood_ttl)
                    broadcaster.broadcast_flood(session, flood_packet)
                    self._status["last_flood_at"] = datetime.utcnow()
                    next_flood = now + config.flood_interval_seconds

                if now >= next_data:
                    forwarding_engine = ForwardingEngine(unicast=UnicastEngine(logger))
                    pipeline = DataPipelineManager(
                        forwarding_engine=forwarding_engine,
                        buffer_timeout=timedelta(seconds=system_config.buffer_timeout_seconds),
                        max_hops=system_config.max_hops,
                    )
                    sample = uav_ids[: max(1, min(config.sample_packets, len(uav_ids)))]
                    for source_id in sample:
                        confidence = scorer.score(session, source_id, config.gs_id)
                        data_packet = packet_engine.create_data_packet(
                            source_uav_id=source_id,
                            destination_id=config.gs_id,
                            priority_level=PriorityLevel.STANDARD,
                            payload_type="telemetry",
                            payload_size=128,
                            route_confidence_tag=confidence,
                            ttl=system_config.max_hops,
                            payload="sample",
                        )
                        pipeline.send(session, data_packet, config.gs_id)
                    self._status["last_data_at"] = datetime.utcnow()
                    next_data = now + config.data_interval_seconds

                if now >= next_tick:
                    expiry_manager = RouteExpiryManager()
                    expired = expiry_manager.expire(session)

                    forwarding_engine = ForwardingEngine(unicast=UnicastEngine(logger))
                    retry_scheduler = RetryScheduler(forwarding_engine)
                    retry_scheduler.retry(session, config.gs_id)

                    congestion = CongestionController(
                        max_size=system_config.buffer_max_size,
                        high_watermark=system_config.buffer_high_watermark,
                        emergency_watermark=system_config.buffer_emergency_watermark,
                    )
                    congestion.enforce(session)

                    detector = PartitionDetector()
                    activation_engine = SatelliteActivationEngine()
                    nodes = session.exec(select(Node).where(Node.role == NodeRole.UAV)).all()
                    for node in nodes:
                        if detector.is_partitioned(
                            session,
                            node_id=node.id,
                            gs_id=config.gs_id,
                            activation_delay=timedelta(seconds=system_config.satellite_activation_delay_seconds),
                            neighbor_threshold=system_config.neighbor_min_threshold,
                        ):
                            activation_engine.activate(session, node.id)

                    self._status["last_tick_at"] = datetime.utcnow()
                    self._status["ticks"] = self._status.get("ticks", 0) + 1
                    next_tick = now + config.tick_interval_seconds

            with self._lock:
                self._status["elapsed_seconds"] = elapsed

            time.sleep(0.2)

        with self._lock:
            self._status["running"] = False


controller = SimulationController()

