from __future__ import annotations

from datetime import datetime
from sqlmodel import select

from app.models import SatelliteState


class SatelliteActivationEngine:
    def activate(self, session, node_id: str) -> SatelliteState:
        state = session.exec(select(SatelliteState).where(SatelliteState.node_id == node_id)).first()
        if state is None:
            state = SatelliteState(node_id=node_id)
        state.active = True
        state.activated_at = state.activated_at or datetime.utcnow()
        state.last_switch = datetime.utcnow()
        session.add(state)
        session.commit()
        return state

    def deactivate(self, session, node_id: str) -> SatelliteState | None:
        state = session.exec(select(SatelliteState).where(SatelliteState.node_id == node_id)).first()
        if state is None:
            return None
        state.active = False
        state.last_switch = datetime.utcnow()
        session.add(state)
        session.commit()
        return state

