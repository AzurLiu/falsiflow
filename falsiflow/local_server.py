"""Local browser server workflows for Falsiflow."""

from __future__ import annotations

import functools
import http.server
import json
from pathlib import Path
import threading
from typing import Protocol
import urllib.parse
import urllib.request

from .browser_demo import refresh_try_browser_assets
from .template_registry import read_json_object


class TryRunner(Protocol):
    def __call__(
        self,
        template: str,
        out_dir: Path,
        template_roots: list[Path] | None = None,
        force: bool = False,
        include_env: bool = True,
    ) -> dict[str, object]: ...


class TemplateRecordsProvider(Protocol):
    def __call__(self, extra_roots: list[Path] | None = None, include_env: bool = True) -> list[dict[str, str]]: ...


class WorkbenchChecker(Protocol):
    def __call__(self, out_dir: Path, payload: dict[str, object]) -> dict[str, object]: ...


class FalsiflowHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def falsiflow_out_dir(self) -> Path:
        return Path(str(getattr(self.server, "falsiflow_out_dir", ".")))

    def template_records_provider(self) -> TemplateRecordsProvider:
        provider = getattr(self.server, "falsiflow_template_records", None)
        if not callable(provider):
            raise SystemExit("Local server template provider is not configured.")
        return provider

    def workbench_checker(self) -> WorkbenchChecker:
        checker = getattr(self.server, "falsiflow_workbench_check", None)
        if not callable(checker):
            raise SystemExit("Local server workbench checker is not configured.")
        return checker

    def send_json(self, payload: dict[str, object], status: int = 200) -> None:
        data = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def read_json_payload(self) -> dict[str, object]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length > 20_000_000:
            raise SystemExit("Workbench upload is too large for the local API limit.")
        raw = self.rfile.read(length)
        loaded = json.loads(raw.decode("utf-8"))
        if not isinstance(loaded, dict):
            raise SystemExit("Workbench payload must be a JSON object.")
        return loaded

    def do_GET(self) -> None:
        request_path = urllib.parse.urlparse(self.path).path
        if request_path == "/api/templates":
            try:
                templates = self.template_records_provider()(include_env=False)
                self.send_json({"status": "templates_ready", "templates": templates})
            except SystemExit as exc:
                self.send_json({"status": "templates_blocked", "message": str(exc)}, status=500)
            return
        if request_path == "/api/workbench/state":
            summary_path = self.falsiflow_out_dir() / "workbench_summary.json"
            if summary_path.exists():
                self.send_json(read_json_object(summary_path, "workbench summary"))
            else:
                self.send_json({"status": "workbench_not_run", "links": {}})
            return
        return super().do_GET()

    def do_POST(self) -> None:
        request_path = urllib.parse.urlparse(self.path).path
        if request_path != "/api/workbench/check":
            self.send_json({"status": "not_found", "message": "Unknown local API endpoint."}, status=404)
            return
        try:
            summary = self.workbench_checker()(self.falsiflow_out_dir(), self.read_json_payload())
            self.send_json(summary)
        except SystemExit as exc:
            self.send_json({"status": "workbench_blocked", "message": str(exc), "failure_count": 1, "failures": [{"stage": "workbench", "id": "request_failed", "message": str(exc)}]}, status=400)
        except Exception as exc:  # pragma: no cover - defensive HTTP boundary.
            self.send_json({"status": "workbench_blocked", "message": str(exc), "failure_count": 1, "failures": [{"stage": "workbench", "id": "unexpected_error", "message": str(exc)}]}, status=500)

    def log_message(self, format: str, *args: object) -> None:
        return


def ensure_try_output(
    template: str,
    out_dir: Path,
    template_roots: list[Path] | None,
    force: bool,
    include_env: bool = True,
    *,
    try_runner: TryRunner,
) -> dict[str, object]:
    launchpad = out_dir / "index.html"
    try_report = out_dir / "try_report.html"
    try_summary_path = out_dir / "try_summary.json"
    if force or not try_report.exists():
        if out_dir.exists() and any(out_dir.iterdir()) and not force:
            raise SystemExit(f"Refusing to replace non-empty serve output directory without --force: {out_dir}")
        return try_runner(template, out_dir, template_roots=template_roots, force=force, include_env=include_env)
    if try_summary_path.exists():
        try:
            summary = read_json_object(try_summary_path, "try summary")
            if isinstance(summary, dict):
                return refresh_try_browser_assets(out_dir, summary)
        except SystemExit:
            pass
    summary = {
        "status": "try_ready",
        "template": template,
        "out_dir": str(out_dir),
        "outputs": {
            "try_summary": str(try_summary_path),
            "launchpad": str(launchpad),
            "try_report": str(try_report),
            "wizard": str(out_dir / "falsiflow_wizard.html"),
        },
    }
    return refresh_try_browser_assets(out_dir, summary)


def local_url(host: str, port: int, path: str) -> str:
    display_host = "127.0.0.1" if host in {"", "0.0.0.0", "::"} else host
    quoted_path = urllib.parse.quote(path.lstrip("/"), safe="/#?=&%:;,+")
    return f"http://{display_host}:{port}/{quoted_path}"


def serve_summary(
    out_dir: Path,
    try_summary: dict[str, object],
    host: str,
    port: int,
    check_status: str = "not_run",
    status_code: int = 0,
    entry_command: str = "serve",
) -> dict[str, object]:
    outputs = try_summary.get("outputs", {}) if isinstance(try_summary.get("outputs"), dict) else {}
    url = local_url(host, port, "index.html")
    reopen_command = f"falsiflow start --out-dir {out_dir}" if entry_command == "start" else f"falsiflow try --out-dir {out_dir} --force --open"
    summary: dict[str, object] = {
        "status": "serve_ready" if check_status != "http_blocked" else "serve_blocked",
        "entry_command": entry_command,
        "url": url,
        "launchpad_url": url,
        "workbench_url": local_url(host, port, "workbench.html"),
        "try_report_url": local_url(host, port, "try_report.html"),
        "wizard_url": local_url(host, port, "falsiflow_wizard.html"),
        "host": host,
        "port": port,
        "out_dir": str(out_dir),
        "try_status": str(try_summary.get("status", "")),
        "launchpad": str(outputs.get("launchpad", out_dir / "index.html")),
        "workbench": str(outputs.get("workbench", out_dir / "workbench.html")),
        "try_report": str(outputs.get("try_report", out_dir / "try_report.html")),
        "wizard": str(outputs.get("wizard", out_dir / "falsiflow_wizard.html")),
        "dashboard": str(outputs.get("dashboard", "")),
        "check_status": check_status,
        "status_code": status_code,
        "next_commands": [
            f"open {url}",
            reopen_command,
            f"open {local_url(host, port, 'workbench.html')}",
            f"falsiflow wizard --out {out_dir / 'falsiflow_wizard.html'} --open",
        ],
    }
    (out_dir / "serve_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary


def make_httpd(
    out_dir: Path,
    host: str,
    port: int,
    *,
    template_records_provider: TemplateRecordsProvider,
    workbench_checker: WorkbenchChecker,
) -> http.server.ThreadingHTTPServer:
    handler = functools.partial(FalsiflowHTTPRequestHandler, directory=str(out_dir.resolve()))
    httpd = http.server.ThreadingHTTPServer((host, port), handler)
    httpd.falsiflow_out_dir = out_dir
    httpd.falsiflow_template_records = template_records_provider
    httpd.falsiflow_workbench_check = workbench_checker
    return httpd


def check_launchpad_http(httpd: http.server.ThreadingHTTPServer, url: str) -> tuple[str, int]:
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    status_code = 0
    check_status = "http_blocked"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            status_code = int(getattr(response, "status", 0) or response.getcode())
            body = response.read(4096).decode("utf-8", errors="replace")
        check_status = "http_ready" if status_code == 200 and "Falsiflow Launchpad" in body else "http_blocked"
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)
    return check_status, status_code


def onboard_summary(out_dir: Path, start_summary: dict[str, object]) -> dict[str, object]:
    return {
        "status": "onboard_ready" if start_summary.get("status") == "serve_ready" else "onboard_blocked",
        "out_dir": str(out_dir),
        "start_status": str(start_summary.get("status", "")),
        "launchpad_url": str(start_summary.get("launchpad_url", start_summary.get("url", ""))),
        "try_report_url": str(start_summary.get("try_report_url", "")),
        "wizard_url": str(start_summary.get("wizard_url", "")),
        "local_only": True,
        "steps": [
            {
                "step": 1,
                "title": "Open the local app",
                "action": str(start_summary.get("url", "")),
            },
            {
                "step": 2,
                "title": "Review the example decision",
                "action": "Open report from the launchpad.",
            },
            {
                "step": 3,
                "title": "Create your own evidence checklist",
                "action": "Open wizard and choose a plain-language preset.",
            },
            {
                "step": 4,
                "title": "Bring real evidence",
                "action": "Fill the downloaded evidence CSV and keep source files beside it.",
            },
        ],
        "next_commands": [
            f"falsiflow start --out-dir {out_dir}",
            f"falsiflow wizard --out {out_dir / 'falsiflow_wizard.html'} --open",
            f"falsiflow doctor --project-dir {out_dir / 'project'} --strict",
        ],
        "start_summary": start_summary,
    }
