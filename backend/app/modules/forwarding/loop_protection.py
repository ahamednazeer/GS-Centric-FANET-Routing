from __future__ import annotations

from collections import deque
from typing import Deque, Dict


class LoopProtection:
    def __init__(self, max_history: int = 200) -> None:
        self._history: Dict[str, Deque[str]] = {}
        self._max_history = max_history

    def seen(self, node_id: str, packet_id: str) -> bool:
        history = self._history.setdefault(node_id, deque(maxlen=self._max_history))
        if packet_id in history:
            return True
        history.append(packet_id)
        return False

