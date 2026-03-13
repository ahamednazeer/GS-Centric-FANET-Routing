from __future__ import annotations

from sqlmodel import select

from app.models import Node, RouteEntry, BufferEntry


class HealthMonitor:
    def snapshot(self, session) -> dict:
        nodes = session.exec(select(Node)).all()
        routes = session.exec(select(RouteEntry)).all()
        buffers = session.exec(select(BufferEntry)).all()
        return {
            "nodes": len(nodes),
            "routes": len(routes),
            "buffered_packets": len(buffers),
        }

