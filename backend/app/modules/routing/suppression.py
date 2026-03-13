from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass
class FloodRecord:
    sequence: int
    hop_count: int


class FloodSuppressionController:
    def __init__(self) -> None:
        self._records: Dict[Tuple[str, str], FloodRecord] = {}

    def should_rebroadcast(self, node_id: str, gs_id: str, sequence: int, hop_count: int) -> bool:
        key = (node_id, gs_id)
        record = self._records.get(key)
        if record is None:
            self._records[key] = FloodRecord(sequence=sequence, hop_count=hop_count)
            return True
        if sequence > record.sequence:
            self._records[key] = FloodRecord(sequence=sequence, hop_count=hop_count)
            return True
        if sequence == record.sequence and hop_count < record.hop_count:
            self._records[key] = FloodRecord(sequence=sequence, hop_count=hop_count)
            return True
        return False

