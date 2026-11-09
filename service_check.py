"""Учебная CLI-утилита: проверка HTTP и TCP без внешних библиотек."""
import argparse
import json
import socket
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import urlopen


def check_http(url, expected=200, timeout=3.0):
    """Возвращает словарь с результатом HTTP-проверки."""
    parsed = urlsplit(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("Нужен полный URL http:// или https://")
    start = time.monotonic()
    try:
        with urlopen(url, timeout=timeout) as response:
            status = response.status
        error = None
    except HTTPError as exc:
        status, error = exc.code, None
        exc.close()  # HTTPError holds a response stream that must be closed.
    except (URLError, OSError, ValueError) as exc:
        status, error = None, str(exc)

    return {
        "check": "http",
        "target": parsed.hostname,  # не сохраняем токены из URL и query
        "ok": status == expected and error is None,
        "status": status,
        "expected": expected,
        "elapsed_ms": round((time.monotonic() - start) * 1000, 1),
        "error": error,
    }


def check_tcp(host, port, timeout=3.0):
    """Пробуем открыть TCP-соединение."""
    start = time.monotonic()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            error = None
    except OSError as exc:
        error = str(exc)
    return {
        "check": "tcp",
        "target": f"{host}:{port}",
        "ok": error is None,
        "elapsed_ms": round((time.monotonic() - start) * 1000, 1),
        "error": error,
    }


def main():
    parser = argparse.ArgumentParser(description="Проверка доступности сервиса")
    parser.add_argument("--json", action="store_true", help="Вывести JSON")
    parser.add_argument("--log", type=Path, help="Дополнительно сохранить JSONL")
    commands = parser.add_subparsers(dest="mode", required=True)

    http = commands.add_parser("http", help="Проверка HTTP")
    http.add_argument("url")
    http.add_argument("--expected", type=int, default=200)
    http.add_argument("--timeout", type=float, default=3.0)

    tcp = commands.add_parser("tcp", help="Проверка порта")
    tcp.add_argument("host")
    tcp.add_argument("port", type=int)
    tcp.add_argument("--timeout", type=float, default=3.0)

    args = parser.parse_args()
    if not 0 < args.timeout <= 60:
        parser.error("--timeout должен быть от 0 до 60 секунд")
    if args.mode == "http":
        if not 100 <= args.expected <= 599:
            parser.error("--expected должен быть HTTP-кодом 100–599")
        try:
            result = check_http(args.url, args.expected, args.timeout)
        except ValueError as exc:
            parser.error(str(exc))
    else:
        if not 1 <= args.port <= 65535:
            parser.error("Порт должен быть в диапазоне 1–65535")
        result = check_tcp(args.host, args.port, args.timeout)

    result["checked_at"] = datetime.now(timezone.utc).isoformat()
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        state = "OK" if result["ok"] else "FAIL"
        print(f"{state}: {result['check']} {result['target']} | "
              f"{result['elapsed_ms']} ms | {result['error'] or result.get('status', 'connected')}")
    if args.log:
        with args.log.open("a", encoding="utf-8") as file:
            file.write(json.dumps(result, ensure_ascii=False) + "\n")
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
