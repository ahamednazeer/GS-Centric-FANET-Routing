from __future__ import annotations

import hmac
import hashlib
import os
from typing import Optional

from app.config import DEFAULT_SECURITY


class FloodAuthentication:
    def __init__(self, key: Optional[bytes] = None) -> None:
        if key is None:
            env_key = os.getenv(DEFAULT_SECURITY.hmac_key_env, "")
            key = env_key.encode("utf-8") if env_key else b"fanet-default-hmac-key"
        self._key = key

    def sign(self, payload: str) -> str:
        digest = hmac.new(self._key, payload.encode("utf-8"), hashlib.sha256).hexdigest()
        return digest

    def verify(self, payload: str, signature: str) -> bool:
        expected = self.sign(payload)
        return hmac.compare_digest(expected, signature)

