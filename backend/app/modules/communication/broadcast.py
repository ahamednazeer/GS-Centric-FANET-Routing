from __future__ import annotations

from app.modules.simulator.network import NetworkSimulator
from app.models.packets import GSFloodPacket


class BroadcastManager:
    def __init__(self, simulator: NetworkSimulator) -> None:
        self._simulator = simulator

    def broadcast_flood(self, session, flood_packet: GSFloodPacket) -> dict:
        return self._simulator.propagate_flood(session, flood_packet)

