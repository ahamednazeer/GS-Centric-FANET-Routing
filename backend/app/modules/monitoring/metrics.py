from __future__ import annotations

from sqlmodel import select

from app.models import Metric


class MetricsCollector:
    def increment(self, session, key: str, amount: float = 1.0, node_id: str | None = None) -> None:
        metric = Metric(key=key, value=amount, node_id=node_id)
        session.add(metric)
        session.commit()

    def aggregate(self, session, key: str, node_id: str | None = None) -> float:
        statement = select(Metric).where(Metric.key == key)
        if node_id:
            statement = statement.where(Metric.node_id == node_id)
        rows = session.exec(statement).all()
        return sum(row.value for row in rows)

