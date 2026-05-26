"""Template installation helpers."""

from __future__ import annotations

from collections.abc import Callable
import json
from pathlib import Path
import shutil
import tempfile

from .template_pack import (
    extract_template_pack_zip,
    merge_template_pack_verification_issues,
    sha256_file,
    template_pack_failure_report,
    verification_issue,
    verify_template_pack,
)
from .template_registry import locked_template_zip, read_json_object, safe_template_identifier

TemplateCheckRunner = Callable[[Path, Path, bool], dict[str, object]]


def count_files(path: Path) -> int:
    return sum(1 for item in path.rglob("*") if item.is_file()) if path.exists() else 0


def template_install_index_path(templates_dir: Path) -> Path:
    return templates_dir / "falsiflow_template_index.json"


def write_template_install_index(templates_dir: Path, record: dict[str, object]) -> dict[str, object]:
    index_path = template_install_index_path(templates_dir)
    existing_templates: list[dict[str, object]] = []
    if index_path.exists():
        try:
            loaded = json.loads(index_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict) and isinstance(loaded.get("templates"), list):
                existing_templates = [item for item in loaded["templates"] if isinstance(item, dict)]
        except json.JSONDecodeError:
            existing_templates = []
    template_id = str(record.get("template_id", ""))
    templates = [item for item in existing_templates if str(item.get("template_id", "")) != template_id]
    templates.append(record)
    templates = sorted(templates, key=lambda item: str(item.get("template_id", "")))
    index = {
        "status": "template_index_ready",
        "template_count": len(templates),
        "templates": templates,
    }
    index_path.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return index


def template_install_attestation_fields(attestation_verification: dict[str, object] | None, attestation_required: bool) -> dict[str, object]:
    if not attestation_verification:
        return {
            "attestation_required": attestation_required,
            "attestation_path": "",
            "attestation_status": "not_checked",
            "attestation_subject_type": "",
            "attestation_subject_sha256": "",
            "attestation_signature_verified": False,
            "attestation_key_id": "",
            "attestation_issue_count": 0,
        }
    return {
        "attestation_required": attestation_required,
        "attestation_path": str(attestation_verification.get("attestation_path", "")),
        "attestation_status": str(attestation_verification.get("status", "")),
        "attestation_subject_type": str(attestation_verification.get("subject_type", "")),
        "attestation_subject_sha256": str(attestation_verification.get("subject_sha256", "")),
        "attestation_signature_verified": bool(attestation_verification.get("signature_verified")),
        "attestation_key_id": str(attestation_verification.get("key_id", "")),
        "attestation_issue_count": int(attestation_verification.get("issue_count", 0) or 0),
    }


def template_install_policy_fields(policy_verification: dict[str, object] | None) -> dict[str, object]:
    if not policy_verification:
        return {
            "policy_path": "",
            "policy_status": "not_checked",
            "policy_id": "",
            "policy_trusted_key_id": "",
            "policy_issue_count": 0,
        }
    return {
        "policy_path": str(policy_verification.get("policy_path", "")),
        "policy_status": str(policy_verification.get("status", "")),
        "policy_id": str(policy_verification.get("policy_id", "")),
        "policy_trusted_key_id": str(policy_verification.get("trusted_key_id", "")),
        "policy_issue_count": int(policy_verification.get("issue_count", 0) or 0),
    }


def template_install_blocked_summary(
    zip_path: Path,
    templates_dir: Path,
    install_dir: Path | None,
    verification: dict[str, object],
    issues: list[dict[str, object]],
    template_id: str = "",
    attestation_verification: dict[str, object] | None = None,
    attestation_required: bool = False,
    policy_verification: dict[str, object] | None = None,
) -> dict[str, object]:
    error_count = sum(1 for issue in issues if issue.get("severity") == "error")
    attestation_fields = template_install_attestation_fields(attestation_verification, attestation_required)
    policy_fields = template_install_policy_fields(policy_verification)
    return {
        "status": "template_install_blocked",
        "template_id": template_id or str(verification.get("template_id", "")),
        "input_path": str(zip_path),
        "templates_dir": str(templates_dir),
        "install_dir": str(install_dir or ""),
        "registry_path": str(template_install_index_path(templates_dir)),
        "verification_status": str(verification.get("status", "")),
        "integrity_status": str(verification.get("integrity_status", "")),
        "template_check_status": "",
        "template_check_failure_count": 0,
        "artifact_count": int(verification.get("artifact_count", 0) or 0),
        "installed_file_count": 0,
        "registry_template_count": 0,
        **attestation_fields,
        **policy_fields,
        "issue_count": len(issues),
        "error_count": error_count,
        "warning_count": sum(1 for issue in issues if issue.get("severity") == "warning"),
        "issues": issues,
    }


def template_install_attestation_issues(attestation_verification: dict[str, object] | None, attestation_required: bool) -> list[dict[str, object]]:
    if attestation_verification is None:
        if not attestation_required:
            return []
        return [verification_issue("error", "attestation_required_missing", "Template install requires a verified template-lock attestation.", "template-install")]
    issues = [issue for issue in attestation_verification.get("issues", []) if isinstance(issue, dict)]
    status = str(attestation_verification.get("status", ""))
    subject_type = str(attestation_verification.get("subject_type", ""))
    if subject_type and subject_type != "template-lock":
        issues.append(verification_issue("error", "attestation_subject_type_mismatch", "Template install attestations must verify a template-lock subject.", str(attestation_verification.get("attestation_path", "")), "template-lock", subject_type))
    if status == "template_attestation_failed" and not any(issue.get("severity") == "error" for issue in issues):
        issues.append(verification_issue("error", "attestation_verification_failed", "Template attestation verification failed.", str(attestation_verification.get("attestation_path", ""))))
    if status not in {"template_attestation_verified", "template_attestation_untrusted", "template_attestation_failed"}:
        issues.append(verification_issue("error", "attestation_status_unknown", "Template attestation verification status is not recognized.", str(attestation_verification.get("attestation_path", "")), "template_attestation_verified", status))
    if attestation_required and status != "template_attestation_verified":
        issues.append(verification_issue("error", "attestation_not_verified", "Template install requires template_attestation_verified.", str(attestation_verification.get("attestation_path", "")), "template_attestation_verified", status))
    return issues


def template_install_policy_issues(policy_verification: dict[str, object] | None) -> list[dict[str, object]]:
    if policy_verification is None:
        return []
    issues = [issue for issue in policy_verification.get("issues", []) if isinstance(issue, dict)]
    if policy_verification.get("status") != "template_policy_verified":
        issues.append(verification_issue("error", "policy_not_verified", "Template install requires template_policy_verified.", str(policy_verification.get("policy_path", "")), "template_policy_verified", policy_verification.get("status")))
    return issues


def template_install_preflight_blocked_summary(
    input_path: Path,
    templates_dir: Path,
    issues: list[dict[str, object]],
    template_id: str = "",
    attestation_verification: dict[str, object] | None = None,
    attestation_required: bool = False,
    policy_verification: dict[str, object] | None = None,
) -> dict[str, object]:
    verification = {
        "status": "",
        "integrity_status": "",
        "artifact_count": 0,
        "issues": [],
    }
    return template_install_blocked_summary(
        input_path,
        templates_dir.expanduser().resolve(),
        None,
        verification,
        issues,
        template_id=template_id,
        attestation_verification=attestation_verification,
        attestation_required=attestation_required,
        policy_verification=policy_verification,
    )


def run_template_install(
    zip_path: Path,
    templates_dir: Path,
    check_out_dir: Path | None = None,
    force: bool = False,
    attestation_verification: dict[str, object] | None = None,
    attestation_required: bool = False,
    policy_verification: dict[str, object] | None = None,
    template_check_runner: TemplateCheckRunner | None = None,
) -> dict[str, object]:
    if template_check_runner is None:
        raise SystemExit("Template install requires a template_check_runner.")
    templates_dir = templates_dir.expanduser().resolve()
    zip_path = zip_path.expanduser().resolve()
    attestation_issues = template_install_attestation_issues(attestation_verification, attestation_required)
    policy_issues = template_install_policy_issues(policy_verification)
    preflight_issues = [*attestation_issues, *policy_issues]
    if any(issue.get("severity") == "error" for issue in preflight_issues):
        return template_install_blocked_summary(
            zip_path,
            templates_dir,
            None,
            {"status": "", "integrity_status": "", "artifact_count": 0, "issues": []},
            preflight_issues,
            attestation_verification=attestation_verification,
            attestation_required=attestation_required,
            policy_verification=policy_verification,
        )
    with tempfile.TemporaryDirectory(prefix="falsiflow_template_install_") as tmp:
        extract_root = Path(tmp) / "template_pack"
        pack_root, extraction_issues, member_count, extracted_file_count = extract_template_pack_zip(zip_path, extract_root)
        if pack_root is None:
            verification = template_pack_failure_report(zip_path, "zip", extraction_issues, zip_path)
            return template_install_blocked_summary(zip_path, templates_dir, None, verification, extraction_issues, attestation_verification=attestation_verification, attestation_required=attestation_required, policy_verification=policy_verification)

        verification = verify_template_pack(pack_root, input_path=zip_path, input_format="zip")
        verification["pack_dir"] = str(zip_path)
        verification["zip_path"] = str(zip_path)
        verification["zip_member_count"] = member_count
        verification["zip_extracted_file_count"] = extracted_file_count
        verification["zip_pack_root"] = pack_root.relative_to(extract_root).as_posix() if pack_root != extract_root else "."
        verification["manifest_path"] = f"{zip_path}:{Path(verification['manifest_path']).relative_to(pack_root).as_posix()}" if (pack_root / "template_pack_manifest.json").exists() else f"{zip_path}:template_pack_manifest.json"
        verification = merge_template_pack_verification_issues(verification, extraction_issues)
        if verification.get("status") != "template_pack_verified":
            return template_install_blocked_summary(zip_path, templates_dir, None, verification, list(verification.get("issues", [])), attestation_verification=attestation_verification, attestation_required=attestation_required, policy_verification=policy_verification)

        source_template_dir = pack_root / "template"
        local_issues: list[dict[str, object]] = []
        if not source_template_dir.exists() or not source_template_dir.is_dir():
            local_issues.append(verification_issue("error", "template_dir_missing", "Verified template pack does not contain template/.", "template"))

        template_id = str(verification.get("template_id", "")).strip()
        if not safe_template_identifier(template_id):
            local_issues.append(verification_issue("error", "unsafe_template_id", "Template id must be a safe path segment.", "template_pack_manifest.json", "safe template id", template_id))
        install_dir = templates_dir / template_id if template_id else None
        if install_dir is not None:
            resolved_install = install_dir.resolve()
            try:
                resolved_install.relative_to(templates_dir)
            except ValueError:
                local_issues.append(verification_issue("error", "install_dir_escape", "Resolved install directory escapes templates_dir.", str(install_dir)))
        if local_issues:
            return template_install_blocked_summary(zip_path, templates_dir, install_dir, verification, [*list(verification.get("issues", [])), *local_issues, *attestation_issues, *policy_issues], template_id, attestation_verification=attestation_verification, attestation_required=attestation_required, policy_verification=policy_verification)

        assert install_dir is not None
        if templates_dir.exists() and not templates_dir.is_dir():
            raise SystemExit(f"Refusing to install templates into non-directory path: {templates_dir}")
        if install_dir.exists() and not install_dir.is_dir():
            raise SystemExit(f"Refusing to overwrite non-directory installed template path: {install_dir}")
        if install_dir.exists() and any(install_dir.iterdir()) and not force:
            raise SystemExit(f"Refusing to overwrite installed template without --force: {install_dir}")

        templates_dir.mkdir(parents=True, exist_ok=True)
        staging_dir = templates_dir / f".{template_id}.installing"
        if staging_dir.exists():
            shutil.rmtree(staging_dir)
        shutil.copytree(source_template_dir, staging_dir)
        if install_dir.exists():
            shutil.rmtree(install_dir)
        shutil.move(str(staging_dir), str(install_dir))

        check_dir = check_out_dir or (templates_dir / ".falsiflow_template_checks" / template_id)
        template_check = template_check_runner(install_dir, check_dir, True)
        if template_check.get("status") != "template_ready":
            shutil.rmtree(install_dir)
            install_issue = verification_issue("error", "installed_template_check_blocked", "Installed template did not pass template-check.", str(check_dir), "template_ready", template_check.get("status"))
            return template_install_blocked_summary(zip_path, templates_dir, install_dir, verification, [*list(verification.get("issues", [])), install_issue, *attestation_issues, *policy_issues], template_id, attestation_verification=attestation_verification, attestation_required=attestation_required, policy_verification=policy_verification)

        template_manifest_path = install_dir / "template.json"
        template_manifest = json.loads(template_manifest_path.read_text(encoding="utf-8")) if template_manifest_path.exists() else {}
        attestation_fields = template_install_attestation_fields(attestation_verification, attestation_required)
        policy_fields = template_install_policy_fields(policy_verification)
        summary_issues = [*list(verification.get("issues", [])), *attestation_issues, *policy_issues]
        record = {
            "template_id": template_id,
            "template_name": str(template_manifest.get("name", "")) if isinstance(template_manifest, dict) else "",
            "template_domain": str(template_manifest.get("domain", "")) if isinstance(template_manifest, dict) else "",
            "template_dir": str(install_dir),
            "source_zip": str(zip_path),
            "source_sha256": sha256_file(zip_path),
            "pack_verification_status": str(verification.get("status", "")),
            "template_check_status": str(template_check.get("status", "")),
            **attestation_fields,
            **policy_fields,
            "artifact_count": int(verification.get("artifact_count", 0) or 0),
            "installed_file_count": count_files(install_dir),
        }
        index = write_template_install_index(templates_dir, record)
        return {
            "status": "template_installed",
            "template_id": template_id,
            "template_name": record["template_name"],
            "template_domain": record["template_domain"],
            "input_path": str(zip_path),
            "templates_dir": str(templates_dir),
            "install_dir": str(install_dir),
            "registry_path": str(template_install_index_path(templates_dir)),
            "verification_status": str(verification.get("status", "")),
            "integrity_status": str(verification.get("integrity_status", "")),
            "template_check_status": str(template_check.get("status", "")),
            "template_check_failure_count": int(template_check.get("failure_count", 0) or 0),
            "artifact_count": int(verification.get("artifact_count", 0) or 0),
            "installed_file_count": count_files(install_dir),
            "registry_template_count": int(index.get("template_count", 0) or 0),
            **attestation_fields,
            **policy_fields,
            "issue_count": len(summary_issues),
            "error_count": sum(1 for issue in summary_issues if issue.get("severity") == "error"),
            "warning_count": sum(1 for issue in summary_issues if issue.get("severity") == "warning"),
            "issues": summary_issues,
        }


def run_template_install_workflow(
    zip_path: Path | None,
    templates_dir: Path,
    *,
    lock_path: Path | None = None,
    release_path: Path | None = None,
    check_out_dir: Path | None = None,
    cache_dir: Path | None = None,
    attestation_path: Path | None = None,
    signing_key: str = "",
    policy_path: Path | None = None,
    require_attestation: bool = False,
    force: bool = False,
    template_check_runner: TemplateCheckRunner | None = None,
    release_verifier: Callable[..., dict[str, object]] | None = None,
    attestation_verifier: Callable[..., dict[str, object]] | None = None,
    policy_verifier: Callable[..., dict[str, object]] | None = None,
) -> dict[str, object]:
    lock: dict[str, object] | None = None
    attestation_verification: dict[str, object] | None = None
    policy_verification: dict[str, object] | None = None

    if release_path is not None:
        if attestation_path is not None or policy_path is not None:
            raise SystemExit("--release includes its own attestation and policy; do not pass --attestation or --policy.")
        if release_verifier is None:
            raise SystemExit("Template install from --release requires a release verifier.")
        with tempfile.TemporaryDirectory(prefix="falsiflow_template_release_install_") as tmp:
            release_verification = release_verifier(
                release_path,
                signing_key=signing_key,
                extract_dir=Path(tmp) / "release_extract",
            )
            release_issues = [issue for issue in release_verification.get("issues", []) if isinstance(issue, dict)]
            artifact_paths = release_verification.get("artifact_paths", {}) if isinstance(release_verification.get("artifact_paths"), dict) else {}
            lock_path = Path(str(artifact_paths.get("template_lock", "")))
            zip_path = Path(str(artifact_paths.get("template_pack", "")))
            lock_preview = read_json_object(lock_path, "template lock") if lock_path.exists() else {}
            attestation_verification = release_verification.get("attestation_verification_summary") if isinstance(release_verification.get("attestation_verification_summary"), dict) else None
            policy_verification = release_verification.get("policy_verification_summary") if isinstance(release_verification.get("policy_verification_summary"), dict) else None
            if release_verification.get("status") != "template_release_verified":
                summary = template_install_preflight_blocked_summary(
                    release_path,
                    templates_dir,
                    release_issues,
                    template_id=str(release_verification.get("template_id", "")),
                    attestation_verification=attestation_verification,
                    attestation_required=True,
                    policy_verification=policy_verification,
                )
                summary["release_path"] = str(release_path)
                summary["release_status"] = str(release_verification.get("status", ""))
                summary["release_sha256"] = str(release_verification.get("release_zip_sha256", ""))
                summary["lock_path"] = str(lock_path)
                summary["lock_status"] = str(lock_preview.get("status", ""))
                summary["lock_source_sha256"] = str(lock_preview.get("source_sha256", ""))
                return summary
            lock = lock_preview
            summary = run_template_install(
                zip_path,
                templates_dir,
                check_out_dir=check_out_dir,
                force=force,
                attestation_verification=attestation_verification,
                attestation_required=True,
                policy_verification=policy_verification,
                template_check_runner=template_check_runner,
            )
            summary["release_path"] = str(release_path)
            summary["release_status"] = str(release_verification.get("status", ""))
            summary["release_sha256"] = str(release_verification.get("release_zip_sha256", ""))
            summary["lock_path"] = str(lock_path)
            summary["lock_status"] = str(lock.get("status", "")) if lock else ""
            summary["lock_source_sha256"] = str(lock.get("source_sha256", "")) if lock else ""
            return summary

    if attestation_path is not None and lock_path is None:
        raise SystemExit("--attestation can only be used with --lock.")
    if require_attestation and lock_path is None:
        raise SystemExit("--require-attestation requires --lock.")
    if policy_path is not None and lock_path is None:
        raise SystemExit("--policy requires --lock.")
    if policy_path is not None and attestation_path is None:
        raise SystemExit("--policy requires --attestation.")
    if zip_path is None and lock_path is None:
        raise SystemExit("Template install requires --zip, --lock, or --release.")

    effective_attestation_required = bool(require_attestation or policy_path is not None)
    if lock_path is not None:
        lock_preview = read_json_object(lock_path.expanduser().resolve(), "template lock")
        if attestation_path is not None:
            if attestation_verifier is None:
                raise SystemExit("Template install from --lock with --attestation requires an attestation verifier.")
            attestation_verification = attestation_verifier(
                attestation_path,
                subject_path=lock_path,
                signing_key=signing_key,
            )
        if policy_path is not None:
            if policy_verifier is None:
                raise SystemExit("Template install from --lock with --policy requires a policy verifier.")
            policy_verification = policy_verifier(
                policy_path,
                lock_path,
                attestation_path,
                signing_key=signing_key,
            )
        attestation_issues = template_install_attestation_issues(attestation_verification, effective_attestation_required)
        policy_issues = template_install_policy_issues(policy_verification)
        preflight_issues = [*attestation_issues, *policy_issues]
        if any(issue.get("severity") == "error" for issue in preflight_issues):
            summary = template_install_preflight_blocked_summary(
                lock_path,
                templates_dir,
                preflight_issues,
                template_id=str(lock_preview.get("template_id", "")),
                attestation_verification=attestation_verification,
                attestation_required=effective_attestation_required,
                policy_verification=policy_verification,
            )
            summary["lock_path"] = str(lock_path)
            summary["lock_status"] = str(lock_preview.get("status", ""))
            summary["lock_source_sha256"] = str(lock_preview.get("source_sha256", ""))
            return summary
        zip_path, lock = locked_template_zip(lock_path, cache_dir=cache_dir)

    assert zip_path is not None
    summary = run_template_install(
        zip_path,
        templates_dir,
        check_out_dir=check_out_dir,
        force=force,
        attestation_verification=attestation_verification,
        attestation_required=effective_attestation_required,
        policy_verification=policy_verification,
        template_check_runner=template_check_runner,
    )
    if lock_path is not None:
        summary["lock_path"] = str(lock_path)
        summary["lock_status"] = str(lock.get("status", "")) if lock else ""
        summary["lock_source_sha256"] = str(lock.get("source_sha256", "")) if lock else ""
        if lock and summary.get("template_id") != lock.get("template_id"):
            summary["status"] = "template_install_blocked"
            summary["issues"] = [
                *list(summary.get("issues", [])),
                verification_issue("error", "lock_template_mismatch", "Installed template id does not match the lockfile.", str(lock_path), lock.get("template_id"), summary.get("template_id")),
            ]
            summary["issue_count"] = len(summary["issues"])
            summary["error_count"] = int(summary.get("error_count", 0) or 0) + 1
    return summary
