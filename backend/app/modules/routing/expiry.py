from __future__ import annotations

from app.modules.routing.route_cache import RouteCache


class RouteExpiryManager:
    def __init__(self) -> None:
        self._cache = RouteCache()

    def expire(self, session) -> int:
        return self._cache.expire_routes(session)

