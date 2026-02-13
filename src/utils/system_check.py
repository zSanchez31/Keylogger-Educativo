from __future__ import annotations

import getpass
import hashlib
import os
import platform
import socket
import subprocess
from typing import Any


def get_system_info() -> dict[str, Any]:
    return {
        "system": platform.system().lower(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "hostname": socket.gethostname(),
        "python_version": platform.python_version(),
    }


def get_hardware_id() -> str:
    system = platform.system().lower()
    value = _read_platform_identifier(system)
    if value:
        return value
    seed = "|".join(
        [
            socket.gethostname(),
            platform.machine(),
            platform.processor(),
            getpass.getuser(),
        ]
    )
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:32]


def get_health_report(log_dir: str, log_file: str, key_file: str) -> dict[str, Any]:
    report: dict[str, Any] = {
        "system": get_system_info(),
        "paths": {},
    }
    report["paths"]["log_dir"] = _path_state(log_dir, is_dir=True)
    report["paths"]["log_file"] = _path_state(log_file, is_dir=False)
    report["paths"]["key_file"] = _path_state(key_file, is_dir=False)
    checks = {
        "log_dir_writable": report["paths"]["log_dir"]["writable"],
        "log_file_parent_writable": report["paths"]["log_file"]["parent_writable"],
        "key_file_parent_writable": report["paths"]["key_file"]["parent_writable"],
    }
    report["checks"] = checks
    report["ok"] = all(bool(value) for value in checks.values())
    return report


def _read_platform_identifier(system: str) -> str | None:
    try:
        if system == "linux":
            for candidate in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
                if os.path.exists(candidate):
                    data = PathReader.read_text(candidate)
                    if data:
                        return data
        if system == "darwin":
            cmd = ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"]
            result = subprocess.run(cmd, check=False, capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if "IOPlatformUUID" in line:
                    parts = line.split('"')
                    if len(parts) >= 4:
                        return parts[3]
        if system == "windows":
            cmd = ["wmic", "csproduct", "get", "uuid"]
            result = subprocess.run(cmd, check=False, capture_output=True, text=True)
            lines = [l.strip() for l in result.stdout.splitlines() if l.strip() and "UUID" not in l]
            if lines:
                return lines[0]
    except Exception:
        return None
    return None


class PathReader:
    @staticmethod
    def read_text(path: str) -> str | None:
        try:
            with open(path, "r", encoding="utf-8") as handle:
                return handle.read().strip()
        except OSError:
            return None


def _path_state(path: str, is_dir: bool) -> dict[str, Any]:
    target = os.path.abspath(path)
    exists = os.path.exists(target)
    parent = target if is_dir else os.path.dirname(target)
    if not parent:
        parent = "."
    return {
        "path": target,
        "exists": exists,
        "is_dir": os.path.isdir(target) if exists else False,
        "is_file": os.path.isfile(target) if exists else False,
        "readable": os.access(target, os.R_OK) if exists else False,
        "writable": os.access(target, os.W_OK) if exists else False,
        "parent_writable": os.access(parent, os.W_OK),
    }
