from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.config import DEFAULT_TIMING, DEFAULT_BUFFER, DEFAULT_MOBILITY
from app.db import get_session
from app.models import (
    Node,
    Neighbor,
    BufferEntry,
    EventLog,
    SystemConfig,
    NodeRole,
    SatelliteState,
    RouteEntry,
    FloodState,
    Packet,
    Metric,
    PriorityLevel,
)
from app.models.schemas import (
    NodeCreate,
    NodeResponse,
    NeighborUpdateRequest,
    FloodEmitRequest,
    FloodEmitResponse,
    DataGenerateRequest,
    DataSendResponse,
    ControlPacketRequest,
    ConfigUpdateRequest,
    TickResponse,
    TickRequest,
    SimSeedRequest,
    SimSeedResponse,
    SimRunRequest,
    SimStatusResponse,
)
from app.modules.communication.packet_engine import PacketEngine
from app.modules.communication.broadcast import BroadcastManager
from app.modules.communication.unicast import UnicastEngine
from app.modules.forwarding.forwarding_engine import ForwardingEngine
from app.modules.forwarding.data_pipeline import DataPipelineManager
from app.modules.routing.gs_flood import GSFloodGenerator
from app.modules.buffering.retry import RetryScheduler
from app.modules.buffering.congestion import CongestionController
from app.modules.mobility.neighbor_tracking import NeighborTrackingEngine
from app.modules.mobility.route_confidence import RouteConfidenceScorer
from app.modules.monitoring.health import HealthMonitor
from app.modules.monitoring.performance import PerformanceAnalyzer
from app.modules.monitoring.metrics import MetricsCollector
from app.modules.monitoring.events import EventLogger
from app.modules.satellite.partition import PartitionDetector
from app.modules.satellite.activation import SatelliteActivationEngine
from app.modules.simulator.network import NetworkSimulator
from app.modules.simulator.seed import seed_network
from app.modules.simulator.controller import controller, SimulationConfig
from app.modules.mobility.movement import MovementEngine
from app.modules.communication.propagation import calculate_link_metrics

router = APIRouter()


# Dependencies

def get_db():
    with get_session() as session:
        yield session


# Helpers

def get_or_create_config(session: Session) -> SystemConfig:
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


def resolve_gs_id(session: Session, candidate: str | None = None) -> str:
    if candidate:
        return candidate
    gs = session.exec(select(Node).where(Node.role == NodeRole.GS)).first()
    return gs.id if gs else "GS-1"


# Routes

@router.get("/")
def root():
    return {"status": "fanet-routing-ready"}


@router.post("/nodes", response_model=NodeResponse)
def create_node(payload: NodeCreate, session: Session = Depends(get_db)):
    existing = session.exec(select(Node).where(Node.id == payload.id)).first()
    if existing:
        existing.role = payload.role
        existing.last_seen = datetime.utcnow()
        session.add(existing)
        session.commit()
        return NodeResponse(
            id=existing.id,
            role=existing.role,
            created_at=existing.created_at,
            last_seen=existing.last_seen,
        )
    node = Node(id=payload.id, role=payload.role)
    session.add(node)
    session.commit()
    return NodeResponse(id=node.id, role=node.role, created_at=node.created_at, last_seen=node.last_seen)


@router.get("/nodes", response_model=List[NodeResponse])
def list_nodes(session: Session = Depends(get_db)):
    nodes = session.exec(select(Node)).all()
    return [NodeResponse(id=n.id, role=n.role, created_at=n.created_at, last_seen=n.last_seen) for n in nodes]


@router.post("/neighbors/{node_id}")
def update_neighbors(node_id: str, payload: NeighborUpdateRequest, session: Session = Depends(get_db)):
    node = session.exec(select(Node).where(Node.id == node_id)).first()
    if node is None:
        node = Node(id=node_id, role=NodeRole.UAV)
    node.last_seen = datetime.utcnow()
    session.add(node)
    session.commit()
    tracker = NeighborTrackingEngine()
    tracker.update_neighbors(session, node_id=node_id, neighbors=[n.dict() for n in payload.neighbors])
    return {"status": "updated", "count": len(payload.neighbors)}


@router.get("/neighbors/{node_id}")
def list_neighbors(node_id: str, session: Session = Depends(get_db)):
    neighbors = session.exec(select(Neighbor).where(Neighbor.node_id == node_id)).all()
    return neighbors


@router.post("/flood/emit", response_model=FloodEmitResponse)
def emit_flood(payload: FloodEmitRequest, session: Session = Depends(get_db)):
    config = get_or_create_config(session)
    gs_node = session.exec(select(Node).where(Node.id == payload.gs_id)).first()
    if gs_node is None:
        gs_node = Node(id=payload.gs_id, role=NodeRole.GS)
    gs_node.last_seen = datetime.utcnow()
    session.add(gs_node)
    session.commit()
    generator = GSFloodGenerator()
    simulator = NetworkSimulator(route_expiry=timedelta(seconds=config.route_expiry_seconds))
    broadcaster = BroadcastManager(simulator)

    packet = generator.emit(session, gs_id=payload.gs_id, flood_ttl=payload.flood_ttl or config.flood_ttl)
    result = broadcaster.broadcast_flood(session, packet)

    return FloodEmitResponse(
        flood_sequence_number=packet.flood_sequence_number,
        propagated_nodes=result["propagated_nodes"],
        accepted_nodes=result["accepted_nodes"],
        dropped_nodes=result["dropped_nodes"],
    )


@router.post("/data/send", response_model=DataSendResponse)
def send_data(payload: DataGenerateRequest, session: Session = Depends(get_db)):
    config = get_or_create_config(session)
    gs_id = resolve_gs_id(session, payload.gs_id)
    source_node = session.exec(select(Node).where(Node.id == payload.source_uav_id)).first()
    if source_node is None:
        source_node = Node(id=payload.source_uav_id, role=NodeRole.UAV)
    source_node.last_seen = datetime.utcnow()
    session.add(source_node)
    session.commit()
    packet_engine = PacketEngine()
    confidence_scorer = RouteConfidenceScorer()

    route_confidence = confidence_scorer.score(session, payload.source_uav_id, gs_id)
    ttl = payload.ttl if payload.ttl is not None else config.max_hops

    data_packet = packet_engine.create_data_packet(
        source_uav_id=payload.source_uav_id,
        destination_id=gs_id,
        priority_level=payload.priority_level,
        payload_type=payload.payload_type,
        payload_size=payload.payload_size,
        route_confidence_tag=route_confidence,
        ttl=ttl,
        payload=payload.payload,
    )

    logger = EventLogger()
    unicast = UnicastEngine(logger)
    forwarding_engine = ForwardingEngine(unicast=unicast)
    pipeline = DataPipelineManager(
        forwarding_engine=forwarding_engine,
        buffer_timeout=timedelta(seconds=config.buffer_timeout_seconds),
        max_hops=config.max_hops,
    )

    status, hops = pipeline.send(session, data_packet, gs_id)
    buffered_at = None
    if status == "BUFFER":
        entry = session.exec(select(BufferEntry).where(BufferEntry.packet_id == data_packet.packet_id)).first()
        if entry:
            buffered_at = entry.created_at.isoformat()

    return DataSendResponse(packet_id=data_packet.packet_id, status=status, hops=hops, buffered_at=buffered_at)


@router.post("/control/send")
def send_control(payload: ControlPacketRequest, session: Session = Depends(get_db)):
    packet_engine = PacketEngine()
    control_packet = packet_engine.create_control_packet(
        control_type=payload.control_type,
        source_id=payload.source_id,
        destination_id=payload.destination_id,
        detail=payload.detail,
        data=payload.data,
    )
    logger = EventLogger()
    logger.log(
        session,
        node_id=payload.source_id,
        event_type="CONTROL",
        message=f"{payload.control_type} to {payload.destination_id}",
        data=control_packet.dict(),
    )
    return {"status": "sent", "packet": control_packet}


@router.get("/routes")
def list_routes(session: Session = Depends(get_db)):
    routes = session.exec(select(RouteEntry)).all()
    return routes


@router.get("/buffer")
def list_buffer(session: Session = Depends(get_db)):
    entries = session.exec(select(BufferEntry)).all()
    return entries


@router.get("/satellite")
def list_satellite(session: Session = Depends(get_db)):
    states = session.exec(select(SatelliteState)).all()
    return states


@router.get("/metrics/summary")
def metrics_summary(session: Session = Depends(get_db)):
    analyzer = PerformanceAnalyzer()
    return analyzer.summary(session)


@router.get("/metrics/counters")
def metrics_counters(session: Session = Depends(get_db)):
    collector = MetricsCollector()
    keys = [
        "packet_delivered",
        "packet_forwarded",
        "packet_buffered",
        "packet_dropped",
        "packet_drop_loop",
        "packet_drop_ttl",
        "packet_drop_max_hops",
        "flood_propagated",
    ]
    return {key: collector.aggregate(session, key) for key in keys}


@router.get("/events")
def list_events(session: Session = Depends(get_db)):
    events = session.exec(select(EventLog).order_by(EventLog.timestamp.desc())).all()
    return events[:50]


@router.get("/health")
def health(session: Session = Depends(get_db)):
    monitor = HealthMonitor()
    return monitor.snapshot(session)


@router.get("/config")
def get_config(session: Session = Depends(get_db)):
    return get_or_create_config(session)


@router.get("/assumptions")
def get_assumptions():
    return {
        "mobility_speed_range_mps": DEFAULT_MOBILITY.mobility_speed_range_mps,
        "avg_radio_range_m": DEFAULT_MOBILITY.avg_radio_range_m,
        "channel_bandwidth_mbps": DEFAULT_MOBILITY.channel_bandwidth_mbps,
        "expected_node_density": DEFAULT_MOBILITY.expected_node_density,
        "expected_gs_distance_m": DEFAULT_MOBILITY.expected_gs_distance_m,
    }


@router.put("/config")
def update_config(payload: ConfigUpdateRequest, session: Session = Depends(get_db)):
    config = get_or_create_config(session)
    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(config, key, value)
    session.add(config)
    session.commit()
    return config


@router.post("/tick", response_model=TickResponse)
def tick(payload: TickRequest, session: Session = Depends(get_db)):
    config = get_or_create_config(session)
    gs_id = resolve_gs_id(session, payload.gs_id)

    expiry_manager = RouteCacheExpirer()
    expired = expiry_manager.expire(session)

    logger = EventLogger()
    forwarding_engine = ForwardingEngine(unicast=UnicastEngine(logger))
    retry_scheduler = RetryScheduler(forwarding_engine)
    buffered_retries = retry_scheduler.retry(session, gs_id)

    congestion = CongestionController(
        max_size=config.buffer_max_size,
        high_watermark=config.buffer_high_watermark,
        emergency_watermark=config.buffer_emergency_watermark,
    )
    congestion.enforce(session)

    # 1. Update Physical Mobility
    movement = MovementEngine(tick_duration_seconds=controller.config.tick_interval_seconds if controller.config else 2.0)
    movement.step(session)

    # 2. Recalculate Neighbor Links based on new positions
    _update_neighbor_links(session, config.neighbor_min_threshold)

    detector = PartitionDetector()
    activation_engine = SatelliteActivationEngine()
    nodes = session.exec(select(Node).where(Node.role == NodeRole.UAV)).all()
    activations = 0
    for node in nodes:
        if detector.is_partitioned(
            session,
            node_id=node.id,
            gs_id=gs_id,
            activation_delay=timedelta(seconds=config.satellite_activation_delay_seconds),
            neighbor_threshold=config.neighbor_min_threshold,
        ):
            activation_engine.activate(session, node.id)
            activations += 1

    return TickResponse(expired_routes=expired, buffered_retries=buffered_retries, satellite_activations=activations)


@router.post("/simulate/seed", response_model=SimSeedResponse)
def seed_simulation(payload: SimSeedRequest, session: Session = Depends(get_db)):
    config = get_or_create_config(session)
    seed_result = seed_network(session, payload)
    gs_id = seed_result["gs_id"]
    uav_ids = seed_result["uav_ids"]
    nodes_created = seed_result["nodes_created"]
    neighbors_created = seed_result["neighbors_created"]

    flood_sequence = None
    flood_propagated = None
    if payload.auto_flood:
        generator = GSFloodGenerator()
        simulator = NetworkSimulator(route_expiry=timedelta(seconds=config.route_expiry_seconds))
        broadcaster = BroadcastManager(simulator)
        flood_packet = generator.emit(session, gs_id=gs_id, flood_ttl=config.flood_ttl)
        flood_result = broadcaster.broadcast_flood(session, flood_packet)
        flood_sequence = flood_packet.flood_sequence_number
        flood_propagated = flood_result.get("propagated_nodes")

    packets_sent = 0
    packets_delivered = 0
    packets_buffered = 0
    if payload.auto_data:
        packet_engine = PacketEngine()
        scorer = RouteConfidenceScorer()
        logger = EventLogger()
        forwarding_engine = ForwardingEngine(unicast=UnicastEngine(logger))
        pipeline = DataPipelineManager(
            forwarding_engine=forwarding_engine,
            buffer_timeout=timedelta(seconds=config.buffer_timeout_seconds),
            max_hops=config.max_hops,
        )
        sample_count = max(0, min(payload.sample_packets, len(uav_ids)))
        for i in range(sample_count):
            source_id = uav_ids[i]
            confidence = scorer.score(session, source_id, gs_id)
            data_packet = packet_engine.create_data_packet(
                source_uav_id=source_id,
                destination_id=gs_id,
                priority_level=PriorityLevel.STANDARD,
                payload_type="telemetry",
                payload_size=128,
                route_confidence_tag=confidence,
                ttl=config.max_hops,
                payload="sample",
            )
            status, _ = pipeline.send(session, data_packet, gs_id)
            packets_sent += 1
            if status == "DELIVERED":
                packets_delivered += 1
            if status == "BUFFER":
                packets_buffered += 1

    return SimSeedResponse(
        gs_id=gs_id,
        uav_count=payload.uav_count,
        neighbors_created=neighbors_created,
        nodes_created=nodes_created,
        topology=payload.topology,
        flood_sequence=flood_sequence,
        flood_propagated=flood_propagated,
        sample_packets_sent=packets_sent,
        sample_packets_delivered=packets_delivered,
        sample_packets_buffered=packets_buffered,
    )


@router.post("/simulate/run", response_model=SimStatusResponse)
def simulate_run(payload: SimRunRequest):
    config = SimulationConfig(
        gs_id=payload.gs_id,
        duration_seconds=payload.duration_seconds,
        tick_interval_seconds=payload.tick_interval_seconds,
        flood_interval_seconds=payload.flood_interval_seconds,
        data_interval_seconds=payload.data_interval_seconds,
        uav_count=payload.uav_count,
        uav_prefix=payload.uav_prefix,
        neighbor_degree=payload.neighbor_degree,
        topology=payload.topology,
        reset=payload.reset,
        auto_flood=payload.auto_flood,
        auto_data=payload.auto_data,
        sample_packets=payload.sample_packets,
    )
    return controller.start(config)


@router.post("/simulate/stop", response_model=SimStatusResponse)
def simulate_stop():
    return controller.stop()


@router.get("/simulate/status", response_model=SimStatusResponse)
def simulate_status():
    return controller.status()


class RouteCacheExpirer:
    def __init__(self) -> None:
        from app.modules.routing.expiry import RouteExpiryManager

        self._manager = RouteExpiryManager()

    def expire(self, session: Session) -> int:
        return self._manager.expire(session)

def _update_neighbor_links(session: Session, min_threshold: int) -> None:
    # Get all nodes that have coordinates
    nodes = session.exec(select(Node).where(Node.lat != None)).all()
    
    # We will completely rebuild the Neighbor table based on distance
    session.exec(select(Neighbor)) # Just to make sure we don't accidentally drop things? 
    # Actually, a better approach is to clear and rebuild, or update existing.
    # For simplicity of the simulation tick, let's clear and rebuild.
    existing_neighbors = session.exec(select(Neighbor)).all()
    for n in existing_neighbors:
        session.delete(n)
        
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            n1 = nodes[i]
            n2 = nodes[j]
            if n1.lat is None or n2.lat is None:
                continue
                
            rssi, plr = calculate_link_metrics(n1.lat, n1.lng, n2.lat, n2.lng)
            
            # If PLR is 1.0, the link is dead, do not add as neighbor
            if plr < 1.0:
                # Add bi-directional links
                session.add(Neighbor(
                    node_id=n1.id,
                    neighbor_id=n2.id,
                    rssi=rssi,
                    packet_loss_rate=plr,
                    last_seen=datetime.utcnow()
                ))
                session.add(Neighbor(
                    node_id=n2.id,
                    neighbor_id=n1.id,
                    rssi=rssi,
                    packet_loss_rate=plr,
                    last_seen=datetime.utcnow()
                ))
    session.commit()
