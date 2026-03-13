from __future__ import annotations

from sqlmodel import select

from app.models import Node


class NodeIdentityVerification:
    def verify(self, session, node_id: str) -> bool:
        node = session.exec(select(Node).where(Node.id == node_id)).first()
        return node is not None

