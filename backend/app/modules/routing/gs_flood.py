from __future__ import annotations

import random
from datetime import datetime

from sqlmodel import select

from app.config import DEFAULT_TIMING
from app.models import FloodState
from app.models.packets import GSFloodPacket
from app.modules.communication.packet_engine import PacketEngine
from app.modules.mobility.route_confidence import RouteConfidenceScorer
from app.modules.mobility.link_stability import LinkStabilityAnalyzer
from app.modules.monitoring.events import EventLogger
from app.modules.routing.route_cache import RouteCache
from app.modules.routing.route_evaluator import RouteEvaluator
from app.modules.routing.suppression import FloodSuppressionController
from app.modules.security.replay import ReplayProtection


class GSFloodGenerator:
    def __init__(self) -> None:
        self._packet_engine = PacketEngine()

    def next_sequence(self, session, gs_id: str) -> int:
        state = session.exec(
            select(FloodState).where(FloodState.node_id == gs_id, FloodState.gs_id == gs_id)
        ).first()
        if state is None:
            state = FloodState(node_id=gs_id, gs_id=gs_id, last_sequence=1, last_flood_at=datetime.utcnow())
            session.add(state)
            session.commit()
            return 1
        state.last_sequence += 1
        state.last_flood_at = datetime.utcnow()
        session.add(state)
        session.commit()
        return state.last_sequence

    def emit(self, session, gs_id: str, flood_ttl: int | None = None) -> GSFloodPacket:
        ttl = flood_ttl if flood_ttl is not None else DEFAULT_TIMING.flood_ttl
        sequence = self.next_sequence(session, gs_id)
        return self._packet_engine.create_flood_packet(gs_id=gs_id, sequence=sequence, flood_ttl=ttl)


class FloodReceiver:
    def __init__(self) -> None:
        self._packet_engine = PacketEngine()
        self._replay = ReplayProtection()
        self._route_cache = RouteCache()
        self._route_evaluator = RouteEvaluator()
        self._suppression = FloodSuppressionController()
        self._route_confidence = RouteConfidenceScorer()
        self._link_stability = LinkStabilityAnalyzer()
        self._logger = EventLogger()

    def process(
        self,
        session,
        receiver_id: str,
        sender_id: str,
        packet: GSFloodPacket,
        route_expiry=None,
    ) -> tuple[bool, float]:
        if not self._packet_engine.verify_flood_packet(packet):
            self._logger.log(session, receiver_id, "FLOOD_REJECT", "Invalid flood signature")
            return False, 0.0
        if self._replay.is_replay(session, receiver_id, packet.gs_id, packet.flood_sequence_number):
            self._logger.log(session, receiver_id, "FLOOD_REJECT", "Replay flood detected")
            return False, 0.0

        stored_state = session.exec(
            select(FloodState).where(FloodState.node_id == receiver_id, FloodState.gs_id == packet.gs_id)
        ).first()
        stored_sequence = stored_state.last_sequence if stored_state else None
        current_route = self._route_cache.get_route(session, receiver_id, packet.gs_id)
        new_hop = packet.hop_count + 1
        if not self._route_evaluator.should_accept(packet.flood_sequence_number, stored_sequence, new_hop, current_route):
            return False, 0.0

        link_quality = self._link_stability.link_quality(session, receiver_id, sender_id)
        route_confidence = self._route_confidence.score(session, receiver_id, packet.gs_id, link_quality)
        expiry = route_expiry or DEFAULT_TIMING.route_expiry
        self._route_cache.update_route(
            session=session,
            node_id=receiver_id,
            gs_id=packet.gs_id,
            next_hop_id=sender_id,
            hop_count=new_hop,
            route_confidence=route_confidence,
            link_quality_score=link_quality,
            expiry=expiry,
        )

        jitter = random.uniform(0.02, 0.2)
        self._logger.log(
            session,
            receiver_id,
            "FLOOD_ACCEPT",
            f"Accepted flood seq {packet.flood_sequence_number}",
            data={"hop_count": new_hop, "jitter": jitter},
        )

        should_rebroadcast = self._suppression.should_rebroadcast(
            node_id=receiver_id,
            gs_id=packet.gs_id,
            sequence=packet.flood_sequence_number,
            hop_count=new_hop,
        )
        return should_rebroadcast, jitter
