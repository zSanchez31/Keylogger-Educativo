from __future__ import annotations

import unittest

from src.crypto.encryptor import Encryptor


class EncryptorTests(unittest.TestCase):
    def test_encrypt_decrypt_roundtrip(self) -> None:
        encryptor = Encryptor(key=b"0123456789ABCDEF0123456789ABCDEF")
        payload = "mensaje de prueba"
        encrypted = encryptor.encrypt(payload)
        decrypted = encryptor.decrypt(encrypted).decode("utf-8")
        self.assertEqual(payload, decrypted)

    def test_key_fingerprint_has_fixed_length(self) -> None:
        encryptor = Encryptor(key=b"0123456789ABCDEF0123456789ABCDEF")
        self.assertEqual(len(encryptor.key_fingerprint()), 16)


if __name__ == "__main__":
    unittest.main()
