from __future__ import annotations

import base64
import os
from typing import Optional

from app.config import DEFAULT_SECURITY

try:
    from cryptography.fernet import Fernet, InvalidToken
except Exception:  # pragma: no cover - fallback when cryptography missing
    Fernet = None
    InvalidToken = Exception


class LightweightEncryption:
    def __init__(self, key: Optional[bytes] = None) -> None:
        if key is None:
            env_key = os.getenv(DEFAULT_SECURITY.encryption_key_env)
            if env_key:
                key = env_key.encode("utf-8")
            elif Fernet is not None:
                key = Fernet.generate_key()
        self._key = key
        self._fernet = Fernet(key) if Fernet is not None and key is not None else None

    def encrypt(self, payload: str) -> str:
        if self._fernet is None:
            return base64.b64encode(payload.encode("utf-8")).decode("utf-8")
        return self._fernet.encrypt(payload.encode("utf-8")).decode("utf-8")

    def decrypt(self, payload: str) -> str:
        if self._fernet is None:
            return base64.b64decode(payload.encode("utf-8")).decode("utf-8")
        try:
            return self._fernet.decrypt(payload.encode("utf-8")).decode("utf-8")
        except InvalidToken:
            return ""

