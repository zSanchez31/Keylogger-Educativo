from __future__ import annotations

import base64
import hashlib
import os
from pathlib import Path

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes


class Encryptor:
    def __init__(self, key: bytes | None = None, key_file: Path | str | None = None) -> None:
        self.key_file = Path(key_file) if key_file else Path("config/.key")
        self.key = key if key else self._load_or_create_key()

    def _load_or_create_key(self) -> bytes:
        if self.key_file.exists():
            data = self.key_file.read_bytes()
            if len(data) not in (16, 24, 32):
                raise ValueError("Clave invalida")
            return data
        self.key_file.parent.mkdir(parents=True, exist_ok=True)
        key = get_random_bytes(32)
        self.key_file.write_bytes(key)
        try:
            os.chmod(self.key_file, 0o600)
        except OSError:
            pass
        return key

    def encrypt(self, data: str | bytes) -> bytes:
        raw = data.encode("utf-8") if isinstance(data, str) else data
        cipher = AES.new(self.key, AES.MODE_GCM)
        ciphertext, tag = cipher.encrypt_and_digest(raw)
        packed = cipher.nonce + tag + ciphertext
        return base64.b64encode(packed)

    def decrypt(self, encrypted_data: str | bytes) -> bytes:
        blob = encrypted_data.encode("utf-8") if isinstance(encrypted_data, str) else encrypted_data
        data = base64.b64decode(blob)
        nonce = data[:16]
        tag = data[16:32]
        ciphertext = data[32:]
        cipher = AES.new(self.key, AES.MODE_GCM, nonce=nonce)
        return cipher.decrypt_and_verify(ciphertext, tag)

    def key_fingerprint(self) -> str:
        return hashlib.sha256(self.key).hexdigest()[:16]
