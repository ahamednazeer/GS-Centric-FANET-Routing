from __future__ import annotations


class TransportAbstraction:
    """Placeholder for transport interface (UDP/TCP/Mesh abstraction)."""

    def __init__(self, name: str = "udp") -> None:
        self.name = name

    def describe(self) -> str:
        return f"transport={self.name}"

