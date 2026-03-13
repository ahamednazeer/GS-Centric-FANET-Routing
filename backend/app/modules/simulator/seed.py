from __future__ import annotations

import random
from datetime import datetime

from sqlmodel import select

from app.models import (
    Node,
    Neighbor,
    RouteEntry,
    FloodState,
    BufferEntry,
    Packet,
    SatelliteState,
    EventLog,
    Metric,
    NodeRole,
)


def reset_state(session) -> None:
    for model in (Neighbor, RouteEntry, FloodState, BufferEntry, Packet, SatelliteState, EventLog, Metric, Node):
        rows = session.exec(select(model)).all()
        for row in rows:
            session.delete(row)
    session.commit()


def seed_network(session, payload) -> dict:
    if getattr(payload, "reset", False):
        reset_state(session)

    gs_id = payload.gs_id
    uav_ids = [f"{payload.uav_prefix}-{i:02d}" for i in range(1, payload.uav_count + 1)]
    node_ids = [gs_id] + uav_ids

    from app.modules.mobility.movement import CENTER_LAT, CENTER_LNG
    from app.modules.communication.propagation import calculate_link_metrics

    nodes_created = 0
    # 1. Spawn nodes with physical coordinates
    for node_id in node_ids:
        role = NodeRole.GS if node_id == gs_id else NodeRole.UAV
        node = session.exec(select(Node).where(Node.id == node_id)).first()
        if node is None:
            node = Node(id=node_id, role=role)
            nodes_created += 1
        node.role = role
        node.last_seen = datetime.utcnow()
        
        # Ground Station is centered
        if role == NodeRole.GS:
            node.lat = CENTER_LAT
            node.lng = CENTER_LNG
            node.alt = 0.0
        else:
            # UAVs spawn randomly within ~2km radius initially
            import random
            node.lat = CENTER_LAT + random.uniform(-0.02, 0.02)
            node.lng = CENTER_LNG + random.uniform(-0.02, 0.02)
            node.alt = 100.0 # 100 meters altitude
            
        session.add(node)
    session.commit()

    # 2. Re-fetch to get saved coordinates for link build
    nodes = session.exec(select(Node)).all()
    
    # 3. Build initial neighbor connections through distance
    neighbors_created = 0
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            n1 = nodes[i]
            n2 = nodes[j]
            if n1.lat is None or n2.lat is None:
                continue
                
            rssi, plr = calculate_link_metrics(n1.lat, n1.lng, n2.lat, n2.lng)
            
            if plr < 1.0:
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
                neighbors_created += 2

    session.commit()

    return {
        "gs_id": gs_id,
        "uav_ids": uav_ids,
        "nodes_created": nodes_created,
        "neighbors_created": neighbors_created,
        "topology": payload.topology,
    }

