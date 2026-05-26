"""Evidence source manifest and bundle helpers for Falsiflow."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import zipfile

from .core import (
    allowed_roots,
    load_project,
    read_csv_rows_with_diagnostics,
    resolve_source_file,
    source_file_base_dir,
    write_render_artifacts,
)


def markdown_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def bundle_member_path(report: dict[str, object], member: str) -> str:
    input_path = str(report.get("input_path", "") or report.get("bundle_dir", "") or "").strip()
    if str(report.get("input_format", "")) == "zip" and input_path:
        return f"{input_path}:{member}"
    bundle_dir = str(report.get("bundle_dir", "") or input_path).strip()
    if bundle_dir:
        return str(Path(bundle_dir) / member)
    return member


def bundle_review_artifact_index(report: dict[str, object]) -> list[dict[str, object]]:
    status = str(report.get("status", ""))
    integrity = str(report.get("integrity_status", ""))
    bundle_status = str(report.get("bundle_status", ""))
    input_path = str(report.get("input_path", "") or report.get("bundle_dir", "") or "").strip()
    rows = [
        {
            "artifact": "Bundle input",
            "status": status,
            "path": input_path,
            "purpose": "Received zip or bundle directory being verified before review or forwarding.",
        },
        {
            "artifact": "Bundle manifest",
            "status": bundle_status,
            "path": str(report.get("manifest_path", "") or bundle_member_path(report, "bundle_manifest.json")),
            "purpose": "Declared bundle contents, roles, byte counts, and SHA-256 hashes.",
        },
        {
            "artifact": "Audit review",
            "status": bundle_status,
            "path": bundle_member_path(report, "audit/audit_review.md"),
            "purpose": "Reviewer decision card for the claim audit.",
        },
        {
            "artifact": "Claim audit",
            "status": bundle_status,
            "path": bundle_member_path(report, "audit/claim_audit.md"),
            "purpose": "Detailed gate-by-gate evidence evaluation.",
        },
        {
            "artifact": "Source manifest",
            "status": bundle_status,
            "path": bundle_member_path(report, "source_manifest.md"),
            "purpose": "Source-file provenance, missing-file, blank-row, and allowed-root review.",
        },
        {
            "artifact": "Dashboard",
            "status": bundle_status,
            "path": bundle_member_path(report, "audit/dashboard.html"),
            "purpose": "Browser-readable view of measured evidence and claim state.",
        },
        {
            "artifact": "Integrity issues",
            "status": integrity,
            "path": str(report.get("input_path", "") or report.get("bundle_dir", "")),
            "purpose": "Use the issues table below if integrity is not verified.",
        },
    ]
    return [row for row in rows if str(row.get("path", "")).strip()]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_record(root: Path, path: Path, role: str) -> dict[str, object]:
    return {
        "role": role,
        "path": str(path.relative_to(root)),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def safe_source_relative_path(source_file: str) -> Path:
    path = Path(source_file)
    parts = [part for part in path.parts if part not in {"", ".", "..", path.anchor}]
    if path.is_absolute():
        parts = ["absolute", *parts]
    if not parts:
        parts = ["source_file"]
    return Path(*parts)


def write_bundle_manifest(
    out_dir: Path,
    project: dict[str, object],
    audit: dict[str, object],
    manifest: dict[str, object],
    zip_path: Path | None,
) -> dict[str, object]:
    artifacts: list[dict[str, object]] = []
    for path, role in [
        (out_dir / "inputs" / "project.json", "project_config"),
        (out_dir / "inputs" / "evidence.csv", "evidence_csv"),
        (out_dir / "audit" / "measurement_template.csv", "measurement_template"),
        (out_dir / "audit" / "claim_audit.json", "claim_audit"),
        (out_dir / "audit" / "claim_audit.md", "claim_audit_report"),
        (out_dir / "audit" / "audit_review.json", "audit_review"),
        (out_dir / "audit" / "audit_review.md", "audit_review_report"),
        (out_dir / "audit" / "claim_summary.json", "claim_summary"),
        (out_dir / "audit" / "next_actions.json", "next_actions"),
        (out_dir / "audit" / "dashboard.html", "dashboard"),
        (out_dir / "source_manifest.json", "source_manifest"),
        (out_dir / "source_manifest.md", "source_manifest_report"),
    ]:
        if path.exists():
            artifacts.append(artifact_record(out_dir, path, role))

    copied_sources = []
    for path in sorted((out_dir / "sources").rglob("*")) if (out_dir / "sources").exists() else []:
        if path.is_file():
            record = artifact_record(out_dir, path, "source_file")
            copied_sources.append(record)
            artifacts.append(record)

    bundle_ready = bool(audit.get("claim_ready")) and manifest.get("status") == "sources_ready"
    bundle = {
        "status": "bundle_ready" if bundle_ready else "bundle_blocked",
        "project_id": str(project.get("project", {}).get("id", "")),
        "claim_id": str(project.get("claim", {}).get("id", "")),
        "audit_status": audit.get("status", ""),
        "claim_ready": bool(audit.get("claim_ready")),
        "source_status": manifest.get("status", ""),
        "artifact_count": len(artifacts),
        "source_file_count": len(copied_sources),
        "artifacts": artifacts,
        "copied_source_files": copied_sources,
        "zip_path": str(zip_path) if zip_path else "",
    }
    (out_dir / "bundle_manifest.json").write_text(json.dumps(bundle, indent=2, sort_keys=True), encoding="utf-8")
    return bundle


def zip_bundle(out_dir: Path, zip_path: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(out_dir.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(out_dir))


def verification_issue(
    severity: str,
    code: str,
    message: str,
    path: str = "",
    expected: object | None = None,
    actual: object | None = None,
) -> dict[str, object]:
    issue: dict[str, object] = {
        "severity": severity,
        "code": code,
        "message": message,
        "path": path,
    }
    if expected is not None:
        issue["expected"] = expected
    if actual is not None:
        issue["actual"] = actual
    return issue


def verification_failure_report(
    input_path: Path,
    input_format: str,
    issues: list[dict[str, object]],
    manifest_path: Path | None = None,
) -> dict[str, object]:
    return {
        "status": "bundle_failed",
        "integrity_status": "integrity_failed",
        "bundle_status": "",
        "input_format": input_format,
        "input_path": str(input_path),
        "bundle_dir": str(input_path),
        "manifest_path": str(manifest_path or (input_path / "bundle_manifest.json")),
        "artifact_count": 0,
        "checked_artifact_count": 0,
        "missing_artifact_count": 0,
        "bytes_mismatch_count": 0,
        "hash_mismatch_count": 0,
        "unsafe_path_count": sum(1 for issue in issues if issue["code"] in {"unsafe_artifact_path", "unsafe_zip_member"}),
        "duplicate_path_count": sum(1 for issue in issues if issue["code"] in {"duplicate_artifact_path", "duplicate_zip_member"}),
        "unmanifested_file_count": 0,
        "zip_member_count": 0,
        "zip_extracted_file_count": 0,
        "zip_issue_count": sum(1 for issue in issues if str(issue["code"]).startswith("zip_") or issue["code"] in {"unsafe_zip_member", "duplicate_zip_member"}),
        "issue_count": len(issues),
        "error_count": sum(1 for issue in issues if issue.get("severity") == "error"),
        "warning_count": sum(1 for issue in issues if issue.get("severity") == "warning"),
        "issues": issues,
    }


def relative_artifact_path(bundle_dir: Path, raw_path: object, issues: list[dict[str, object]]) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path.strip():
        issues.append(verification_issue("error", "invalid_artifact_path", "Artifact path must be a non-empty string."))
        return None
    path = Path(raw_path)
    if path.is_absolute() or ".." in path.parts:
        issues.append(verification_issue("error", "unsafe_artifact_path", "Artifact path must stay inside the bundle.", raw_path))
        return None
    resolved_bundle = bundle_dir.resolve()
    resolved_path = (bundle_dir / path).resolve()
    try:
        resolved_path.relative_to(resolved_bundle)
    except ValueError:
        issues.append(verification_issue("error", "unsafe_artifact_path", "Artifact path resolves outside the bundle.", raw_path))
        return None
    return resolved_path


def is_sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdefABCDEF" for char in value)


def verify_bundle(bundle_dir: Path, input_path: Path | None = None, input_format: str = "directory") -> dict[str, object]:
    input_path = input_path or bundle_dir
    issues: list[dict[str, object]] = []
    manifest_path = bundle_dir / "bundle_manifest.json"
    if not bundle_dir.exists():
        issues.append(verification_issue("error", "bundle_dir_missing", "Bundle directory does not exist.", str(bundle_dir)))
    if not bundle_dir.is_dir():
        issues.append(verification_issue("error", "bundle_dir_not_directory", "Bundle path is not a directory.", str(bundle_dir)))
    if issues:
        return verification_failure_report(input_path, input_format, issues, manifest_path)

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        manifest = {}
        issues.append(verification_issue("error", "manifest_missing", "bundle_manifest.json is missing.", "bundle_manifest.json"))
    except json.JSONDecodeError as exc:
        manifest = {}
        issues.append(verification_issue("error", "manifest_invalid_json", f"bundle_manifest.json is not valid JSON: {exc}", "bundle_manifest.json"))

    if not isinstance(manifest, dict):
        issues.append(verification_issue("error", "manifest_not_object", "bundle_manifest.json must contain a JSON object.", "bundle_manifest.json"))
        manifest = {}

    required_fields = [
        "status",
        "project_id",
        "claim_id",
        "audit_status",
        "claim_ready",
        "source_status",
        "artifact_count",
        "source_file_count",
        "artifacts",
        "copied_source_files",
    ]
    for field in required_fields:
        if field not in manifest:
            issues.append(verification_issue("error", "manifest_field_missing", f"Manifest is missing `{field}`.", "bundle_manifest.json"))

    artifacts_raw = manifest.get("artifacts", [])
    if not isinstance(artifacts_raw, list):
        issues.append(verification_issue("error", "manifest_artifacts_invalid", "Manifest `artifacts` must be an array.", "bundle_manifest.json"))
        artifacts: list[object] = []
    else:
        artifacts = artifacts_raw

    copied_sources_raw = manifest.get("copied_source_files", [])
    if not isinstance(copied_sources_raw, list):
        issues.append(verification_issue("error", "manifest_sources_invalid", "Manifest `copied_source_files` must be an array.", "bundle_manifest.json"))
        copied_sources: list[object] = []
    else:
        copied_sources = copied_sources_raw

    if manifest.get("artifact_count") != len(artifacts):
        issues.append(verification_issue("error", "artifact_count_mismatch", "Manifest artifact_count does not match artifacts length.", "bundle_manifest.json", len(artifacts), manifest.get("artifact_count")))
    if manifest.get("source_file_count") != len(copied_sources):
        issues.append(verification_issue("error", "source_file_count_mismatch", "Manifest source_file_count does not match copied_source_files length.", "bundle_manifest.json", len(copied_sources), manifest.get("source_file_count")))

    required_roles = {
        "project_config",
        "evidence_csv",
        "measurement_template",
        "claim_audit",
        "claim_audit_report",
        "audit_review",
        "audit_review_report",
        "claim_summary",
        "next_actions",
        "dashboard",
        "source_manifest",
        "source_manifest_report",
    }
    artifact_roles: set[str] = set()
    artifact_by_path: dict[str, dict[str, object]] = {}
    source_artifact_paths: set[str] = set()
    checked_artifact_count = 0
    missing_artifact_count = 0
    bytes_mismatch_count = 0
    hash_mismatch_count = 0
    duplicate_path_count = 0

    for index, artifact in enumerate(artifacts):
        artifact_path = f"artifacts[{index}]"
        if not isinstance(artifact, dict):
            issues.append(verification_issue("error", "artifact_invalid", "Artifact entry must be an object.", artifact_path))
            continue
        role = artifact.get("role")
        raw_path = artifact.get("path")
        expected_bytes = artifact.get("bytes")
        expected_sha256 = artifact.get("sha256")
        if not isinstance(role, str) or not role:
            issues.append(verification_issue("error", "artifact_role_invalid", "Artifact role must be a non-empty string.", artifact_path))
        else:
            artifact_roles.add(role)
        if not isinstance(expected_bytes, int) or expected_bytes < 0:
            issues.append(verification_issue("error", "artifact_bytes_invalid", "Artifact bytes must be a non-negative integer.", artifact_path))
        if not is_sha256(expected_sha256):
            issues.append(verification_issue("error", "artifact_sha256_invalid", "Artifact sha256 must be a 64-character hex digest.", artifact_path))

        resolved = relative_artifact_path(bundle_dir, raw_path, issues)
        normalized_path = Path(raw_path).as_posix() if isinstance(raw_path, str) else artifact_path
        if isinstance(raw_path, str):
            if normalized_path in artifact_by_path:
                duplicate_path_count += 1
                issues.append(verification_issue("error", "duplicate_artifact_path", "Artifact path appears more than once.", normalized_path))
            artifact_by_path[normalized_path] = artifact
        if role == "source_file":
            source_artifact_paths.add(normalized_path)
        if resolved is None:
            continue
        if not resolved.exists():
            missing_artifact_count += 1
            issues.append(verification_issue("error", "artifact_missing", "Artifact file is missing.", normalized_path))
            continue
        if not resolved.is_file():
            issues.append(verification_issue("error", "artifact_not_file", "Artifact path is not a file.", normalized_path))
            continue
        checked_artifact_count += 1
        actual_bytes = resolved.stat().st_size
        if isinstance(expected_bytes, int) and actual_bytes != expected_bytes:
            bytes_mismatch_count += 1
            issues.append(verification_issue("error", "artifact_bytes_mismatch", "Artifact byte size does not match manifest.", normalized_path, expected_bytes, actual_bytes))
        if is_sha256(expected_sha256):
            actual_sha256 = sha256_file(resolved)
            if str(expected_sha256).lower() != actual_sha256.lower():
                hash_mismatch_count += 1
                issues.append(verification_issue("error", "artifact_hash_mismatch", "Artifact SHA-256 does not match manifest.", normalized_path, expected_sha256, actual_sha256))

    for role in sorted(required_roles - artifact_roles):
        issues.append(verification_issue("error", "required_role_missing", f"Required artifact role `{role}` is missing.", "bundle_manifest.json"))

    for index, source in enumerate(copied_sources):
        source_path = f"copied_source_files[{index}]"
        if not isinstance(source, dict):
            issues.append(verification_issue("error", "copied_source_invalid", "Copied source entry must be an object.", source_path))
            continue
        raw_path = source.get("path")
        normalized_path = Path(raw_path).as_posix() if isinstance(raw_path, str) else source_path
        artifact = artifact_by_path.get(normalized_path)
        if artifact is None:
            issues.append(verification_issue("error", "copied_source_not_artifact", "Copied source is not listed in artifacts.", normalized_path))
            continue
        if artifact.get("role") != "source_file":
            issues.append(verification_issue("error", "copied_source_role_mismatch", "Copied source artifact must use role `source_file`.", normalized_path))
        for field in ["bytes", "sha256"]:
            if source.get(field) != artifact.get(field):
                issues.append(verification_issue("error", "copied_source_record_mismatch", f"Copied source `{field}` does not match artifact record.", normalized_path, artifact.get(field), source.get(field)))

    if isinstance(manifest.get("source_file_count"), int) and manifest.get("source_file_count") != len(source_artifact_paths):
        issues.append(verification_issue("error", "source_artifact_count_mismatch", "source_file_count does not match artifacts with role `source_file`.", "bundle_manifest.json", len(source_artifact_paths), manifest.get("source_file_count")))

    manifested_paths = set(artifact_by_path)
    unmanifested_files = [
        path.relative_to(bundle_dir).as_posix()
        for path in sorted(bundle_dir.rglob("*"))
        if path.is_file() and path.relative_to(bundle_dir).as_posix() not in manifested_paths and path.name != "bundle_manifest.json"
    ]
    for path in unmanifested_files:
        issues.append(verification_issue("error", "unmanifested_file", "Bundle contains a file not listed in bundle_manifest.json.", path))

    error_count = sum(1 for issue in issues if issue.get("severity") == "error")
    warning_count = sum(1 for issue in issues if issue.get("severity") == "warning")
    integrity_status = "integrity_failed" if error_count else "integrity_verified"
    bundle_status = str(manifest.get("status", ""))
    if error_count:
        status = "bundle_failed"
    elif bundle_status == "bundle_ready":
        status = "bundle_verified"
    else:
        status = "bundle_blocked"

    return {
        "status": status,
        "integrity_status": integrity_status,
        "bundle_status": bundle_status,
        "input_format": input_format,
        "input_path": str(input_path),
        "bundle_dir": str(bundle_dir),
        "manifest_path": str(manifest_path),
        "artifact_count": len(artifacts),
        "checked_artifact_count": checked_artifact_count,
        "missing_artifact_count": missing_artifact_count,
        "bytes_mismatch_count": bytes_mismatch_count,
        "hash_mismatch_count": hash_mismatch_count,
        "unsafe_path_count": sum(1 for issue in issues if issue["code"] == "unsafe_artifact_path"),
        "duplicate_path_count": duplicate_path_count,
        "unmanifested_file_count": len(unmanifested_files),
        "issue_count": len(issues),
        "error_count": error_count,
        "warning_count": warning_count,
        "issues": issues,
    }


def safe_zip_member_relative_path(member_name: str) -> Path | None:
    normalized = member_name.replace("\\", "/").strip("/")
    if not normalized:
        return None
    parts = [part for part in normalized.split("/") if part not in {"", "."}]
    if not parts or any(part == ".." for part in parts):
        return None
    if member_name.startswith(("/", "\\")):
        return None
    return Path(*parts)


def extracted_bundle_root(extract_root: Path, issues: list[dict[str, object]]) -> Path:
    if (extract_root / "bundle_manifest.json").exists():
        return extract_root
    manifests = sorted(extract_root.rglob("bundle_manifest.json"))
    if len(manifests) == 1:
        bundle_root = manifests[0].parent
        outside_files = [
            path.relative_to(extract_root).as_posix()
            for path in sorted(extract_root.rglob("*"))
            if path.is_file() and not path.resolve().is_relative_to(bundle_root.resolve())
        ]
        for path in outside_files:
            issues.append(verification_issue("error", "zip_file_outside_bundle_root", "Zip contains a file outside the detected bundle root.", path))
        return bundle_root
    if len(manifests) > 1:
        for manifest in manifests:
            issues.append(verification_issue("error", "multiple_bundle_manifests", "Zip contains multiple bundle_manifest.json files.", manifest.relative_to(extract_root).as_posix()))
    return extract_root


def merge_verification_issues(report: dict[str, object], extra_issues: list[dict[str, object]]) -> dict[str, object]:
    issues = [*extra_issues, *list(report.get("issues", []))]
    error_count = sum(1 for issue in issues if issue.get("severity") == "error")
    warning_count = sum(1 for issue in issues if issue.get("severity") == "warning")
    report["issues"] = issues
    report["issue_count"] = len(issues)
    report["error_count"] = error_count
    report["warning_count"] = warning_count
    report["unsafe_path_count"] = sum(1 for issue in issues if issue["code"] in {"unsafe_artifact_path", "unsafe_zip_member"})
    report["duplicate_path_count"] = sum(1 for issue in issues if issue["code"] in {"duplicate_artifact_path", "duplicate_zip_member"})
    report["zip_issue_count"] = sum(1 for issue in extra_issues if issue.get("severity") == "error")
    if error_count:
        report["status"] = "bundle_failed"
        report["integrity_status"] = "integrity_failed"
    return report


def verify_bundle_zip(zip_path: Path) -> dict[str, object]:
    issues: list[dict[str, object]] = []
    if not zip_path.exists():
        issues.append(verification_issue("error", "zip_missing", "Bundle zip does not exist.", str(zip_path)))
    if not zip_path.is_file():
        issues.append(verification_issue("error", "zip_not_file", "Bundle zip path is not a file.", str(zip_path)))
    if issues:
        return verification_failure_report(zip_path, "zip", issues, zip_path)

    try:
        archive = zipfile.ZipFile(zip_path)
    except zipfile.BadZipFile as exc:
        issues.append(verification_issue("error", "zip_invalid", f"Bundle zip is not a valid zip archive: {exc}", str(zip_path)))
        return verification_failure_report(zip_path, "zip", issues, zip_path)

    with archive:
        infos = archive.infolist()
        with tempfile.TemporaryDirectory(prefix="falsiflow_bundle_zip_") as tmp:
            extract_root = Path(tmp) / "bundle"
            extract_root.mkdir(parents=True, exist_ok=True)
            seen_files: set[str] = set()
            extracted_file_count = 0
            for info in infos:
                relative_path = safe_zip_member_relative_path(info.filename)
                if relative_path is None:
                    issues.append(verification_issue("error", "unsafe_zip_member", "Zip member path is empty, absolute, or escapes the archive root.", info.filename))
                    continue
                normalized = relative_path.as_posix()
                if info.is_dir():
                    (extract_root / relative_path).mkdir(parents=True, exist_ok=True)
                    continue
                if normalized in seen_files:
                    issues.append(verification_issue("error", "duplicate_zip_member", "Zip member path appears more than once.", normalized))
                    continue
                seen_files.add(normalized)
                destination = (extract_root / relative_path).resolve()
                try:
                    destination.relative_to(extract_root.resolve())
                except ValueError:
                    issues.append(verification_issue("error", "unsafe_zip_member", "Zip member resolves outside the extraction root.", info.filename))
                    continue
                destination.parent.mkdir(parents=True, exist_ok=True)
                try:
                    with archive.open(info, "r") as source, destination.open("wb") as target:
                        shutil.copyfileobj(source, target)
                    extracted_file_count += 1
                except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
                    issues.append(verification_issue("error", "zip_member_read_failed", f"Could not extract zip member: {exc}", normalized))

            bundle_root = extracted_bundle_root(extract_root, issues)
            report = verify_bundle(bundle_root, input_path=zip_path, input_format="zip")
            report["bundle_dir"] = str(zip_path)
            report["zip_path"] = str(zip_path)
            report["zip_member_count"] = len(infos)
            report["zip_extracted_file_count"] = extracted_file_count
            report["zip_bundle_root"] = bundle_root.relative_to(extract_root).as_posix() if bundle_root != extract_root else "."
            report["manifest_path"] = f"{zip_path}:{Path(report['manifest_path']).relative_to(bundle_root).as_posix()}" if (bundle_root / "bundle_manifest.json").exists() else f"{zip_path}:bundle_manifest.json"
            return merge_verification_issues(report, issues)


def render_bundle_verification_report(report: dict[str, object]) -> str:
    lines = [
        "# Falsiflow Bundle Verification",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Integrity: `{report.get('integrity_status', '')}`",
        f"- Bundle status: `{report.get('bundle_status', '')}`",
        f"- Input: `{report.get('input_format', '')}` `{report.get('input_path', '')}`",
        f"- Artifacts checked: {report.get('checked_artifact_count', 0)}/{report.get('artifact_count', 0)}",
        f"- Issues: {report.get('issue_count', 0)} errors={report.get('error_count', 0)} warnings={report.get('warning_count', 0)}",
        "",
        "## Review Artifact Index",
        "",
        "| Artifact | Status | Path | Purpose |",
        "| --- | --- | --- | --- |",
    ]
    for artifact in bundle_review_artifact_index(report):
        lines.append(
            "| "
            + " | ".join([
                markdown_cell(artifact.get("artifact", "")),
                f"`{markdown_cell(artifact.get('status', ''))}`",
                f"`{markdown_cell(artifact.get('path', ''))}`",
                markdown_cell(artifact.get("purpose", "")),
            ])
            + " |"
        )
    lines.extend([
        "",
        "## Counters",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
    ])
    for key in [
        "missing_artifact_count",
        "bytes_mismatch_count",
        "hash_mismatch_count",
        "unsafe_path_count",
        "duplicate_path_count",
        "unmanifested_file_count",
        "zip_member_count",
        "zip_extracted_file_count",
        "zip_issue_count",
    ]:
        if key in report:
            lines.append(f"| `{key}` | {report.get(key, 0)} |")
    issues = report.get("issues", [])
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


def build_bundle(config: Path, evidence: Path, out_dir: Path, zip_out: Path | None = None, force: bool = False) -> dict[str, object]:
    project = load_project(config)
    if not evidence.exists():
        raise SystemExit(f"Evidence file does not exist: {evidence}")
    if out_dir.exists() and any(out_dir.iterdir()) and not force:
        raise SystemExit(f"Refusing to overwrite non-empty directory without --force: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "inputs").mkdir(parents=True, exist_ok=True)
    (out_dir / "sources").mkdir(parents=True, exist_ok=True)

    shutil.copy2(config, out_dir / "inputs" / "project.json")
    shutil.copy2(evidence, out_dir / "inputs" / "evidence.csv")

    evidence_rows, evidence_issues = read_csv_rows_with_diagnostics(evidence)
    rendered = write_render_artifacts(project, evidence_rows, out_dir / "audit", evidence_file_issues=evidence_issues)
    audit = rendered["audit"]
    manifest = source_manifest(project, evidence_rows, evidence_issues)
    (out_dir / "source_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    (out_dir / "source_manifest.md").write_text(render_source_manifest_report(manifest), encoding="utf-8")

    for record in manifest.get("source_files", []):
        if not isinstance(record, dict) or record.get("status") != "present":
            continue
        source_file = str(record.get("source_file", ""))
        source_path = Path(str(record.get("resolved_path", "")))
        destination = out_dir / "sources" / safe_source_relative_path(source_file)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination)

    bundle = write_bundle_manifest(out_dir, project, audit, manifest, zip_out)
    if zip_out is not None:
        zip_bundle(out_dir, zip_out)
    return bundle


def source_manifest(project: dict[str, object], evidence_rows: list[dict[str, str]], evidence_issues: list[dict[str, object]]) -> dict[str, object]:
    policy = project.get("evidence_policy", {})
    policy = policy if isinstance(policy, dict) else {}
    require_sources = bool(policy.get("require_source_files", True))
    roots = allowed_roots(project)
    base_dir = source_file_base_dir(project)
    source_records: dict[str, dict[str, object]] = {}
    blank_source_rows: list[dict[str, object]] = []

    for row_number, row in enumerate(evidence_rows, start=2):
        source_file = str(row.get("source_file", "") or "").strip()
        reference = {
            "row_number": row_number,
            "gate_id": str(row.get("gate_id", "")),
            "candidate_id": str(row.get("candidate_id", "")),
            "sample_id": str(row.get("sample_id", "")),
            "field": str(row.get("field", "")),
        }
        if not source_file:
            blank_source_rows.append(reference)
            continue
        record = source_records.setdefault(source_file, {
            "source_file": source_file,
            "reference_count": 0,
            "references": [],
        })
        record["reference_count"] = int(record["reference_count"]) + 1
        references = record["references"]
        if isinstance(references, list) and len(references) < 50:
            references.append(reference)

    source_files = []
    missing_count = 0
    outside_allowed_roots_count = 0
    present_count = 0
    for source_file, record in sorted(source_records.items()):
        resolved = resolve_source_file(project, source_file)
        exists = resolved.exists()
        within_allowed_roots = not roots or any(resolved == root or root in resolved.parents for root in roots)
        status = "present"
        issue = ""
        if not exists:
            status = "missing"
            issue = "source_file does not exist"
            missing_count += 1
        elif not within_allowed_roots:
            status = "outside_allowed_roots"
            issue = "source_file outside allowed roots"
            outside_allowed_roots_count += 1
        else:
            present_count += 1
        source_files.append({
            **record,
            "status": status,
            "exists": exists,
            "within_allowed_roots": within_allowed_roots,
            "resolved_path": str(resolved),
            "issue": issue,
        })

    evidence_file_error_count = sum(1 for issue in evidence_issues if issue.get("level") == "error")
    evidence_file_warning_count = sum(1 for issue in evidence_issues if issue.get("level") == "warning")
    source_blocker_count = (
        len(blank_source_rows) + missing_count + outside_allowed_roots_count
        if require_sources
        else 0
    )
    blocker_count = evidence_file_error_count + source_blocker_count

    return {
        "status": "sources_ready" if blocker_count == 0 else "sources_blocked",
        "project_id": str(project.get("project", {}).get("id", "")),
        "claim_id": str(project.get("claim", {}).get("id", "")),
        "source_policy_required": require_sources,
        "source_file_base_dir": str(base_dir),
        "allowed_source_roots": [str(root) for root in roots],
        "evidence_row_count": len(evidence_rows),
        "referenced_source_file_count": len(source_files),
        "present_source_file_count": present_count,
        "missing_source_file_count": missing_count,
        "outside_allowed_roots_count": outside_allowed_roots_count,
        "blank_source_row_count": len(blank_source_rows),
        "source_blocker_count": source_blocker_count,
        "evidence_file_issue_count": len(evidence_issues),
        "evidence_file_error_count": evidence_file_error_count,
        "evidence_file_warning_count": evidence_file_warning_count,
        "blocker_count": blocker_count,
        "blank_source_rows": blank_source_rows[:200],
        "source_files": source_files,
    }


def render_source_manifest_report(manifest: dict[str, object]) -> str:
    lines = [
        "# Falsiflow Source Manifest",
        "",
        f"**Status:** `{manifest.get('status')}`",
        f"**Project:** `{manifest.get('project_id')}`",
        f"**Claim:** `{manifest.get('claim_id')}`",
        f"**Source policy required:** `{str(bool(manifest.get('source_policy_required'))).lower()}`",
        f"**Evidence rows:** {manifest.get('evidence_row_count', 0)}",
        f"**Referenced source files:** {manifest.get('referenced_source_file_count', 0)}",
        f"**Present:** {manifest.get('present_source_file_count', 0)}",
        f"**Missing:** {manifest.get('missing_source_file_count', 0)}",
        f"**Outside allowed roots:** {manifest.get('outside_allowed_roots_count', 0)}",
        f"**Blank source rows:** {manifest.get('blank_source_row_count', 0)}",
        f"**Evidence file errors / warnings:** {manifest.get('evidence_file_error_count', 0)} / {manifest.get('evidence_file_warning_count', 0)}",
        "",
        "## Source Files",
        "",
        "| Source file | Status | References | Resolved path | Issue |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for record in manifest.get("source_files", []):
        if not isinstance(record, dict):
            continue
        lines.append(
            "| "
            + " | ".join([
                markdown_cell(record.get("source_file", "")),
                markdown_cell(record.get("status", "")),
                markdown_cell(record.get("reference_count", 0)),
                markdown_cell(record.get("resolved_path", "")),
                markdown_cell(record.get("issue", "")),
            ])
            + " |"
        )
    if manifest.get("blank_source_rows"):
        lines.extend([
            "",
            "## Blank Source Rows",
            "",
            "| Row | Gate | Candidate | Sample | Field |",
            "| ---: | --- | --- | --- | --- |",
        ])
        for row in manifest.get("blank_source_rows", []):
            if not isinstance(row, dict):
                continue
            lines.append(
                "| "
                + " | ".join([
                    markdown_cell(row.get("row_number", "")),
                    markdown_cell(row.get("gate_id", "")),
                    markdown_cell(row.get("candidate_id", "")),
                    markdown_cell(row.get("sample_id", "")),
                    markdown_cell(row.get("field", "")),
                ])
                + " |"
            )
    lines.append("")
    return "\n".join(lines)
