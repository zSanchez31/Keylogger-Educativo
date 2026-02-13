from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from config import settings
from ..crypto.encryptor import Encryptor
from ..storage.file_handler import FileHandler
from ..utils.system_check import get_hardware_id


class BaseKeylogger:
    def __init__(self, log_file: Path | str | None = None, hardware_id: str | None = None) -> None:
        self.log_file = Path(log_file) if log_file else settings.LOG_FILE
        self.encryptor = Encryptor(key_file=settings.KEY_FILE)
        self.file_handler = FileHandler(
            log_file=self.log_file,
            encryptor=self.encryptor,
            max_size=settings.MAX_LOG_SIZE,
            rotation=settings.LOG_ROTATION,
            cleanup_days=settings.CLEANUP_DAYS,
        )
        self.expected_hardware_id = hardware_id
        self.running = False

    def verify_hardware(self) -> bool:
        if not self.expected_hardware_id:
            return True
        return get_hardware_id() == self.expected_hardware_id

    def format_entry(self, message: str) -> str:
        stamp = datetime.now(timezone.utc).isoformat()
        system_name = settings.SYSTEM
        hw = get_hardware_id()
        clean = message.replace("\r", " ").replace("\n", " ").strip()
        return f"{stamp}|{system_name}|{hw}|{clean}"

    def record_input(self, message: str) -> bool:
        if not self.running:
            return False
        if not message or not message.strip():
            return False
        entry = self.format_entry(message)
        self.file_handler.append(entry + "\n")
        return True

    def start(self) -> None:
        if not self.verify_hardware():
            raise PermissionError("Hardware no autorizado")
        self.file_handler.initialize()
        self.running = True

    def stop(self) -> None:
        self.running = False

    def run_interactive(self) -> None:
        self.start()
        try:
            while self.running:
                line = input("texto> ")
                if line.strip().lower() in {"exit", "quit", "salir"}:
                    break
                self.record_input(line)
        finally:
            self.stop()

    def stats(self) -> dict:
        return self.file_handler.get_stats()

    def read_entries(self) -> list[dict[str, str]]:
        return self.file_handler.read_parsed()

    def read_entries_all(self) -> list[dict[str, str]]:
        return self.file_handler.read_parsed_all(include_current=True)

    def list_logs(self) -> list[str]:
        return [str(p) for p in self.file_handler.list_log_files(include_current=True)]

    def verify(self) -> dict:
        self.file_handler.initialize()
        return self.file_handler.verify_files(include_current=True)

    def clear(self) -> None:
        self.file_handler.clear_current_log()

    def export_json(self, output_path: Path | str, limit: int | None = None) -> int:
        return self.file_handler.export_json(output_path=output_path, limit=limit)

    def export_csv(self, output_path: Path | str, limit: int | None = None) -> int:
        return self.file_handler.export_csv(output_path=output_path, limit=limit)

    def rotate(self) -> None:
        self.file_handler.initialize()
        self.file_handler.rotate()

    def cleanup(self) -> int:
        self.file_handler.initialize()
        return self.file_handler.cleanup_old_logs()

    def import_json(self, input_path: Path | str, limit: int | None = None) -> dict[str, int]:
        self.file_handler.initialize()
        return self.file_handler.import_json(input_path=input_path, limit=limit)

    def import_csv(self, input_path: Path | str, limit: int | None = None) -> dict[str, int]:
        self.file_handler.initialize()
        return self.file_handler.import_csv(input_path=input_path, limit=limit)

    def key_fingerprint(self) -> str:
        return self.encryptor.key_fingerprint()
