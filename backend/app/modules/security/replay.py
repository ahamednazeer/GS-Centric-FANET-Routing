from __future__ import annotations

from datetime import datetime
from sqlmodel import select

from app.models import FloodState


class ReplayProtection:
    def is_replay(self, session, node_id: str, gs_id: str, sequence: int) -> bool:
        state = session.exec(
            select(FloodState).where(FloodState.node_id == node_id, FloodState.gs_id == gs_id)
        ).first()
        if state is None:
            state = FloodState(node_id=node_id, gs_id=gs_id, last_sequence=sequence, last_flood_at=datetime.utcnow())
            session.add(state)
            session.commit()
            return False
        if sequence < state.last_sequence:
            return True
        if sequence > state.last_sequence:
            state.last_sequence = sequence
            state.last_flood_at = datetime.utcnow()
            session.add(state)
            session.commit()
        return False

