from __future__ import annotations

import base64
import zlib


class CompressionEngine:
    def compress(self, payload: str) -> str:
        compressed = zlib.compress(payload.encode("utf-8"))
        return base64.b64encode(compressed).decode("utf-8")

    def decompress(self, payload: str) -> str:
        data = base64.b64decode(payload.encode("utf-8"))
        return zlib.decompress(data).decode("utf-8")

