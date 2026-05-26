#!/usr/bin/env python3
"""Minimal client for NVIDIA NIM ALCHEMI Batched Molecular Dynamics."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_BASE_URL = "http://localhost:8000"


def _read_dotenv(path: Path) -> None:
    """Load simple KEY=VALUE lines without overriding existing environment."""
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _env_api_key() -> str | None:
    for name in ("ALCHEMI_BMD_API_KEY", "NVIDIA_API_KEY", "NGC_API_KEY"):
        value = os.getenv(name)
        if value:
            return value
    return None


def _json_dumps(data: Any) -> bytes:
    return json.dumps(data, ensure_ascii=True, separators=(",", ":")).encode("utf-8")


class AlchemiBMDClient:
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self.base_url = (base_url or os.getenv("ALCHEMI_BMD_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.api_key = api_key if api_key is not None else _env_api_key()
        self.timeout = float(timeout or os.getenv("ALCHEMI_BMD_TIMEOUT") or 120)

    def request(self, method: str, path: str, body: Any | None = None) -> Any:
        url = urllib.parse.urljoin(f"{self.base_url}/", path.lstrip("/"))
        data = _json_dumps(body) if body is not None else None
        headers = {"Accept": "application/json"}

        if body is not None:
            headers["Content-Type"] = "application/json"
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        request = urllib.request.Request(url=url, data=data, headers=headers, method=method.upper())

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = response.read()
                if not payload:
                    return None
                content_type = response.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    return json.loads(payload.decode("utf-8"))
                return payload.decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            body_text = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code} from {url}: {body_text}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Could not reach {url}: {exc.reason}") from exc

    def live(self) -> Any:
        return self.request("GET", "/v1/health/live")

    def ready(self) -> Any:
        return self.request("GET", "/v1/health/ready")

    def status(self) -> Any:
        return self.request("GET", "/v1/status")

    def infer(self, payload: dict[str, Any]) -> Any:
        return self.request("POST", "/v1/infer", payload)


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _print_json(value: Any) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=True, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Call NVIDIA NIM ALCHEMI BMD endpoints.")
    parser.add_argument("--base-url", default=None, help="NIM base URL. Defaults to ALCHEMI_BMD_BASE_URL or localhost.")
    parser.add_argument("--timeout", type=float, default=None, help="Request timeout in seconds.")

    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("health", help="Call live and ready health endpoints.")
    subparsers.add_parser("status", help="Call /v1/status.")

    infer_parser = subparsers.add_parser("infer", help="Call /v1/infer with a JSON payload.")
    infer_parser.add_argument("--payload", type=Path, required=True, help="Path to request JSON.")
    infer_parser.add_argument("--out", type=Path, default=None, help="Optional output JSON path.")
    infer_parser.add_argument("--dry-run", action="store_true", help="Print request metadata without sending it.")

    return parser


def main(argv: list[str] | None = None) -> int:
    _read_dotenv(Path(".env"))
    args = build_parser().parse_args(argv)
    client = AlchemiBMDClient(base_url=args.base_url, timeout=args.timeout)

    try:
        if args.command == "health":
            _print_json({"live": client.live(), "ready": client.ready()})
            return 0

        if args.command == "status":
            _print_json(client.status())
            return 0

        if args.command == "infer":
            payload = _load_json(args.payload)
            if args.dry_run:
                _print_json(
                    {
                        "base_url": client.base_url,
                        "endpoint": "/v1/infer",
                        "auth_enabled": bool(client.api_key),
                        "payload_path": str(args.payload),
                        "payload_keys": sorted(payload.keys()),
                    }
                )
                return 0

            response = client.infer(payload)
            if args.out:
                args.out.parent.mkdir(parents=True, exist_ok=True)
                args.out.write_text(json.dumps(response, indent=2, ensure_ascii=True), encoding="utf-8")
                print(f"Wrote {args.out}")
            else:
                _print_json(response)
            return 0

        raise AssertionError(f"Unhandled command: {args.command}")
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
