from __future__ import annotations


class TrafficShaper:
    def __init__(self, max_kbps: float = 256.0) -> None:
        self.max_kbps = max_kbps

    def allow(self, payload_size: int) -> bool:
        return payload_size <= (self.max_kbps * 1024)

