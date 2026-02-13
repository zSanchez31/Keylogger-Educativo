#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import importlib
import platform

DIRECTORIES = [
    Path("logs"),
    Path("config"),
    Path("src"),
    Path("src/keylogger"),
    Path("src/crypto"),
    Path("src/storage"),
    Path("src/utils"),
]

INIT_FILES = [
    Path("config/__init__.py"),
    Path("src/__init__.py"),
    Path("src/keylogger/__init__.py"),
    Path("src/crypto/__init__.py"),
    Path("src/storage/__init__.py"),
    Path("src/utils/__init__.py"),
]

REQUIRED_MODULES = ["Crypto.Cipher"]


def ensure_structure() -> None:
    for directory in DIRECTORIES:
        directory.mkdir(parents=True, exist_ok=True)
    for init_file in INIT_FILES:
        init_file.parent.mkdir(parents=True, exist_ok=True)
        init_file.touch(exist_ok=True)


def check_dependencies() -> tuple[bool, list[str]]:
    missing: list[str] = []
    for module in REQUIRED_MODULES:
        try:
            importlib.import_module(module)
        except Exception:
            missing.append(module)
    return len(missing) == 0, missing


def main() -> int:
    ensure_structure()
    ok, missing = check_dependencies()
    print(f"Sistema detectado: {platform.system()}")
    print(f"Directorio base: {Path.cwd()}")
    if ok:
        print("Dependencias principales correctas")
        return 0
    print("Faltan dependencias:")
    for module in missing:
        print(f"- {module}")
    print("Instala requirements.txt antes de ejecutar main.py")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
