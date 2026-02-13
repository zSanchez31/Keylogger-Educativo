#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
import time

from config import settings
from src.keylogger import LinuxKeylogger, MacOSKeylogger, WindowsKeylogger
from src.utils import get_hardware_id, get_health_report, get_system_info


def build_keylogger():
    hardware_id = get_hardware_id()
    if settings.IS_WINDOWS:
        return WindowsKeylogger(log_file=settings.LOG_FILE, hardware_id=hardware_id)
    if settings.IS_LINUX:
        return LinuxKeylogger(log_file=settings.LOG_FILE, hardware_id=hardware_id)
    if settings.IS_MACOS:
        return MacOSKeylogger(log_file=settings.LOG_FILE, hardware_id=hardware_id)
    raise OSError(f"Sistema no soportado: {settings.SYSTEM}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Registro educativo seguro de entradas de texto")
    parser.add_argument("--once", type=str, default=None, help="Guarda una sola entrada y termina")
    parser.add_argument("--info", action="store_true", help="Muestra informacion del sistema")
    parser.add_argument("--stats", action="store_true", help="Muestra estado del almacenamiento")
    parser.add_argument(
        "--read",
        action="store_true",
        help="Muestra entradas descifradas",
    )
    parser.add_argument(
        "--read-all",
        action="store_true",
        help="Lee entradas del log actual y de logs rotados",
    )
    parser.add_argument(
        "--tail",
        action="store_true",
        help="Muestra entradas nuevas en tiempo real (Ctrl+C para salir)",
    )
    parser.add_argument(
        "--tail-from-start",
        action="store_true",
        help="En --tail, empieza desde el inicio del archivo",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=settings.DEFAULT_READ_LIMIT,
        help="Limite de filas para lectura o exportacion",
    )
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="Filtra por coincidencia en message",
    )
    parser.add_argument(
        "--since",
        type=str,
        default=None,
        help="Filtra desde timestamp ISO8601 (inclusive)",
    )
    parser.add_argument(
        "--until",
        type=str,
        default=None,
        help="Filtra hasta timestamp ISO8601 (inclusive)",
    )
    parser.add_argument(
        "--redact-hardware",
        action="store_true",
        help="Oculta hardware_id en la salida",
    )
    parser.add_argument(
        "--export-json",
        dest="export_json",
        type=str,
        default=None,
        help="Exporta entradas descifradas a JSON",
    )
    parser.add_argument(
        "--export-csv",
        dest="export_csv",
        type=str,
        default=None,
        help="Exporta entradas descifradas a CSV",
    )
    parser.add_argument(
        "--rotate",
        action="store_true",
        help="Fuerza rotacion del log actual",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Elimina logs rotados vencidos segun configuracion",
    )
    parser.add_argument(
        "--list-logs",
        action="store_true",
        help="Lista el log actual y los logs rotados",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Audita logs y cuenta lineas validas/invalidas",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Vacia el log actual (requiere --yes)",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Confirma acciones destructivas",
    )
    parser.add_argument(
        "--doctor",
        action="store_true",
        help="Ejecuta diagnostico de entorno y rutas",
    )
    parser.add_argument(
        "--key-info",
        action="store_true",
        help="Muestra metadatos de clave sin exponer su contenido",
    )
    parser.add_argument(
        "--import-json",
        dest="import_json",
        type=str,
        default=None,
        help="Importa entradas desde JSON",
    )
    parser.add_argument(
        "--import-csv",
        dest="import_csv",
        type=str,
        default=None,
        help="Importa entradas desde CSV",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Muestra version de la aplicacion",
    )
    return parser.parse_args()


def parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def apply_filters(
    rows: list[dict[str, str]],
    query: str | None,
    since: str | None,
    until: str | None,
    redact_hardware: bool,
) -> list[dict[str, str]]:
    if query:
        q = query.lower()
        rows = [r for r in rows if q in str(r.get("message", "")).lower()]
    if since:
        since_dt = parse_iso(since)
        rows = [r for r in rows if r.get("timestamp") and parse_iso(r["timestamp"]) >= since_dt]
    if until:
        until_dt = parse_iso(until)
        rows = [r for r in rows if r.get("timestamp") and parse_iso(r["timestamp"]) <= until_dt]
    if redact_hardware:
        for r in rows:
            if "hardware_id" in r:
                r["hardware_id"] = "REDACTED"
    return rows


def main() -> int:
    args = parse_args()
    if args.limit < 0:
        print("El valor de --limit debe ser mayor o igual a 0")
        return 2
    if args.limit > settings.MAX_EXPORT_ROWS:
        print(f"El valor de --limit no puede exceder {settings.MAX_EXPORT_ROWS}")
        return 2
    primary_actions = [
        bool(args.info),
        bool(args.stats),
        bool(args.doctor),
        bool(args.key_info),
        bool(args.list_logs),
        bool(args.read),
        bool(args.tail),
        bool(args.export_json),
        bool(args.export_csv),
        bool(args.import_json),
        bool(args.import_csv),
        bool(args.rotate),
        bool(args.cleanup),
        bool(args.verify),
        bool(args.clear),
        args.once is not None,
        bool(args.version),
    ]
    if sum(primary_actions) > 1:
        print("Usa solo una accion por ejecucion para evitar resultados ambiguos")
        return 2

    keylogger = build_keylogger()

    if args.version:
        print(f"{settings.APP_NAME} {settings.APP_VERSION}")
        return 0

    if args.info:
        print(json.dumps(get_system_info(), ensure_ascii=False, indent=2))
        return 0

    if args.stats:
        print(json.dumps(keylogger.stats(), ensure_ascii=False, indent=2))
        return 0

    if args.doctor:
        report = get_health_report(
            log_dir=str(settings.LOG_DIR),
            log_file=str(settings.LOG_FILE),
            key_file=str(settings.KEY_FILE),
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    if args.key_info:
        payload = {
            "key_file": str(settings.KEY_FILE),
            "fingerprint": keylogger.key_fingerprint(),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if args.list_logs:
        print(json.dumps(keylogger.list_logs(), ensure_ascii=False, indent=2))
        return 0

    if args.verify:
        print(json.dumps(keylogger.verify(), ensure_ascii=False, indent=2))
        return 0

    if args.clear:
        if not args.yes:
            print("Para vaciar el log actual, usa --clear --yes")
            return 2
        keylogger.clear()
        print("Log actual vaciado")
        return 0

    if args.rotate:
        keylogger.rotate()
        print("Rotacion completada")
        return 0

    if args.cleanup:
        removed = keylogger.cleanup()
        print(f"Logs antiguos eliminados: {removed}")
        return 0

    if args.read:
        try:
            rows = keylogger.read_entries_all() if args.read_all else keylogger.read_entries()
            rows = apply_filters(rows, args.query, args.since, args.until, args.redact_hardware)
        except ValueError:
            print("Formato invalido en --since/--until. Usa ISO8601, por ejemplo 2026-02-13T00:00:00+00:00")
            return 2
        if args.limit:
            rows = rows[-args.limit :]
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0

    if args.tail:
        path = settings.LOG_FILE
        try:
            with path.open("rb") as handle:
                if not args.tail_from_start:
                    handle.seek(0, 2)
                while True:
                    line = handle.readline()
                    if not line:
                        time.sleep(0.25)
                        continue
                    clean = line.strip()
                    if not clean:
                        continue
                    try:
                        decrypted = keylogger.encryptor.decrypt(clean).decode("utf-8", errors="replace")
                    except Exception:
                        continue
                    parts = decrypted.rstrip("\n").split("|", 3)
                    if len(parts) == 4:
                        row = {"timestamp": parts[0], "platform": parts[1], "hardware_id": parts[2], "message": parts[3]}
                    else:
                        row = {"timestamp": "", "platform": "", "hardware_id": "", "message": decrypted.rstrip("\n")}
                    rows = apply_filters([row], args.query, args.since, args.until, args.redact_hardware)
                    if rows:
                        print(json.dumps(rows[0], ensure_ascii=False))
        except KeyboardInterrupt:
            return 0

    if args.export_json:
        count = keylogger.export_json(args.export_json, limit=args.limit)
        print(f"Entradas exportadas a JSON: {count}")
        return 0

    if args.export_csv:
        count = keylogger.export_csv(args.export_csv, limit=args.limit)
        print(f"Entradas exportadas a CSV: {count}")
        return 0

    if args.import_json:
        result = keylogger.import_json(args.import_json, limit=args.limit)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.import_csv:
        result = keylogger.import_csv(args.import_csv, limit=args.limit)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.once is not None:
        keylogger.start()
        try:
            keylogger.record_input(args.once)
        finally:
            keylogger.stop()
        print("Entrada guardada")
        return 0

    print("Modo interactivo. Escribe 'salir' para terminar.")
    keylogger.run_interactive()
    print("Sesion finalizada")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
