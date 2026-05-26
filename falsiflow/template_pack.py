"""Template pack manifest and verification helpers."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import zipfile

from .bundle import zip_bundle
from .template_check import run_template_check


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_record(root: Path, path: Path, role: str) -> dict[str, object]:
    relative = path.relative_to(root).as_posix()
    return {
        "path": relative,
        "role": role,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def is_sha256(value: object) -> bool:
    text = str(value or "")
    return len(text) == 64 and all(char in "0123456789abcdefABCDEF" for char in text)


def markdown_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def verification_issue(
    severity: str,
    code: str,
    message: str,
    path: str = "",
    expected: object = "",
    actual: object = "",
) -> dict[str, object]:
    issue: dict[str, object] = {
        "severity": severity,
        "code": code,
        "message": message,
        "path": path,
    }
    if expected != "":
        issue["expected"] = expected
    if actual != "":
        issue["actual"] = actual
    return issue


def relative_artifact_path(bundle_dir: Path, raw_path: object, issues: list[dict[str, object]]) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path:
        issues.append(verification_issue("error", "artifact_path_invalid", "Artifact path must be a non-empty relative path."))
        return None
    path = Path(raw_path)
    if path.is_absolute() or ".." in path.parts:
        issues.append(verification_issue("error", "unsafe_artifact_path", "Artifact path is absolute or escapes the bundle.", raw_path))
        return None
    resolved = (bundle_dir / path).resolve()
    try:
        resolved.relative_to(bundle_dir.resolve())
    except ValueError:
        issues.append(verification_issue("error", "unsafe_artifact_path", "Artifact path resolves outside the bundle.", raw_path))
        return None
    return resolved


def safe_zip_member_relative_path(member_name: str) -> Path | None:
    if not member_name or member_name.startswith("/"):
        return None
    path = Path(member_name)
    if path.is_absolute() or ".." in path.parts:
        return None
    return path


def template_pack_artifact_role(relative_path: Path) -> str:
    path = relative_path.as_posix()
    if path == "template/template.json":
        return "template_manifest"
    if path == "template/project.json":
        return "project_config"
    if path == "template/evidence_pass_demo.csv":
        return "pass_demo_evidence"
    if path == "template/evidence_placeholder_demo.csv":
        return "placeholder_demo_evidence"
    if path == "template/README.md":
        return "template_readme"
    if path.startswith("template/source_files/"):
        return "template_source_file"
    if path == "checks/template_check.json":
        return "template_check_summary"
    if path == "checks/template_check.md":
        return "template_check_report"
    if path == "checks/bundle_verification.json":
        return "template_bundle_verification"
    if path == "checks/bundle_verification.md":
        return "template_bundle_verification_report"
    if path.startswith("checks/"):
        return "template_check_artifact"
    return "template_file"


def write_template_pack_manifest(
    out_dir: Path,
    template_manifest: dict[str, object],
    template_check: dict[str, object],
    zip_path: Path | None,
) -> dict[str, object]:
    artifacts = [
        artifact_record(out_dir, path, template_pack_artifact_role(path.relative_to(out_dir)))
        for path in sorted(out_dir.rglob("*"))
        if path.is_file() and path.name != "template_pack_manifest.json"
    ]
    template_ready = template_check.get("status") == "template_ready"
    manifest: dict[str, object] = {
        "status": "template_pack_ready" if template_ready else "template_pack_blocked",
        "template_id": str(template_manifest.get("id") or ""),
        "template_name": str(template_manifest.get("name") or ""),
        "template_domain": str(template_manifest.get("domain") or ""),
        "template_check_status": str(template_check.get("status", "")),
        "template_check_failure_count": int(template_check.get("failure_count", 0) or 0),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "zip_path": str(zip_path) if zip_path else "",
    }
    (out_dir / "template_pack_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest


def run_template_pack(
    template_dir: Path,
    out_dir: Path,
    zip_out: Path,
    verification_out: Path | None = None,
    report_out: Path | None = None,
    force: bool = False,
    template_check_runner=run_template_check,
) -> dict[str, object]:
    template_dir = template_dir.resolve()
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"Refusing to write template pack into non-empty directory without --force: {out_dir}")
        shutil.rmtree(out_dir)
    resolved_out = out_dir.resolve()
    resolved_template = template_dir.resolve()
    resolved_zip = zip_out.resolve()
    if resolved_out == resolved_template or resolved_template in resolved_out.parents:
        raise SystemExit("Refusing to write a template pack inside the source template directory.")
    if resolved_zip == resolved_out or resolved_out in resolved_zip.parents:
        raise SystemExit("Refusing to write template pack zip inside the pack directory.")
    for output_path in [verification_out, report_out]:
        if output_path is not None:
            resolved_output = output_path.resolve()
            if resolved_output == resolved_out or resolved_out in resolved_output.parents:
                raise SystemExit("Refusing to write template pack verification outputs inside the pack directory.")
    out_dir.mkdir(parents=True, exist_ok=True)

    packaged_template_dir = out_dir / "template"
    shutil.copytree(template_dir, packaged_template_dir)
    template_check = template_check_runner(packaged_template_dir, out_dir / "checks", force=True)
    manifest_path = packaged_template_dir / "template.json"
    template_manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    pack_manifest = write_template_pack_manifest(out_dir, template_manifest, template_check, zip_out)
    zip_bundle(out_dir, zip_out)

    verification = verify_template_pack_zip(zip_out)
    if verification_out is not None:
        verification_out.parent.mkdir(parents=True, exist_ok=True)
        verification_out.write_text(json.dumps(verification, indent=2, sort_keys=True), encoding="utf-8")
    if report_out is not None:
        report_out.parent.mkdir(parents=True, exist_ok=True)
        report_out.write_text(render_template_pack_verification_report(verification), encoding="utf-8")

    ready = pack_manifest.get("status") == "template_pack_ready" and verification.get("status") == "template_pack_verified"
    return {
        "status": "template_pack_ready" if ready else "template_pack_blocked",
        "template_id": pack_manifest.get("template_id", ""),
        "template_check_status": template_check.get("status", ""),
        "template_check_failure_count": template_check.get("failure_count", 0),
        "template_pack_status": pack_manifest.get("status", ""),
        "verification_status": verification.get("status", ""),
        "artifact_count": pack_manifest.get("artifact_count", 0),
        "pack_dir": str(out_dir),
        "zip_path": str(zip_out),
        "manifest_path": str(out_dir / "template_pack_manifest.json"),
        "verification_path": str(verification_out or ""),
        "verification_report_path": str(report_out or ""),
    }


def template_pack_failure_report(
    input_path: Path,
    input_format: str,
    issues: list[dict[str, object]],
    manifest_path: Path | None = None,
) -> dict[str, object]:
    return {
        "status": "template_pack_failed",
        "integrity_status": "integrity_failed",
        "template_pack_status": "",
        "input_format": input_format,
        "input_path": str(input_path),
        "pack_dir": str(input_path),
        "manifest_path": str(manifest_path or (input_path / "template_pack_manifest.json")),
        "template_id": "",
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


def verify_template_pack(pack_dir: Path, input_path: Path | None = None, input_format: str = "directory") -> dict[str, object]:
    input_path = input_path or pack_dir
    issues: list[dict[str, object]] = []
    manifest_path = pack_dir / "template_pack_manifest.json"
    if not pack_dir.exists():
        issues.append(verification_issue("error", "pack_dir_missing", "Template pack directory does not exist.", str(pack_dir)))
    if not pack_dir.is_dir():
        issues.append(verification_issue("error", "pack_dir_not_directory", "Template pack path is not a directory.", str(pack_dir)))
    if issues:
        return template_pack_failure_report(input_path, input_format, issues, manifest_path)

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        manifest = {}
        issues.append(verification_issue("error", "manifest_missing", "template_pack_manifest.json is missing.", "template_pack_manifest.json"))
    except json.JSONDecodeError as exc:
        manifest = {}
        issues.append(verification_issue("error", "manifest_invalid_json", f"template_pack_manifest.json is not valid JSON: {exc}", "template_pack_manifest.json"))

    if not isinstance(manifest, dict):
        issues.append(verification_issue("error", "manifest_not_object", "template_pack_manifest.json must contain a JSON object.", "template_pack_manifest.json"))
        manifest = {}

    required_fields = ["status", "template_id", "template_check_status", "artifact_count", "artifacts"]
    for field in required_fields:
        if field not in manifest:
            issues.append(verification_issue("error", "manifest_field_missing", f"Manifest is missing `{field}`.", "template_pack_manifest.json"))
    if manifest.get("status") == "template_pack_ready" and manifest.get("template_check_status") != "template_ready":
        issues.append(verification_issue("error", "template_check_status_mismatch", "Ready template packs must come from a ready template-check.", "template_pack_manifest.json", "template_ready", manifest.get("template_check_status")))

    artifacts_raw = manifest.get("artifacts", [])
    if not isinstance(artifacts_raw, list):
        issues.append(verification_issue("error", "manifest_artifacts_invalid", "Manifest `artifacts` must be an array.", "template_pack_manifest.json"))
        artifacts: list[object] = []
    else:
        artifacts = artifacts_raw
    if manifest.get("artifact_count") != len(artifacts):
        issues.append(verification_issue("error", "artifact_count_mismatch", "Manifest artifact_count does not match artifacts length.", "template_pack_manifest.json", len(artifacts), manifest.get("artifact_count")))

    required_roles = {
        "template_manifest",
        "project_config",
        "pass_demo_evidence",
        "placeholder_demo_evidence",
        "template_source_file",
        "template_check_summary",
        "template_check_report",
        "template_bundle_verification",
        "template_bundle_verification_report",
    }
    artifact_roles: set[str] = set()
    artifact_by_path: dict[str, dict[str, object]] = {}
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

        resolved = relative_artifact_path(pack_dir, raw_path, issues)
        normalized_path = Path(raw_path).as_posix() if isinstance(raw_path, str) else artifact_path
        if isinstance(raw_path, str):
            if normalized_path in artifact_by_path:
                duplicate_path_count += 1
                issues.append(verification_issue("error", "duplicate_artifact_path", "Artifact path appears more than once.", normalized_path))
            artifact_by_path[normalized_path] = artifact
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
        issues.append(verification_issue("error", "required_role_missing", f"Required artifact role `{role}` is missing.", "template_pack_manifest.json"))

    manifested_paths = set(artifact_by_path)
    unmanifested_files = [
        path.relative_to(pack_dir).as_posix()
        for path in sorted(pack_dir.rglob("*"))
        if path.is_file()
        and path.relative_to(pack_dir).as_posix() not in manifested_paths
        and path.name != "template_pack_manifest.json"
    ]
    for path in unmanifested_files:
        issues.append(verification_issue("error", "unmanifested_file", "Template pack contains a file not listed in template_pack_manifest.json.", path))

    error_count = sum(1 for issue in issues if issue.get("severity") == "error")
    warning_count = sum(1 for issue in issues if issue.get("severity") == "warning")
    integrity_status = "integrity_failed" if error_count else "integrity_verified"
    template_pack_status = str(manifest.get("status", ""))
    if error_count:
        status = "template_pack_failed"
    elif template_pack_status == "template_pack_ready":
        status = "template_pack_verified"
    else:
        status = "template_pack_blocked"

    return {
        "status": status,
        "integrity_status": integrity_status,
        "template_pack_status": template_pack_status,
        "input_format": input_format,
        "input_path": str(input_path),
        "pack_dir": str(pack_dir),
        "manifest_path": str(manifest_path),
        "template_id": str(manifest.get("template_id", "")),
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


def extracted_template_pack_root(extract_root: Path, issues: list[dict[str, object]]) -> Path:
    if (extract_root / "template_pack_manifest.json").exists():
        return extract_root
    manifests = sorted(extract_root.rglob("template_pack_manifest.json"))
    if len(manifests) == 1:
        pack_root = manifests[0].parent
        outside_files = [
            path.relative_to(extract_root).as_posix()
            for path in sorted(extract_root.rglob("*"))
            if path.is_file() and not path.resolve().is_relative_to(pack_root.resolve())
        ]
        for path in outside_files:
            issues.append(verification_issue("error", "zip_file_outside_pack_root", "Zip contains a file outside the detected template pack root.", path))
        return pack_root
    if len(manifests) > 1:
        for manifest in manifests:
            issues.append(verification_issue("error", "multiple_template_pack_manifests", "Zip contains multiple template_pack_manifest.json files.", manifest.relative_to(extract_root).as_posix()))
    return extract_root


def merge_template_pack_verification_issues(report: dict[str, object], extra_issues: list[dict[str, object]]) -> dict[str, object]:
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
        report["status"] = "template_pack_failed"
        report["integrity_status"] = "integrity_failed"
    return report


def extract_template_pack_zip(zip_path: Path, extract_root: Path) -> tuple[Path | None, list[dict[str, object]], int, int]:
    issues: list[dict[str, object]] = []
    if not zip_path.exists():
        issues.append(verification_issue("error", "zip_missing", "Template pack zip does not exist.", str(zip_path)))
    if not zip_path.is_file():
        issues.append(verification_issue("error", "zip_not_file", "Template pack zip path is not a file.", str(zip_path)))
    if issues:
        return None, issues, 0, 0

    try:
        archive = zipfile.ZipFile(zip_path)
    except zipfile.BadZipFile as exc:
        issues.append(verification_issue("error", "zip_invalid", f"Template pack zip is not a valid zip archive: {exc}", str(zip_path)))
        return None, issues, 0, 0

    with archive:
        infos = archive.infolist()
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

    pack_root = extracted_template_pack_root(extract_root, issues)
    return pack_root, issues, len(infos), extracted_file_count


def verify_template_pack_zip(zip_path: Path) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="falsiflow_template_pack_zip_") as tmp:
        extract_root = Path(tmp) / "template_pack"
        pack_root, issues, member_count, extracted_file_count = extract_template_pack_zip(zip_path, extract_root)
        if pack_root is None:
            return template_pack_failure_report(zip_path, "zip", issues, zip_path)
        report = verify_template_pack(pack_root, input_path=zip_path, input_format="zip")
        report["pack_dir"] = str(zip_path)
        report["zip_path"] = str(zip_path)
        report["zip_member_count"] = member_count
        report["zip_extracted_file_count"] = extracted_file_count
        report["zip_pack_root"] = pack_root.relative_to(extract_root).as_posix() if pack_root != extract_root else "."
        report["manifest_path"] = f"{zip_path}:{Path(report['manifest_path']).relative_to(pack_root).as_posix()}" if (pack_root / "template_pack_manifest.json").exists() else f"{zip_path}:template_pack_manifest.json"
        return merge_template_pack_verification_issues(report, issues)


def render_template_pack_verification_report(report: dict[str, object]) -> str:
    lines = [
        "# Falsiflow Template Pack Verification",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Integrity: `{report.get('integrity_status', '')}`",
        f"- Template pack status: `{report.get('template_pack_status', '')}`",
        f"- Template: `{report.get('template_id', '')}`",
        f"- Input: `{report.get('input_format', '')}` `{report.get('input_path', '')}`",
        f"- Artifacts checked: {report.get('checked_artifact_count', 0)}/{report.get('artifact_count', 0)}",
        f"- Issues: {report.get('issue_count', 0)} errors={report.get('error_count', 0)} warnings={report.get('warning_count', 0)}",
        "",
        "## Counters",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
    ]
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
