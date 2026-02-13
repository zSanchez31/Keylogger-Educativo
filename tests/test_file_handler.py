from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.crypto.encryptor import Encryptor
from src.storage.file_handler import FileHandler


class FileHandlerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.log_file = self.base / "logs" / "keystrokes.enc"
        self.encryptor = Encryptor(key=b"0123456789ABCDEF0123456789ABCDEF")
        self.handler = FileHandler(
            log_file=self.log_file,
            encryptor=self.encryptor,
            max_size=10_000,
            rotation=True,
            cleanup_days=30,
        )
        self.handler.initialize()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_append_and_read_parsed(self) -> None:
        self.handler.append("2026-02-13T00:00:00+00:00|darwin|abc123|hola\n")
        rows = self.handler.read_parsed()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["message"], "hola")

    def test_list_log_files_includes_current(self) -> None:
        files = self.handler.list_log_files(include_current=True)
        self.assertTrue(any(Path(p) == self.log_file for p in files))

    def test_import_json(self) -> None:
        payload = [
            {
                "timestamp": "2026-02-13T00:00:00+00:00",
                "platform": "darwin",
                "hardware_id": "abc",
                "message": "uno",
            },
            {
                "timestamp": "",
                "platform": "darwin",
                "hardware_id": "abc",
                "message": "dos",
            },
        ]
        source = self.base / "in.json"
        source.write_text(json.dumps(payload), encoding="utf-8")
        result = self.handler.import_json(source)
        self.assertEqual(result["accepted"], 1)
        self.assertEqual(result["rejected"], 1)

    def test_verify_files_counts_lines(self) -> None:
        self.handler.append("2026-02-13T00:00:00+00:00|darwin|abc123|hola\n")
        report = self.handler.verify_files(include_current=True)
        self.assertGreaterEqual(report["total"]["lines"], 1)
        self.assertGreaterEqual(report["total"]["valid"], 1)

    def test_clear_current_log(self) -> None:
        self.handler.append("2026-02-13T00:00:00+00:00|darwin|abc123|hola\n")
        self.handler.clear_current_log()
        self.assertEqual(self.log_file.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
