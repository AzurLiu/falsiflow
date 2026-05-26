"""Template registry, source cache, and lock helpers."""

from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
import tempfile
import urllib.parse
import urllib.request

from .template_pack import (
    extract_template_pack_zip,
    is_sha256,
    markdown_cell,
    merge_template_pack_verification_issues,
    sha256_file,
    template_pack_failure_report,
    verification_issue,
    verify_template_pack,
)


def read_json_object(path: Path, label: str) -> dict[str, object]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"{label} does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{label} is not valid JSON: {path}: {exc}") from exc
    if not isinstance(loaded, dict):
        raise SystemExit(f"{label} must contain a JSON object: {path}")
    return loaded


def safe_template_identifier(identifier: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", identifier)) and identifier not in {".", ".."}


def template_source_url(base_url: str, zip_path: Path) -> str:
    normalized = base_url.strip()
    if not normalized:
        return ""
    if not normalized.endswith("/"):
        normalized += "/"
    return urllib.parse.urljoin(normalized, urllib.parse.quote(zip_path.name))


def template_registry_entry(zip_path: Path, source_url: str = "") -> dict[str, object]:
    zip_path = zip_path.expanduser().resolve()
    source_bytes = zip_path.stat().st_size if zip_path.exists() and zip_path.is_file() else 0
    source_sha256 = sha256_file(zip_path) if zip_path.exists() and zip_path.is_file() else ""
    with tempfile.TemporaryDirectory(prefix="falsiflow_template_registry_") as tmp:
        extract_root = Path(tmp) / "template_pack"
        pack_root, extraction_issues, member_count, extracted_file_count = extract_template_pack_zip(zip_path, extract_root)
        if pack_root is None:
            verification = template_pack_failure_report(zip_path, "zip", extraction_issues, zip_path)
            manifest: dict[str, object] = {}
            project: dict[str, object] = {}
        else:
            verification = verify_template_pack(pack_root, input_path=zip_path, input_format="zip")
            verification["zip_path"] = str(zip_path)
            verification["zip_member_count"] = member_count
            verification["zip_extracted_file_count"] = extracted_file_count
            verification = merge_template_pack_verification_issues(verification, extraction_issues)
            try:
                manifest = read_json_object(pack_root / "template_pack_manifest.json", "template pack manifest") if (pack_root / "template_pack_manifest.json").exists() else {}
            except SystemExit:
                manifest = {}
            try:
                project = read_json_object(pack_root / "template" / "project.json", "template project")
            except SystemExit:
                project = {}

    project_meta = project.get("project", {}) if isinstance(project.get("project"), dict) else {}
    template_id = str(manifest.get("template_id") or verification.get("template_id", ""))
    template_version = str(project_meta.get("version", ""))
    return {
        "status": "template_available" if verification.get("status") == "template_pack_verified" else "template_blocked",
        "template_id": template_id,
        "template_name": str(manifest.get("template_name", "")),
        "template_domain": str(manifest.get("template_domain", "")),
        "template_version": template_version,
        "template_project_id": str(project_meta.get("id", "")),
        "template_project_version": template_version,
        "source_type": "url" if source_url else "file",
        "source_url": source_url,
        "source_path": str(zip_path),
        "source_bytes": source_bytes,
        "source_sha256": source_sha256,
        "verification_status": str(verification.get("status", "")),
        "integrity_status": str(verification.get("integrity_status", "")),
        "template_pack_status": str(verification.get("template_pack_status", "")),
        "artifact_count": int(verification.get("artifact_count", 0) or 0),
        "zip_member_count": int(verification.get("zip_member_count", 0) or 0),
        "zip_extracted_file_count": int(verification.get("zip_extracted_file_count", 0) or 0),
        "issue_count": int(verification.get("issue_count", 0) or 0),
        "error_count": int(verification.get("error_count", 0) or 0),
        "warning_count": int(verification.get("warning_count", 0) or 0),
        "issues": list(verification.get("issues", [])),
    }


def render_template_registry_report(registry: dict[str, object]) -> str:
    lines = [
        "# Falsiflow Template Registry",
        "",
        f"- Status: `{registry.get('status', '')}`",
        f"- Templates: {registry.get('verified_template_count', 0)}/{registry.get('template_count', 0)}",
        f"- Duplicates: {registry.get('duplicate_template_count', 0)}",
        f"- Issues: {registry.get('issue_count', 0)}",
        "",
        "## Entries",
        "",
        "| Template | Status | Version | Source SHA-256 | Source |",
        "| --- | --- | --- | --- | --- |",
    ]
    for entry in registry.get("templates", []):
        if not isinstance(entry, dict):
            continue
        lines.append(
            "| "
            + " | ".join([
                markdown_cell(entry.get("template_id", "")),
                markdown_cell(entry.get("status", "")),
                markdown_cell(entry.get("template_version", entry.get("template_project_version", ""))),
                markdown_cell(entry.get("source_sha256", "")),
                markdown_cell(entry.get("source_url") or entry.get("source_path", "")),
            ])
            + " |"
        )
    issues = registry.get("issues", [])
    lines.extend(["", "## Issues", ""])
    if not issues:
        lines.append("No issues found.")
    else:
        lines.extend(["| Severity | Code | Path | Message |", "| --- | --- | --- | --- |"])
        for issue in issues:
            if not isinstance(issue, dict):
                continue
            lines.append(
                "| "
                + " | ".join([
                    markdown_cell(issue.get("severity", "")),
                    f"`{markdown_cell(issue.get('code', ''))}`",
                    markdown_cell(issue.get("path", "")),
                    markdown_cell(issue.get("message", "")),
                ])
                + " |"
            )
    return "\n".join(lines) + "\n"


def run_template_registry(
    pack_zips: list[Path],
    out: Path | None = None,
    report_out: Path | None = None,
    base_url: str = "",
) -> dict[str, object]:
    entries = [
        template_registry_entry(zip_path, source_url=template_source_url(base_url, zip_path) if base_url else "")
        for zip_path in pack_zips
    ]
    issues: list[dict[str, object]] = []
    seen: dict[tuple[str, str], int] = {}
    duplicate_template_count = 0
    for entry in entries:
        template_id = str(entry.get("template_id", ""))
        template_version = str(entry.get("template_version") or entry.get("template_project_version", ""))
        if not safe_template_identifier(template_id):
            issues.append(verification_issue("error", "unsafe_template_id", "Registry entry template_id is missing or unsafe.", str(entry.get("source_path", ""))))
        if template_id:
            key = (template_id, template_version)
            seen[key] = seen.get(key, 0) + 1
    for (template_id, template_version), count in sorted(seen.items()):
        if count > 1:
            duplicate_template_count += 1
            issues.append(verification_issue("error", "duplicate_template_version", "Registry contains duplicate template id/version entries.", f"{template_id}@{template_version}"))
    for entry in entries:
        if entry.get("status") != "template_available":
            issues.append(verification_issue("error", "template_pack_not_available", "Template pack is not verified and available.", str(entry.get("source_path", "")), "template_available", entry.get("status")))
        for issue in entry.get("issues", []):
            if isinstance(issue, dict) and issue.get("severity") == "error":
                issues.append(issue)

    error_count = sum(1 for issue in issues if issue.get("severity") == "error")
    registry = {
        "status": "template_registry_ready" if not error_count else "template_registry_blocked",
        "template_count": len(entries),
        "verified_template_count": sum(1 for entry in entries if entry.get("status") == "template_available"),
        "duplicate_template_count": duplicate_template_count,
        "issue_count": len(issues),
        "error_count": error_count,
        "warning_count": sum(1 for issue in issues if issue.get("severity") == "warning"),
        "templates": entries,
        "issues": issues,
    }
    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if report_out is not None:
        report_out.parent.mkdir(parents=True, exist_ok=True)
        report_out.write_text(render_template_registry_report(registry), encoding="utf-8")
    return registry


def safe_cache_segment(value: str, fallback: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._")
    return cleaned or fallback


def template_source_cache_path(cache_dir: Path, template_id: str, template_version: str, source_sha256: str) -> Path:
    template_part = safe_cache_segment(template_id, "template")
    version_part = safe_cache_segment(template_version, "unversioned")
    sha_part = source_sha256[:16] if is_sha256(source_sha256) else "unverified"
    return cache_dir / f"{template_part}-{version_part}-{sha_part}.zip"


def download_template_source(source_url: str, cache_dir: Path, template_id: str, template_version: str, expected_bytes: int, expected_sha256: str) -> Path:
    parsed = urllib.parse.urlparse(source_url)
    if parsed.scheme not in {"http", "https", "file"}:
        raise SystemExit(f"Unsupported template source URL scheme: {source_url}")
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached = template_source_cache_path(cache_dir, template_id, template_version, expected_sha256)
    if cached.exists() and cached.is_file():
        if cached.stat().st_size == expected_bytes and sha256_file(cached) == expected_sha256:
            return cached
        cached.unlink()
    tmp_path = cached.with_suffix(cached.suffix + ".tmp")
    if tmp_path.exists():
        tmp_path.unlink()
    try:
        with urllib.request.urlopen(source_url, timeout=30) as response, tmp_path.open("wb") as target:
            shutil.copyfileobj(response, target)
    except Exception as exc:  # pragma: no cover - defensive network/file URL boundary.
        if tmp_path.exists():
            tmp_path.unlink()
        raise SystemExit(f"Could not fetch template source URL `{source_url}`: {exc}") from exc
    actual_bytes = tmp_path.stat().st_size
    if actual_bytes != expected_bytes:
        tmp_path.unlink()
        raise SystemExit(f"Downloaded template source byte size mismatch: expected {expected_bytes}, got {actual_bytes}")
    actual_sha256 = sha256_file(tmp_path)
    if actual_sha256 != expected_sha256:
        tmp_path.unlink()
        raise SystemExit(f"Downloaded template source SHA-256 mismatch: expected {expected_sha256}, got {actual_sha256}")
    tmp_path.replace(cached)
    return cached


def run_template_lock(
    registry_path: Path,
    template_id: str,
    version: str = "",
    out: Path | None = None,
    cache_dir: Path | None = None,
) -> dict[str, object]:
    registry_path = registry_path.expanduser().resolve()
    registry = read_json_object(registry_path, "template registry")
    issues: list[dict[str, object]] = []
    if registry.get("status") != "template_registry_ready":
        issues.append(verification_issue("error", "registry_not_ready", "Template registry is not ready.", str(registry_path), "template_registry_ready", registry.get("status")))
    entries = [
        entry
        for entry in registry.get("templates", [])
        if isinstance(entry, dict)
        and entry.get("template_id") == template_id
        and (not version or str(entry.get("template_version") or entry.get("template_project_version", "")) == version)
    ]
    if not entries:
        issues.append(verification_issue("error", "template_not_found", "Template id/version was not found in the registry.", f"{template_id}@{version}" if version else template_id))
        entry: dict[str, object] = {}
    elif len(entries) > 1:
        issues.append(verification_issue("error", "ambiguous_template_version", "Template id appears more than once in the registry; pass --version.", template_id))
        entry = entries[0]
    else:
        entry = entries[0]
    if entry and entry.get("status") != "template_available":
        issues.append(verification_issue("error", "template_not_available", "Template registry entry is not available.", template_id, "template_available", entry.get("status")))

    template_version = str(entry.get("template_version") or entry.get("template_project_version", "")) if entry else version
    source_url = str(entry.get("source_url", "")) if entry else ""
    source_path = Path(str(entry.get("source_path", ""))).expanduser() if entry else Path()
    if source_path and not source_path.is_absolute():
        source_path = (registry_path.parent / source_path).resolve()
    source_bytes = int(entry.get("source_bytes", 0) or 0) if entry else 0
    source_sha256 = str(entry.get("source_sha256", "")) if entry else ""
    cached_source_path = ""
    if entry:
        if source_url:
            try:
                resolved_cache_dir = cache_dir or (registry_path.parent / ".falsiflow_template_cache")
                cached_source_path = str(download_template_source(source_url, resolved_cache_dir, template_id, template_version, source_bytes, source_sha256))
            except SystemExit as exc:
                issues.append(verification_issue("error", "source_url_fetch_failed", str(exc), source_url))
        elif not source_path.exists() or not source_path.is_file():
            issues.append(verification_issue("error", "source_missing", "Template pack source zip is missing.", str(source_path)))
        else:
            actual_bytes = source_path.stat().st_size
            if actual_bytes != source_bytes:
                issues.append(verification_issue("error", "source_bytes_mismatch", "Template pack source bytes do not match registry.", str(source_path), source_bytes, actual_bytes))
            actual_sha256 = sha256_file(source_path)
            if actual_sha256 != source_sha256:
                issues.append(verification_issue("error", "source_sha256_mismatch", "Template pack source SHA-256 does not match registry.", str(source_path), source_sha256, actual_sha256))

    error_count = sum(1 for issue in issues if issue.get("severity") == "error")
    lock = {
        "status": "template_locked" if not error_count else "template_lock_blocked",
        "template_id": template_id,
        "template_name": str(entry.get("template_name", "")) if entry else "",
        "template_domain": str(entry.get("template_domain", "")) if entry else "",
        "template_version": template_version,
        "template_project_version": str(entry.get("template_project_version", "")) if entry else "",
        "registry_path": str(registry_path),
        "registry_sha256": sha256_file(registry_path) if registry_path.exists() else "",
        "source_type": str(entry.get("source_type", "")) if entry else "",
        "source_url": source_url,
        "source_path": str(source_path) if entry else "",
        "cached_source_path": cached_source_path,
        "source_bytes": source_bytes,
        "source_sha256": source_sha256,
        "pack_verification_status": str(entry.get("verification_status", "")) if entry else "",
        "artifact_count": int(entry.get("artifact_count", 0) or 0) if entry else 0,
        "issue_count": len(issues),
        "error_count": error_count,
        "warning_count": sum(1 for issue in issues if issue.get("severity") == "warning"),
        "issues": issues,
    }
    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return lock


def locked_template_zip(lock_path: Path, cache_dir: Path | None = None) -> tuple[Path, dict[str, object]]:
    lock_path = lock_path.expanduser().resolve()
    lock = read_json_object(lock_path, "template lock")
    if lock.get("status") != "template_locked":
        raise SystemExit(f"Template lock is not ready: {lock_path}")
    expected_bytes = int(lock.get("source_bytes", 0) or 0)
    expected_sha256 = str(lock.get("source_sha256", ""))
    template_id = str(lock.get("template_id", ""))
    template_version = str(lock.get("template_version") or lock.get("template_project_version", ""))
    source_url = str(lock.get("source_url", ""))
    if source_url:
        return download_template_source(
            source_url,
            cache_dir or (lock_path.parent / ".falsiflow_template_cache"),
            template_id,
            template_version,
            expected_bytes,
            expected_sha256,
        ), lock
    raw_cached_source = str(lock.get("cached_source_path", ""))
    cached_source_path = Path(raw_cached_source).expanduser()
    if raw_cached_source and not cached_source_path.is_absolute():
        cached_source_path = (lock_path.parent / cached_source_path).resolve()
    if raw_cached_source and cached_source_path.exists() and cached_source_path.is_file():
        source_path = cached_source_path
    else:
        source_path = Path(str(lock.get("source_path", ""))).expanduser()
    if not source_path.is_absolute():
        source_path = (lock_path.parent / source_path).resolve()
    if not source_path.exists() or not source_path.is_file():
        raise SystemExit(f"Locked template pack source does not exist: {source_path}")
    actual_bytes = source_path.stat().st_size
    if actual_bytes != expected_bytes:
        raise SystemExit(f"Locked template pack byte size mismatch: expected {expected_bytes}, got {actual_bytes}")
    actual_sha256 = sha256_file(source_path)
    if actual_sha256 != expected_sha256:
        raise SystemExit(f"Locked template pack SHA-256 mismatch: expected {expected_sha256}, got {actual_sha256}")
    return source_path, lock
