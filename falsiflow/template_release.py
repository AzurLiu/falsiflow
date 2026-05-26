"""Template release packaging and verification helpers."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import tempfile
import zipfile

from .template_pack import (
    artifact_record,
    markdown_cell,
    sha256_file,
    verification_issue,
    verify_template_pack_zip,
)
from .template_provenance import run_verify_template_attestation, run_verify_template_policy
from .template_registry import read_json_object


def zip_release_directory(release_root: Path, zip_path: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(release_root.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(release_root))


def safe_release_zip_member_relative_path(member_name: str) -> Path | None:
    normalized = member_name.replace("\\", "/").strip("/")
    if not normalized:
        return None
    parts = [part for part in normalized.split("/") if part not in {"", "."}]
    if not parts or any(part == ".." for part in parts):
        return None
    if member_name.startswith(("/", "\\")):
        return None
    return Path(*parts)


def template_release_member_path(report: dict[str, object], member: object) -> str:
    path = str(member or "").strip()
    if not path:
        return ""
    release_zip = str(report.get("release_zip_path", "") or "").strip()
    if release_zip:
        return f"{release_zip}:{path}"
    return path


def template_release_review_artifact_index(report: dict[str, object]) -> list[dict[str, object]]:
    artifact_members = report.get("artifact_members", {})
    if not isinstance(artifact_members, dict) or not artifact_members:
        artifact_paths = report.get("artifact_paths", {})
        artifact_members = artifact_paths if isinstance(artifact_paths, dict) else {}
    role_specs = [
        ("template_pack", "Template pack", "pack_verification_status", "Verified starter template pack included in this release."),
        ("template_registry", "Template registry", "status", "Registry metadata used to resolve and install the template release."),
        ("template_lock", "Template lock", "status", "Pinned template source identity, byte count, and SHA-256 hash."),
        ("template_attestation", "Template attestation", "attestation_verification_status", "Signed provenance for the template lock."),
        ("template_policy", "Template policy", "policy_verification_status", "Adoption policy checked before installation."),
    ]
    rows = [
        {
            "artifact": "Template release zip",
            "status": str(report.get("status", "")),
            "path": str(report.get("release_zip_path", "")),
            "purpose": "Portable release package verified before template installation.",
        },
        {
            "artifact": "Release manifest",
            "status": str(report.get("status", "")),
            "path": template_release_member_path(report, "template_release_manifest.json"),
            "purpose": "Manifest declaring release contents, statuses, byte counts, and hashes.",
        },
    ]
    for role, label, status_key, purpose in role_specs:
        path = str(artifact_members.get(role, "") or "").strip()
        if not path:
            continue
        rows.append({
            "artifact": label,
            "status": str(report.get(status_key, report.get("status", "")) or ""),
            "path": path if Path(path).is_absolute() else template_release_member_path(report, path),
            "purpose": purpose,
        })
    return [row for row in rows if str(row.get("path", "")).strip()]


def copy_template_release_artifact(release_root: Path, source: Path, name: str, role: str) -> dict[str, object]:
    target = release_root / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return artifact_record(release_root, target, role)


def template_release_manifest(
    release_root: Path,
    artifacts: list[dict[str, object]],
    lock: dict[str, object],
    policy: dict[str, object],
    pack_verification: dict[str, object],
    attestation_verification: dict[str, object],
    policy_verification: dict[str, object],
    issues: list[dict[str, object]],
) -> dict[str, object]:
    error_count = sum(1 for issue in issues if issue.get("severity") == "error")
    return {
        "status": "template_release_ready" if not error_count else "template_release_blocked",
        "template_id": str(lock.get("template_id", "")),
        "template_version": str(lock.get("template_version") or lock.get("template_project_version", "")),
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "generator": "falsiflow template-release",
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "pack_verification_status": str(pack_verification.get("status", "")),
        "attestation_verification_status": str(attestation_verification.get("status", "")),
        "policy_verification_status": str(policy_verification.get("status", "")),
        "trusted_key_id": str(policy.get("trusted_key_id", "")),
        "source_sha256": str(lock.get("source_sha256", "")),
        "issue_count": len(issues),
        "error_count": error_count,
        "warning_count": sum(1 for issue in issues if issue.get("severity") == "warning"),
        "issues": issues,
    }


def run_template_release(
    pack_zip: Path,
    registry_path: Path,
    lock_path: Path,
    attestation_path: Path,
    policy_path: Path,
    out: Path,
    signing_key: str = "",
) -> dict[str, object]:
    pack_zip = pack_zip.expanduser().resolve()
    registry_path = registry_path.expanduser().resolve()
    lock_path = lock_path.expanduser().resolve()
    attestation_path = attestation_path.expanduser().resolve()
    policy_path = policy_path.expanduser().resolve()
    out = out.expanduser().resolve()
    issues: list[dict[str, object]] = []
    missing_input = False
    for label, path in [
        ("template_pack", pack_zip),
        ("template_registry", registry_path),
        ("template_lock", lock_path),
        ("template_attestation", attestation_path),
        ("template_policy", policy_path),
    ]:
        if not path.exists() or not path.is_file():
            missing_input = True
            issues.append(verification_issue("error", f"{label}_missing", "Template release input file is missing.", str(path)))
    lock = read_json_object(lock_path, "template lock") if lock_path.exists() and lock_path.is_file() else {}
    policy = read_json_object(policy_path, "template policy") if policy_path.exists() and policy_path.is_file() else {}
    pack_verification = verify_template_pack_zip(pack_zip) if pack_zip.exists() and pack_zip.is_file() else {"status": "template_pack_failed", "issues": []}
    attestation_verification = run_verify_template_attestation(attestation_path, subject_path=lock_path, signing_key=signing_key) if attestation_path.exists() and attestation_path.is_file() and lock_path.exists() and lock_path.is_file() else {"status": "template_attestation_failed", "issues": []}
    policy_verification = run_verify_template_policy(policy_path, lock_path, attestation_path, signing_key=signing_key) if policy_path.exists() and policy_path.is_file() and lock_path.exists() and lock_path.is_file() and attestation_path.exists() and attestation_path.is_file() else {"status": "template_policy_failed", "issues": []}
    issues.extend(issue for issue in pack_verification.get("issues", []) if isinstance(issue, dict) and issue.get("severity") == "error")
    issues.extend(issue for issue in attestation_verification.get("issues", []) if isinstance(issue, dict) and issue.get("severity") == "error")
    issues.extend(issue for issue in policy_verification.get("issues", []) if isinstance(issue, dict) and issue.get("severity") == "error")
    if pack_verification.get("status") != "template_pack_verified":
        issues.append(verification_issue("error", "template_pack_not_verified", "Template release requires a verified template pack.", str(pack_zip), "template_pack_verified", pack_verification.get("status")))
    if attestation_verification.get("status") != "template_attestation_verified":
        issues.append(verification_issue("error", "attestation_not_verified", "Template release requires a verified attestation.", str(attestation_path), "template_attestation_verified", attestation_verification.get("status")))
    if policy_verification.get("status") != "template_policy_verified":
        issues.append(verification_issue("error", "policy_not_verified", "Template release requires a verified policy.", str(policy_path), "template_policy_verified", policy_verification.get("status")))
    if lock.get("source_sha256") and pack_zip.exists() and pack_zip.is_file() and sha256_file(pack_zip) != str(lock.get("source_sha256", "")):
        issues.append(verification_issue("error", "pack_source_sha256_mismatch", "Template pack zip does not match the lockfile source SHA-256.", str(pack_zip), lock.get("source_sha256"), sha256_file(pack_zip)))
    if lock.get("registry_sha256") and registry_path.exists() and registry_path.is_file() and sha256_file(registry_path) != str(lock.get("registry_sha256", "")):
        issues.append(verification_issue("error", "registry_sha256_mismatch", "Template registry does not match the lockfile registry SHA-256.", str(registry_path), lock.get("registry_sha256"), sha256_file(registry_path)))

    if missing_input:
        manifest = template_release_manifest(Path(), [], lock, policy, pack_verification, attestation_verification, policy_verification, issues)
        return {
            **manifest,
            "release_zip_path": str(out),
            "release_zip_bytes": 0,
            "release_zip_sha256": "",
        }

    with tempfile.TemporaryDirectory(prefix="falsiflow_template_release_") as tmp:
        release_root = Path(tmp) / "release"
        release_root.mkdir(parents=True, exist_ok=True)
        artifacts = [
            copy_template_release_artifact(release_root, pack_zip, "template_pack.zip", "template_pack"),
            copy_template_release_artifact(release_root, registry_path, "template_registry.json", "template_registry"),
            copy_template_release_artifact(release_root, lock_path, "falsiflow_template_lock.json", "template_lock"),
            copy_template_release_artifact(release_root, attestation_path, "falsiflow_template_lock.attestation.json", "template_attestation"),
            copy_template_release_artifact(release_root, policy_path, "falsiflow_template_policy.json", "template_policy"),
        ]
        manifest = template_release_manifest(release_root, artifacts, lock, policy, pack_verification, attestation_verification, policy_verification, issues)
        (release_root / "template_release_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        zip_release_directory(release_root, out)

    return {
        **manifest,
        "release_zip_path": str(out),
        "release_zip_bytes": out.stat().st_size if out.exists() else 0,
        "release_zip_sha256": sha256_file(out) if out.exists() else "",
    }


def relative_release_artifact_path(release_root: Path, raw_path: object, issues: list[dict[str, object]]) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path.strip():
        issues.append(verification_issue("error", "invalid_artifact_path", "Template release artifact path must be a non-empty string."))
        return None
    relative_path = safe_release_zip_member_relative_path(raw_path)
    if relative_path is None:
        issues.append(verification_issue("error", "unsafe_artifact_path", "Template release artifact path must stay inside the release.", raw_path))
        return None
    resolved_root = release_root.resolve()
    resolved_path = (release_root / relative_path).resolve()
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError:
        issues.append(verification_issue("error", "unsafe_artifact_path", "Template release artifact path resolves outside the release.", raw_path))
        return None
    return resolved_path


def extract_template_release_zip(zip_path: Path, extract_root: Path) -> tuple[Path | None, list[dict[str, object]], int, int]:
    issues: list[dict[str, object]] = []
    if not zip_path.exists() or not zip_path.is_file():
        return None, [verification_issue("error", "zip_missing", "Template release zip does not exist.", str(zip_path))], 0, 0
    release_root = extract_root / "release"
    member_count = 0
    extracted_file_count = 0
    seen: set[str] = set()
    try:
        with zipfile.ZipFile(zip_path) as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                member_count += 1
                relative_path = safe_release_zip_member_relative_path(info.filename)
                if relative_path is None:
                    issues.append(verification_issue("error", "unsafe_zip_member", "Zip member path is empty, absolute, or escapes the archive root.", info.filename))
                    continue
                relative_name = relative_path.as_posix()
                if relative_name in seen:
                    issues.append(verification_issue("error", "duplicate_zip_member", "Zip member appears more than once.", relative_name))
                    continue
                seen.add(relative_name)
                target = (release_root / relative_path).resolve()
                resolved_release_root = release_root.resolve()
                try:
                    target.relative_to(resolved_release_root)
                except ValueError:
                    issues.append(verification_issue("error", "unsafe_zip_member", "Zip member resolves outside the extraction root.", info.filename))
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as source, target.open("wb") as dest:
                    shutil.copyfileobj(source, dest)
                extracted_file_count += 1
    except zipfile.BadZipFile as exc:
        issues.append(verification_issue("error", "zip_invalid", f"Template release zip is not readable: {exc}", str(zip_path)))
    return release_root if release_root.exists() else None, issues, member_count, extracted_file_count


def run_verify_template_release(
    release_zip: Path,
    signing_key: str = "",
    extract_dir: Path | None = None,
) -> dict[str, object]:
    release_zip = release_zip.expanduser().resolve()
    temp_dir: tempfile.TemporaryDirectory[str] | None = None
    if extract_dir is None:
        temp_dir = tempfile.TemporaryDirectory(prefix="falsiflow_template_release_verify_")
        extract_root = Path(temp_dir.name)
    else:
        extract_root = extract_dir.expanduser().resolve()
        if extract_root.exists():
            shutil.rmtree(extract_root)
        extract_root.mkdir(parents=True, exist_ok=True)
    try:
        release_root, extraction_issues, member_count, extracted_file_count = extract_template_release_zip(release_zip, extract_root)
        issues = list(extraction_issues)
        manifest: dict[str, object] = {}
        artifact_paths: dict[str, Path] = {}
        artifact_entries: list[dict[str, object]] = []
        manifested_paths: set[str] = {"template_release_manifest.json"}
        missing_artifact_count = 0
        bytes_mismatch_count = 0
        hash_mismatch_count = 0
        duplicate_path_count = 0
        if release_root is None:
            manifest_path = extract_root / "release" / "template_release_manifest.json"
        else:
            manifest_path = release_root / "template_release_manifest.json"
            try:
                manifest = read_json_object(manifest_path, "template release manifest")
            except SystemExit as exc:
                issues.append(verification_issue("error", "manifest_invalid", str(exc), str(manifest_path)))
            if manifest:
                if manifest.get("status") != "template_release_ready":
                    issues.append(verification_issue("error", "manifest_not_ready", "Template release manifest is not ready.", str(manifest_path), "template_release_ready", manifest.get("status")))
                raw_artifacts = manifest.get("artifacts", [])
                if not isinstance(raw_artifacts, list):
                    issues.append(verification_issue("error", "artifacts_invalid", "Template release manifest artifacts must be a list.", str(manifest_path)))
                    raw_artifacts = []
                artifact_entries = [artifact for artifact in raw_artifacts if isinstance(artifact, dict)]
                if len(artifact_entries) != len(raw_artifacts):
                    issues.append(verification_issue("error", "artifact_entry_invalid", "Template release manifest contains a non-object artifact entry.", str(manifest_path)))
                expected_artifact_count = int(manifest.get("artifact_count", 0) or 0)
                if expected_artifact_count != len(artifact_entries):
                    issues.append(verification_issue("error", "artifact_count_mismatch", "Template release manifest artifact_count does not match the artifact list.", str(manifest_path), expected_artifact_count, len(artifact_entries)))
            seen_roles: set[str] = set()
            seen_paths: set[str] = set()
            for artifact in artifact_entries:
                role = str(artifact.get("role", ""))
                if not role:
                    issues.append(verification_issue("error", "artifact_role_missing", "Template release artifact role is missing.", str(manifest_path)))
                elif role in seen_roles:
                    issues.append(verification_issue("error", "duplicate_artifact_role", "Template release artifact role appears more than once.", role))
                else:
                    seen_roles.add(role)
                path = relative_release_artifact_path(release_root, artifact.get("path", ""), issues)
                if path is None:
                    continue
                relative_name = path.relative_to(release_root.resolve()).as_posix()
                if relative_name in seen_paths:
                    duplicate_path_count += 1
                    issues.append(verification_issue("error", "duplicate_artifact_path", "Template release artifact path appears more than once.", relative_name))
                    continue
                seen_paths.add(relative_name)
                manifested_paths.add(relative_name)
                if role and role not in artifact_paths:
                    artifact_paths[role] = path
                if not isinstance(artifact, dict):
                    continue
                if not path.exists() or not path.is_file():
                    missing_artifact_count += 1
                    issues.append(verification_issue("error", "artifact_missing", "Template release artifact is missing.", str(path)))
                    continue
                expected_bytes = int(artifact.get("bytes", 0) or 0)
                expected_sha256 = str(artifact.get("sha256", ""))
                if path.stat().st_size != expected_bytes:
                    bytes_mismatch_count += 1
                    issues.append(verification_issue("error", "artifact_bytes_mismatch", "Template release artifact byte count does not match.", str(path), expected_bytes, path.stat().st_size))
                actual_sha256 = sha256_file(path)
                if actual_sha256 != expected_sha256:
                    hash_mismatch_count += 1
                    issues.append(verification_issue("error", "artifact_sha256_mismatch", "Template release artifact SHA-256 does not match.", str(path), expected_sha256, actual_sha256))
            unmanifested_files = [
                path.resolve().relative_to(release_root.resolve()).as_posix()
                for path in sorted(release_root.rglob("*"))
                if path.is_file() and path.resolve().relative_to(release_root.resolve()).as_posix() not in manifested_paths
            ]
            for path in unmanifested_files:
                issues.append(verification_issue("error", "unmanifested_file", "Template release contains a file not listed in template_release_manifest.json.", path))
        if release_root is None:
            unmanifested_files = []

        pack_zip = artifact_paths.get("template_pack", Path())
        registry_path = artifact_paths.get("template_registry", Path())
        lock_path = artifact_paths.get("template_lock", Path())
        attestation_path = artifact_paths.get("template_attestation", Path())
        policy_path = artifact_paths.get("template_policy", Path())
        artifact_members = {
            str(artifact.get("role", "")): str(artifact.get("path", ""))
            for artifact in artifact_entries
            if str(artifact.get("role", "")).strip() and str(artifact.get("path", "")).strip()
        }
        required_roles = {
            "template_pack": pack_zip,
            "template_registry": registry_path,
            "template_lock": lock_path,
            "template_attestation": attestation_path,
            "template_policy": policy_path,
        }
        for role, path in required_roles.items():
            if not path or not path.exists() or not path.is_file():
                issues.append(verification_issue("error", f"{role}_missing", "Template release is missing a required artifact role.", role))

        lock = read_json_object(lock_path, "template lock") if lock_path.exists() and lock_path.is_file() else {}
        pack_verification = verify_template_pack_zip(pack_zip) if pack_zip.exists() and pack_zip.is_file() else {"status": "template_pack_failed", "issues": []}
        attestation_verification = run_verify_template_attestation(attestation_path, subject_path=lock_path, signing_key=signing_key) if attestation_path.exists() and attestation_path.is_file() and lock_path.exists() and lock_path.is_file() else {"status": "template_attestation_failed", "issues": []}
        policy_verification = run_verify_template_policy(policy_path, lock_path, attestation_path, signing_key=signing_key) if policy_path.exists() and policy_path.is_file() and lock_path.exists() and lock_path.is_file() and attestation_path.exists() and attestation_path.is_file() else {"status": "template_policy_failed", "issues": []}
        if pack_verification.get("status") != "template_pack_verified":
            issues.append(verification_issue("error", "template_pack_not_verified", "Template release pack is not verified.", str(pack_zip), "template_pack_verified", pack_verification.get("status")))
        if attestation_verification.get("status") != "template_attestation_verified":
            issues.append(verification_issue("error", "attestation_not_verified", "Template release attestation is not verified.", str(attestation_path), "template_attestation_verified", attestation_verification.get("status")))
        if policy_verification.get("status") != "template_policy_verified":
            issues.append(verification_issue("error", "policy_not_verified", "Template release policy is not verified.", str(policy_path), "template_policy_verified", policy_verification.get("status")))
        if lock.get("source_sha256") and pack_zip.exists() and pack_zip.is_file() and sha256_file(pack_zip) != str(lock.get("source_sha256", "")):
            issues.append(verification_issue("error", "pack_source_sha256_mismatch", "Template release pack does not match the lockfile source SHA-256.", str(pack_zip), lock.get("source_sha256"), sha256_file(pack_zip)))
        if lock.get("registry_sha256") and registry_path.exists() and registry_path.is_file() and sha256_file(registry_path) != str(lock.get("registry_sha256", "")):
            issues.append(verification_issue("error", "registry_sha256_mismatch", "Template release registry does not match the lockfile registry SHA-256.", str(registry_path), lock.get("registry_sha256"), sha256_file(registry_path)))
        if manifest.get("template_id") and lock.get("template_id") and str(manifest.get("template_id")) != str(lock.get("template_id")):
            issues.append(verification_issue("error", "manifest_template_id_mismatch", "Template release manifest template_id does not match the lockfile.", str(manifest_path), manifest.get("template_id"), lock.get("template_id")))
        lock_version = str(lock.get("template_version") or lock.get("template_project_version", ""))
        if manifest.get("template_version") and lock_version and str(manifest.get("template_version")) != lock_version:
            issues.append(verification_issue("error", "manifest_template_version_mismatch", "Template release manifest template_version does not match the lockfile.", str(manifest_path), manifest.get("template_version"), lock_version))
        if manifest.get("source_sha256") and lock.get("source_sha256") and str(manifest.get("source_sha256")) != str(lock.get("source_sha256")):
            issues.append(verification_issue("error", "manifest_source_sha256_mismatch", "Template release manifest source_sha256 does not match the lockfile.", str(manifest_path), manifest.get("source_sha256"), lock.get("source_sha256")))
        for manifest_key, actual_value in [
            ("pack_verification_status", pack_verification.get("status", "")),
            ("attestation_verification_status", attestation_verification.get("status", "")),
            ("policy_verification_status", policy_verification.get("status", "")),
        ]:
            if manifest.get(manifest_key) and str(manifest.get(manifest_key)) != str(actual_value):
                issues.append(verification_issue("error", f"manifest_{manifest_key}_mismatch", f"Template release manifest `{manifest_key}` does not match re-verification.", str(manifest_path), manifest.get(manifest_key), actual_value))

        error_count = sum(1 for issue in issues if issue.get("severity") == "error")
        return {
            "status": "template_release_verified" if not error_count else "template_release_failed",
            "release_zip_path": str(release_zip),
            "release_zip_bytes": release_zip.stat().st_size if release_zip.exists() else 0,
            "release_zip_sha256": sha256_file(release_zip) if release_zip.exists() else "",
            "release_dir": str(release_root or ""),
            "manifest_path": str(manifest_path),
            "template_id": str(lock.get("template_id", manifest.get("template_id", ""))),
            "template_version": str(lock.get("template_version") or lock.get("template_project_version", manifest.get("template_version", ""))),
            "zip_member_count": member_count,
            "zip_extracted_file_count": extracted_file_count,
            "artifact_count": int(manifest.get("artifact_count", 0) or 0),
            "artifact_members": artifact_members,
            "artifact_paths": {role: str(path) for role, path in required_roles.items()},
            "missing_artifact_count": missing_artifact_count,
            "bytes_mismatch_count": bytes_mismatch_count,
            "hash_mismatch_count": hash_mismatch_count,
            "unsafe_path_count": sum(1 for issue in issues if issue.get("code") in {"unsafe_artifact_path", "unsafe_zip_member"}),
            "duplicate_path_count": duplicate_path_count + sum(1 for issue in issues if issue.get("code") == "duplicate_zip_member"),
            "unmanifested_file_count": len(unmanifested_files),
            "zip_issue_count": sum(1 for issue in extraction_issues if issue.get("severity") == "error"),
            "pack_verification_status": str(pack_verification.get("status", "")),
            "attestation_verification_status": str(attestation_verification.get("status", "")),
            "policy_verification_status": str(policy_verification.get("status", "")),
            "attestation_verification_summary": attestation_verification,
            "policy_verification_summary": policy_verification,
            "issue_count": len(issues),
            "error_count": error_count,
            "warning_count": sum(1 for issue in issues if issue.get("severity") == "warning"),
            "issues": issues,
        }
    finally:
        if temp_dir is not None:
            temp_dir.cleanup()


def render_template_release_verification_report(report: dict[str, object]) -> str:
    lines = [
        "# Falsiflow Template Release Verification",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Template: `{report.get('template_id', '')}@{report.get('template_version', '')}`",
        f"- Release zip SHA-256: `{report.get('release_zip_sha256', '')}`",
        f"- Pack verification: `{report.get('pack_verification_status', '')}`",
        f"- Attestation verification: `{report.get('attestation_verification_status', '')}`",
        f"- Policy verification: `{report.get('policy_verification_status', '')}`",
        f"- Issues: {report.get('issue_count', 0)} errors={report.get('error_count', 0)} warnings={report.get('warning_count', 0)}",
        "",
        "## Review Artifact Index",
        "",
        "| Artifact | Status | Path | Purpose |",
        "| --- | --- | --- | --- |",
    ]
    for artifact in template_release_review_artifact_index(report):
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
        "## Integrity Counters",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
    ])
    for key in [
        "artifact_count",
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
    artifact_paths = report.get("artifact_paths", {})
    lines.extend(["", "## Artifacts", ""])
    if isinstance(artifact_paths, dict) and artifact_paths:
        lines.extend(["| Role | Path |", "| --- | --- |"])
        for role, path in sorted(artifact_paths.items()):
            lines.append(f"| `{markdown_cell(role)}` | {markdown_cell(path)} |")
    else:
        lines.append("No artifact paths found.")
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
