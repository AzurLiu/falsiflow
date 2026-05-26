"""Template attestation and policy helpers."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import hmac
import json
import os
from pathlib import Path

from .template_pack import sha256_file, verification_issue
from .template_registry import read_json_object


def canonical_json_bytes(data: object) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def infer_template_subject_type(subject: dict[str, object], subject_path: Path, requested: str = "") -> str:
    if requested:
        return requested
    status = str(subject.get("status", ""))
    if status in {"template_locked", "template_lock_blocked"} or "registry_sha256" in subject:
        return "template-lock"
    if status in {"template_registry_ready", "template_registry_blocked"} or isinstance(subject.get("templates"), list):
        return "template-registry"
    name = subject_path.name.lower()
    if "lock" in name:
        return "template-lock"
    if "registry" in name:
        return "template-registry"
    raise SystemExit("Could not infer template attestation subject type; pass --subject-type.")


def template_subject_payload(subject_path: Path, subject_type: str = "", builder: str = "") -> tuple[dict[str, object], list[dict[str, object]]]:
    subject_path = subject_path.expanduser().resolve()
    subject = read_json_object(subject_path, "template attestation subject")
    resolved_type = infer_template_subject_type(subject, subject_path, subject_type)
    issues: list[dict[str, object]] = []
    payload: dict[str, object] = {
        "subject_type": resolved_type,
        "subject_path": str(subject_path),
        "subject_bytes": subject_path.stat().st_size if subject_path.exists() and subject_path.is_file() else 0,
        "subject_sha256": sha256_file(subject_path) if subject_path.exists() and subject_path.is_file() else "",
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "builder": builder,
        "generator": "falsiflow template-attest",
    }
    if resolved_type == "template-lock":
        if subject.get("status") != "template_locked":
            issues.append(verification_issue("error", "subject_not_ready", "Template lock subject is not ready.", str(subject_path), "template_locked", subject.get("status")))
        payload.update({
            "template_id": str(subject.get("template_id", "")),
            "template_version": str(subject.get("template_version") or subject.get("template_project_version", "")),
            "registry_sha256": str(subject.get("registry_sha256", "")),
            "source_type": str(subject.get("source_type", "")),
            "source_url": str(subject.get("source_url", "")),
            "source_bytes": int(subject.get("source_bytes", 0) or 0),
            "source_sha256": str(subject.get("source_sha256", "")),
            "pack_verification_status": str(subject.get("pack_verification_status", "")),
        })
    elif resolved_type == "template-registry":
        if subject.get("status") != "template_registry_ready":
            issues.append(verification_issue("error", "subject_not_ready", "Template registry subject is not ready.", str(subject_path), "template_registry_ready", subject.get("status")))
        templates = [
            {
                "template_id": str(entry.get("template_id", "")),
                "template_version": str(entry.get("template_version") or entry.get("template_project_version", "")),
                "source_type": str(entry.get("source_type", "")),
                "source_url": str(entry.get("source_url", "")),
                "source_bytes": int(entry.get("source_bytes", 0) or 0),
                "source_sha256": str(entry.get("source_sha256", "")),
            }
            for entry in subject.get("templates", [])
            if isinstance(entry, dict)
        ]
        payload.update({
            "template_count": int(subject.get("template_count", 0) or 0),
            "verified_template_count": int(subject.get("verified_template_count", 0) or 0),
            "templates": templates,
        })
    else:
        issues.append(verification_issue("error", "unsupported_subject_type", "Unsupported template attestation subject type.", resolved_type))
    return payload, issues


def resolve_attestation_key(signing_key: str = "") -> str:
    return signing_key or os.environ.get("FALSIFLOW_TEMPLATE_ATTESTATION_KEY", "")


def sign_attestation_payload(payload: dict[str, object], signing_key: str) -> str:
    return hmac.new(signing_key.encode("utf-8"), canonical_json_bytes(payload), hashlib.sha256).hexdigest()


def run_template_attestation(
    subject_path: Path,
    subject_type: str = "",
    out: Path | None = None,
    signing_key: str = "",
    key_id: str = "",
    builder: str = "",
) -> dict[str, object]:
    payload, issues = template_subject_payload(subject_path, subject_type=subject_type, builder=builder)
    resolved_key = resolve_attestation_key(signing_key)
    payload_sha256 = sha256_bytes(canonical_json_bytes(payload))
    signature_type = "hmac-sha256" if resolved_key else "unsigned"
    signature = sign_attestation_payload(payload, resolved_key) if resolved_key else ""
    error_count = sum(1 for issue in issues if issue.get("severity") == "error")
    attestation = {
        "status": "template_attested" if not error_count else "template_attestation_blocked",
        "subject_type": str(payload.get("subject_type", "")),
        "subject_path": str(payload.get("subject_path", "")),
        "subject_bytes": int(payload.get("subject_bytes", 0) or 0),
        "subject_sha256": str(payload.get("subject_sha256", "")),
        "payload_sha256": payload_sha256,
        "created_at": str(payload.get("created_at", "")),
        "builder": builder,
        "generator": "falsiflow template-attest",
        "signature_type": signature_type,
        "signature": signature,
        "key_id": key_id,
        "payload": payload,
        "issue_count": len(issues),
        "error_count": error_count,
        "warning_count": sum(1 for issue in issues if issue.get("severity") == "warning"),
        "issues": issues,
    }
    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(attestation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return attestation


def attestation_subject_path(attestation: dict[str, object], attestation_path: Path, override: Path | None = None) -> Path:
    if override is not None:
        return override.expanduser().resolve()
    payload = attestation.get("payload", {})
    raw_path = str(payload.get("subject_path", "") if isinstance(payload, dict) else "").strip()
    if not raw_path:
        raw_path = str(attestation.get("subject_path", "")).strip()
    if not raw_path:
        raise SystemExit("Template attestation does not declare a subject path; pass --subject.")
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = (attestation_path.parent / path).resolve()
    return path


def run_verify_template_attestation(
    attestation_path: Path,
    subject_path: Path | None = None,
    signing_key: str = "",
) -> dict[str, object]:
    attestation_path = attestation_path.expanduser().resolve()
    attestation = read_json_object(attestation_path, "template attestation")
    issues: list[dict[str, object]] = []
    payload = attestation.get("payload")
    if not isinstance(payload, dict):
        payload = {}
        issues.append(verification_issue("error", "payload_missing", "Template attestation payload is missing or invalid.", str(attestation_path)))
    expected_payload_sha256 = str(attestation.get("payload_sha256", ""))
    actual_payload_sha256 = sha256_bytes(canonical_json_bytes(payload))
    if expected_payload_sha256 != actual_payload_sha256:
        issues.append(verification_issue("error", "payload_sha256_mismatch", "Template attestation payload hash does not match.", str(attestation_path), expected_payload_sha256, actual_payload_sha256))

    subject = attestation_subject_path(attestation, attestation_path, override=subject_path)
    if not subject.exists() or not subject.is_file():
        issues.append(verification_issue("error", "subject_missing", "Template attestation subject file does not exist.", str(subject)))
        actual_subject_bytes = 0
        actual_subject_sha256 = ""
    else:
        actual_subject_bytes = subject.stat().st_size
        actual_subject_sha256 = sha256_file(subject)
    expected_subject_bytes = int(payload.get("subject_bytes", attestation.get("subject_bytes", 0)) or 0)
    expected_subject_sha256 = str(payload.get("subject_sha256", attestation.get("subject_sha256", "")))
    if actual_subject_bytes != expected_subject_bytes:
        issues.append(verification_issue("error", "subject_bytes_mismatch", "Template attestation subject byte size does not match.", str(subject), expected_subject_bytes, actual_subject_bytes))
    if actual_subject_sha256 != expected_subject_sha256:
        issues.append(verification_issue("error", "subject_sha256_mismatch", "Template attestation subject SHA-256 does not match.", str(subject), expected_subject_sha256, actual_subject_sha256))

    signature_type = str(attestation.get("signature_type", "unsigned") or "unsigned")
    signature_verified = False
    if signature_type == "hmac-sha256":
        resolved_key = resolve_attestation_key(signing_key)
        if not resolved_key:
            issues.append(verification_issue("warning", "signing_key_missing", "Template attestation has an HMAC signature, but no signing key was provided.", str(attestation_path)))
        else:
            expected_signature = str(attestation.get("signature", ""))
            actual_signature = sign_attestation_payload(payload, resolved_key)
            if hmac.compare_digest(expected_signature, actual_signature):
                signature_verified = True
            else:
                issues.append(verification_issue("error", "signature_mismatch", "Template attestation HMAC signature does not match.", str(attestation_path)))
    elif signature_type == "unsigned":
        issues.append(verification_issue("warning", "attestation_unsigned", "Template attestation is unsigned; provenance is not trusted.", str(attestation_path)))
    else:
        issues.append(verification_issue("error", "unsupported_signature_type", "Template attestation signature type is not supported.", str(attestation_path), "hmac-sha256 or unsigned", signature_type))

    error_count = sum(1 for issue in issues if issue.get("severity") == "error")
    if error_count:
        status = "template_attestation_failed"
    elif signature_verified:
        status = "template_attestation_verified"
    else:
        status = "template_attestation_untrusted"
    return {
        "status": status,
        "attestation_path": str(attestation_path),
        "subject_type": str(payload.get("subject_type", attestation.get("subject_type", ""))),
        "subject_path": str(subject),
        "subject_bytes": actual_subject_bytes,
        "subject_sha256": actual_subject_sha256,
        "payload_sha256": actual_payload_sha256,
        "signature_type": signature_type,
        "signature_verified": signature_verified,
        "key_id": str(attestation.get("key_id", "")),
        "issue_count": len(issues),
        "error_count": error_count,
        "warning_count": sum(1 for issue in issues if issue.get("severity") == "warning"),
        "issues": issues,
    }


def template_policy_expected(lock: dict[str, object], lock_path: Path, attestation_verification: dict[str, object]) -> dict[str, object]:
    return {
        "template_id": str(lock.get("template_id", "")),
        "template_version": str(lock.get("template_version") or lock.get("template_project_version", "")),
        "source_type": str(lock.get("source_type", "")),
        "source_url": str(lock.get("source_url", "")),
        "source_bytes": int(lock.get("source_bytes", 0) or 0),
        "source_sha256": str(lock.get("source_sha256", "")),
        "registry_sha256": str(lock.get("registry_sha256", "")),
        "lock_sha256": sha256_file(lock_path) if lock_path.exists() and lock_path.is_file() else "",
        "attestation_subject_sha256": str(attestation_verification.get("subject_sha256", "")),
        "attestation_payload_sha256": str(attestation_verification.get("payload_sha256", "")),
        "attestation_signature_type": str(attestation_verification.get("signature_type", "")),
        "attestation_key_id": str(attestation_verification.get("key_id", "")),
    }


def run_template_policy(
    lock_path: Path,
    attestation_path: Path,
    out: Path | None = None,
    signing_key: str = "",
    policy_id: str = "",
    owner: str = "",
) -> dict[str, object]:
    lock_path = lock_path.expanduser().resolve()
    attestation_path = attestation_path.expanduser().resolve()
    lock = read_json_object(lock_path, "template lock")
    attestation_verification = run_verify_template_attestation(attestation_path, subject_path=lock_path, signing_key=signing_key)
    issues = [issue for issue in attestation_verification.get("issues", []) if isinstance(issue, dict)]
    if lock.get("status") != "template_locked":
        issues.append(verification_issue("error", "lock_not_ready", "Template policy requires a locked template.", str(lock_path), "template_locked", lock.get("status")))
    if attestation_verification.get("status") != "template_attestation_verified":
        issues.append(verification_issue("error", "attestation_not_verified", "Template policy requires a verified template-lock attestation.", str(attestation_path), "template_attestation_verified", attestation_verification.get("status")))
    expected = template_policy_expected(lock, lock_path, attestation_verification)
    if not expected["attestation_key_id"]:
        issues.append(verification_issue("error", "attestation_key_id_missing", "Template policy requires an attestation key_id.", str(attestation_path)))
    error_count = sum(1 for issue in issues if issue.get("severity") == "error")
    policy = {
        "status": "template_policy_ready" if not error_count else "template_policy_blocked",
        "policy_id": policy_id or f"{expected['template_id']}@{expected['template_version']}",
        "policy_version": "1",
        "owner": owner,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "generator": "falsiflow template-policy",
        "lock_path": str(lock_path),
        "attestation_path": str(attestation_path),
        "template_id": expected["template_id"],
        "template_version": expected["template_version"],
        "require_attestation": True,
        "trusted_key_id": expected["attestation_key_id"],
        "expected": expected,
        "attestation_status": str(attestation_verification.get("status", "")),
        "attestation_signature_verified": bool(attestation_verification.get("signature_verified")),
        "issue_count": len(issues),
        "error_count": error_count,
        "warning_count": sum(1 for issue in issues if issue.get("severity") == "warning"),
        "issues": issues,
    }
    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(policy, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return policy


def run_verify_template_policy(
    policy_path: Path,
    lock_path: Path,
    attestation_path: Path,
    signing_key: str = "",
) -> dict[str, object]:
    policy_path = policy_path.expanduser().resolve()
    lock_path = lock_path.expanduser().resolve()
    attestation_path = attestation_path.expanduser().resolve()
    policy = read_json_object(policy_path, "template policy")
    lock = read_json_object(lock_path, "template lock")
    attestation_verification = run_verify_template_attestation(attestation_path, subject_path=lock_path, signing_key=signing_key)
    issues = [issue for issue in attestation_verification.get("issues", []) if isinstance(issue, dict)]
    if policy.get("status") != "template_policy_ready":
        issues.append(verification_issue("error", "policy_not_ready", "Template policy is not ready.", str(policy_path), "template_policy_ready", policy.get("status")))
    if lock.get("status") != "template_locked":
        issues.append(verification_issue("error", "lock_not_ready", "Template policy verification requires a locked template.", str(lock_path), "template_locked", lock.get("status")))
    if attestation_verification.get("status") != "template_attestation_verified":
        issues.append(verification_issue("error", "attestation_not_verified", "Template policy verification requires template_attestation_verified.", str(attestation_path), "template_attestation_verified", attestation_verification.get("status")))

    expected = policy.get("expected", {}) if isinstance(policy.get("expected"), dict) else {}
    actual = template_policy_expected(lock, lock_path, attestation_verification)
    for key, actual_value in actual.items():
        if expected.get(key) != actual_value:
            issues.append(verification_issue("error", f"policy_{key}_mismatch", f"Template policy expected `{key}` does not match.", str(policy_path), expected.get(key), actual_value))
    trusted_key_id = str(policy.get("trusted_key_id", ""))
    if trusted_key_id and trusted_key_id != str(actual.get("attestation_key_id", "")):
        issues.append(verification_issue("error", "policy_trusted_key_id_mismatch", "Template policy trusted_key_id does not match the attestation key_id.", str(policy_path), trusted_key_id, actual.get("attestation_key_id", "")))
    if bool(policy.get("require_attestation", True)) and attestation_verification.get("status") != "template_attestation_verified":
        issues.append(verification_issue("error", "policy_attestation_required", "Template policy requires a verified attestation.", str(policy_path)))

    error_count = sum(1 for issue in issues if issue.get("severity") == "error")
    return {
        "status": "template_policy_verified" if not error_count else "template_policy_failed",
        "policy_path": str(policy_path),
        "policy_id": str(policy.get("policy_id", "")),
        "lock_path": str(lock_path),
        "attestation_path": str(attestation_path),
        "template_id": str(actual.get("template_id", "")),
        "template_version": str(actual.get("template_version", "")),
        "trusted_key_id": trusted_key_id,
        "attestation_status": str(attestation_verification.get("status", "")),
        "attestation_signature_verified": bool(attestation_verification.get("signature_verified")),
        "expected": expected,
        "actual": actual,
        "issue_count": len(issues),
        "error_count": error_count,
        "warning_count": sum(1 for issue in issues if issue.get("severity") == "warning"),
        "issues": issues,
    }
