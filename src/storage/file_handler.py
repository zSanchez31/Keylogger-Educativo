from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


class FileHandler:
    def __init__(self, log_file: Path | str, encryptor, max_size: int, rotation: bool, cleanup_days: int) -> None:
        self.log_file = Path(log_file)
        self.encryptor = encryptor
        self.max_size = max_size
        self.rotation = rotation
        self.cleanup_days = cleanup_days

    def initialize(self) -> None:
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.log_file.exists():
            self.log_file.touch()

    def append(self, data: str) -> None:
        encrypted = self.encryptor.encrypt(data)
        with self.log_file.open("ab") as handle:
            handle.write(encrypted + b"\n")
        if self.rotation and self.log_file.stat().st_size > self.max_size:
            self.rotate()

    def append_structured(self, item: dict[str, str]) -> bool:
        normalized = self._normalize_item(item)
        if not normalized:
            return False
        line = (
            f"{normalized['timestamp']}|{normalized['platform']}|"
            f"{normalized['hardware_id']}|{normalized['message']}\n"
        )
        self.append(line)
        return True

    def rotate(self) -> None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        rotated = self.log_file.parent / f"keystrokes_{stamp}.enc"
        self.log_file.rename(rotated)
        self.log_file.touch()
        self.cleanup_old_logs()

    def cleanup_old_logs(self) -> int:
        cutoff = datetime.now() - timedelta(days=self.cleanup_days)
        removed = 0
        for path in self.log_file.parent.glob("keystrokes_*.enc"):
            modified = datetime.fromtimestamp(path.stat().st_mtime)
            if modified < cutoff:
                path.unlink(missing_ok=True)
                removed += 1
        return removed

    def read_all(self) -> list[str]:
        return self._read_all_from_file(self.log_file)

    def _read_all_from_file(self, path: Path) -> list[str]:
        if not path.exists():
            return []
        rows: list[str] = []
        with path.open("rb") as handle:
            for line in handle:
                clean = line.strip()
                if not clean:
                    continue
                decrypted = self._decrypt_line(clean)
                if decrypted is None:
                    continue
                rows.append(decrypted)
        return rows

    def _decrypt_line(self, encrypted_line: bytes) -> str | None:
        try:
            return self.encryptor.decrypt(encrypted_line).decode("utf-8", errors="replace")
        except Exception:
            return None

    def read_parsed(self) -> list[dict[str, str]]:
        return self._read_parsed_from_lines(self.read_all())

    def read_parsed_from_file(self, path: Path | str) -> list[dict[str, str]]:
        return self._read_parsed_from_lines(self._read_all_from_file(Path(path)))

    def list_log_files(self, include_current: bool = True) -> list[Path]:
        files: list[Path] = []
        if include_current:
            files.append(self.log_file)
        files.extend(sorted(self.log_file.parent.glob("keystrokes_*.enc")))
        files = [p for p in files if p.exists()]
        files.sort(key=lambda p: p.stat().st_mtime)
        return files

    def read_parsed_all(self, include_current: bool = True) -> list[dict[str, str]]:
        items: list[dict[str, str]] = []
        for path in self.list_log_files(include_current=include_current):
            items.extend(self.read_parsed_from_file(path))
        return items

    def _read_parsed_from_lines(self, lines: list[str]) -> list[dict[str, str]]:
        parsed: list[dict[str, str]] = []
        for line in lines:
            payload = line.rstrip("\n")
            parts = payload.split("|", 3)
            if len(parts) != 4:
                parsed.append(
                    {
                        "timestamp": "",
                        "platform": "",
                        "hardware_id": "",
                        "message": payload,
                    }
                )
                continue
            parsed.append(
                {
                    "timestamp": parts[0],
                    "platform": parts[1],
                    "hardware_id": parts[2],
                    "message": parts[3],
                }
            )
        return parsed

    def verify_files(self, include_current: bool = True) -> dict[str, Any]:
        results: list[dict[str, Any]] = []
        total_valid = 0
        total_invalid = 0
        total_lines = 0
        for path in self.list_log_files(include_current=include_current):
            valid = 0
            invalid = 0
            lines = 0
            with path.open("rb") as handle:
                for raw in handle:
                    clean = raw.strip()
                    if not clean:
                        continue
                    lines += 1
                    if self._decrypt_line(clean) is None:
                        invalid += 1
                    else:
                        valid += 1
            total_valid += valid
            total_invalid += invalid
            total_lines += lines
            results.append(
                {
                    "path": str(path),
                    "lines": lines,
                    "valid": valid,
                    "invalid": invalid,
                }
            )
        return {
            "total": {
                "files": len(results),
                "lines": total_lines,
                "valid": total_valid,
                "invalid": total_invalid,
            },
            "files": results,
        }

    def clear_current_log(self) -> None:
        self.initialize()
        self.log_file.write_bytes(b"")

    def export_json(self, output_path: Path | str, limit: int | None = None) -> int:
        items = self.read_parsed()
        if limit is not None and limit >= 0:
            items = items[-limit:]
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
        return len(items)

    def export_csv(self, output_path: Path | str, limit: int | None = None) -> int:
        items = self.read_parsed()
        if limit is not None and limit >= 0:
            items = items[-limit:]
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle, fieldnames=["timestamp", "platform", "hardware_id", "message"]
            )
            writer.writeheader()
            writer.writerows(items)
        return len(items)

    def import_json(self, input_path: Path | str, limit: int | None = None) -> dict[str, int]:
        source = Path(input_path)
        if not source.exists():
            raise FileNotFoundError(str(source))
        data = json.loads(source.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("El JSON debe contener una lista de objetos")
        if limit is not None and limit >= 0:
            data = data[:limit]
        accepted = 0
        rejected = 0
        for item in data:
            if not isinstance(item, dict):
                rejected += 1
                continue
            if self.append_structured(item):
                accepted += 1
            else:
                rejected += 1
        return {"accepted": accepted, "rejected": rejected}

    def import_csv(self, input_path: Path | str, limit: int | None = None) -> dict[str, int]:
        source = Path(input_path)
        if not source.exists():
            raise FileNotFoundError(str(source))
        accepted = 0
        rejected = 0
        with source.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for index, row in enumerate(reader):
                if limit is not None and limit >= 0 and index >= limit:
                    break
                if self.append_structured(dict(row)):
                    accepted += 1
                else:
                    rejected += 1
        return {"accepted": accepted, "rejected": rejected}

    def _normalize_item(self, item: dict[str, str]) -> dict[str, str] | None:
        required = ("timestamp", "platform", "hardware_id", "message")
        if not all(key in item for key in required):
            return None
        timestamp = str(item["timestamp"]).strip()
        platform_name = str(item["platform"]).strip()
        hardware_id = str(item["hardware_id"]).strip()
        message = str(item["message"]).replace("\r", " ").replace("\n", " ").strip()
        if not timestamp or not platform_name or not hardware_id or not message:
            return None
        return {
            "timestamp": timestamp,
            "platform": platform_name,
            "hardware_id": hardware_id,
            "message": message,
        }

    def get_stats(self) -> dict:
        exists = self.log_file.exists()
        size = self.log_file.stat().st_size if exists else 0
        rotated = len(list(self.log_file.parent.glob("keystrokes_*.enc")))
        return {
            "exists": exists,
            "path": str(self.log_file),
            "size": size,
            "rotated_files": rotated,
        }
