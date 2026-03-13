from __future__ import annotations

from typing import Optional

from app.models import RouteEntry


class RouteEvaluator:
    def should_accept(self, sequence: int, stored_sequence: int | None, hop: int, stored_route: Optional[RouteEntry]) -> bool:
        if stored_sequence is None:
            return True
        if sequence > stored_sequence:
            return True
        if sequence == stored_sequence and stored_route is not None:
            return hop < stored_route.hop_count
        if sequence == stored_sequence and stored_route is None:
            return True
        return False

