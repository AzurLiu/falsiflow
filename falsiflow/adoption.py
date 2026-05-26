"""Adoption-readiness gates and reports for Falsiflow."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from .bundle import markdown_cell
from .release import failure_record, release_check_item

ROOT = Path(__file__).resolve().parents[1]


class PackageChecksRunner(Protocol):
    def __call__(self, root: Path) -> dict[str, object]: ...


class DistChecksRunner(Protocol):
    def __call__(self, root: Path, artifact_root: Path, run_dist: bool = True) -> dict[str, object]: ...


class TemplateGalleryRunner(Protocol):
    def __call__(
        self,
        extra_roots: list[Path] | None = None,
        include_env: bool = True,
        out: Path | None = None,
        json_out: Path | None = None,
    ) -> dict[str, object]: ...


class CasebookCheckRunner(Protocol):
    def __call__(
        self,
        artifact_root: Path,
        extra_roots: list[Path] | None = None,
        force: bool = False,
        include_env: bool = True,
    ) -> dict[str, object]: ...


class QuickstartRunner(Protocol):
    def __call__(
        self,
        template: str,
        out_dir: Path,
        template_roots: list[Path] | None = None,
        force: bool = False,
        include_env: bool = True,
    ) -> dict[str, object]: ...


class DoctorRunner(Protocol):
    def __call__(self, project_dir: Path | None, config: Path, evidence: Path, out_dir: Path, force: bool = False) -> dict[str, object]: ...


class ClaimCheckRunner(Protocol):
    def __call__(self, config: Path, evidence: Path, out_dir: Path, force: bool = False) -> dict[str, object]: ...


class TemplateResolver(Protocol):
    def __call__(self, template: str, extra_roots: list[Path] | None = None, include_env: bool = True) -> Path | None: ...


class DefaultEvidencePath(Protocol):
    def __call__(self, project_dir: Path) -> Path: ...


def adoption_priority(
    priority_id: str,
    title: str,
    checks: list[dict[str, str]],
    next_actions: list[str],
) -> dict[str, object]:
    passed = sum(1 for check in checks if check.get("status") == "passed")
    failed_checks = [str(check.get("check", "")) for check in checks if check.get("status") != "passed"]
    return {
        "priority_id": priority_id,
        "title": title,
        "status": "priority_ready" if passed == len(checks) else "priority_blocked",
        "check_count": len(checks),
        "passed_check_count": passed,
        "checks": checks,
        "next_actions": next_actions if failed_checks else [],
        "failed_checks": failed_checks,
    }

def package_check_lookup(package: dict[str, object]) -> dict[str, dict[str, object]]:
    return {
        str(check.get("check", "")): check
        for check in package.get("checks", [])
        if isinstance(check, dict) and check.get("check")
    }

def package_check_item(
    package_checks: dict[str, dict[str, object]],
    check_id: str,
    *,
    installed_mode: bool,
    installed_ok: bool = False,
) -> dict[str, str]:
    check = package_checks.get(check_id)
    if check is not None:
        return release_check_item(
            check_id,
            check.get("status") == "passed",
            str(check.get("message", "")),
            str(check.get("path", "")),
        )
    if installed_mode and installed_ok:
        return release_check_item(
            check_id,
            True,
            "Source documentation gate is covered by source release-check; installed package mode verifies runtime metadata and bundled templates.",
            ROOT,
        )
    return release_check_item(check_id, False, f"Package check `{check_id}` was not run.", ROOT)

def package_check_any_item(
    package_checks: dict[str, dict[str, object]],
    check_id: str,
    aliases: list[str],
    *,
    installed_mode: bool,
    installed_ok: bool = False,
) -> dict[str, str]:
    for alias in aliases:
        check = package_checks.get(alias)
        if check is not None:
            return release_check_item(
                check_id,
                check.get("status") == "passed",
                str(check.get("message", "")),
                str(check.get("path", "")),
            )
    if installed_mode and installed_ok:
        return release_check_item(
            check_id,
            True,
            "Source-tree package gate is covered before packaging; installed package mode verifies the nearest runtime equivalent.",
            ROOT,
        )
    return release_check_item(check_id, False, f"None of `{', '.join(aliases)}` ran.", ROOT)

def dist_check_item(
    dist_checks: dict[str, dict[str, object]],
    check_id: str,
    *,
    dist_status: str,
    dist_root: Path,
    skipped_ok: bool = False,
) -> dict[str, str]:
    check = dist_checks.get(check_id)
    if check is not None:
        return release_check_item(
            check_id,
            check.get("status") == "passed",
            str(check.get("message", "")),
            str(check.get("path", "")),
        )
    if skipped_ok and dist_status == "dist_skipped":
        return release_check_item(
            check_id,
            True,
            "Distribution hygiene is verified by full release-check; this fast or installed-package run skipped distribution checks.",
            dist_root,
        )
    return release_check_item(check_id, False, f"Distribution check `{check_id}` was not run.", dist_root)

def command_list_contains(commands: object, token: str) -> bool:
    return isinstance(commands, list) and any(token in str(command) for command in commands)

def release_validation_status_for_dist(dist_status: str) -> tuple[str, str]:
    if dist_status == "dist_ready":
        return "release_validation_ready", "Wheel, sdist, isolated install, and installed-package release checks completed."
    if dist_status == "dist_skipped":
        return "release_validation_skipped", "Distribution validation was skipped; run adoption-check or release-check without --skip-dist before treating the tree as publish-ready."
    return "release_validation_blocked", f"Distribution validation ended as {dist_status or 'unknown'}."

def adoption_release_validation_status(dist_status: str) -> tuple[str, str]:
    return release_validation_status_for_dist(dist_status)

def adoption_repair_checklist(
    priorities: list[dict[str, object]],
    artifact_root: Path,
    dist_status: str,
    adoption_rerun_root: Path | None = None,
) -> list[dict[str, object]]:
    blocked = [priority for priority in priorities if priority.get("status") != "priority_ready"]
    skip_dist_flag = " --skip-dist" if dist_status == "dist_skipped" else ""
    rerun_root = adoption_rerun_root or artifact_root

    def checklist_item(
        rank: int,
        priority: dict[str, object],
        action_id: str,
        why: str,
        command: str,
        expected_artifact: Path,
        success_signal: str,
    ) -> dict[str, object]:
        failed_checks = priority.get("failed_checks", [])
        return {
            "rank": rank,
            "priority_id": str(priority.get("priority_id", "")),
            "action_id": action_id,
            "failed_checks": [str(check) for check in failed_checks] if isinstance(failed_checks, list) else [],
            "why": why,
            "command": command,
            "expected_artifact": str(expected_artifact),
            "success_signal": success_signal,
        }

    if not blocked:
        return [{
            "rank": 1,
            "priority_id": "all_priorities",
            "action_id": "verify_adoption_ready",
            "failed_checks": [],
            "why": "All adoption priorities are ready; rerun this gate before release or after changing docs, templates, packaging, quickstart, doctor, or claim-check behavior.",
            "command": f"falsiflow adoption-check --out-dir {rerun_root}{skip_dist_flag} --force",
            "expected_artifact": str(rerun_root / "adoption_check.json"),
            "success_signal": "adoption_check.json reports adoption_ready with ready_priority_count equal to priority_count.",
        }]

    checklist: list[dict[str, object]] = []
    for index, priority in enumerate(blocked, start=1):
        priority_id = str(priority.get("priority_id", ""))
        if priority_id == "open_source_entry_point":
            checklist.append(checklist_item(
                index,
                priority,
                "repair_open_source_entry_point",
                "Repair README, examples, quickstart, or handoff checks until first-run users can start from one clear path.",
                f"falsiflow quickstart --template biointerface_coatings --out {artifact_root / 'quickstart_project'} --strict --force",
                artifact_root / "quickstart_project" / "quickstart_summary.json",
                "Quickstart reports quickstart_ready and next_commands starts with falsiflow doctor --project-dir.",
            ))
        elif priority_id == "trusted_audit_experience":
            checklist.append(checklist_item(
                index,
                priority,
                "repair_trusted_audit_experience",
                "Repair claim-check, doctor, audit-review, source, bundle, or verification blockers before treating claims as reviewable.",
                f"falsiflow doctor --project-dir {artifact_root / 'quickstart_project'} --out-dir {artifact_root / 'doctor'} --strict --force",
                artifact_root / "doctor" / "doctor_summary.json",
                "Doctor reports doctor_ready and its repair_checklist points to a claim-check artifact.",
            ))
        elif priority_id == "generality_proof":
            checklist.append(checklist_item(
                index,
                priority,
                "repair_generality_proof",
                "Repair starter templates or template-gallery coverage until Falsiflow visibly spans non-neural workflows.",
                f"falsiflow template-gallery --out {artifact_root / 'template_gallery.md'} --json-out {artifact_root / 'template_gallery.json'}",
                artifact_root / "template_gallery.json",
                "Template gallery reports template_gallery_ready with at least three non-neural templates and doctor handoffs.",
            ))
        elif priority_id == "release_and_distribution":
            checklist.append(checklist_item(
                index,
                priority,
                "repair_release_and_distribution",
                "Repair package metadata, distribution artifacts, or release docs before publishing.",
                f"falsiflow release-check --out-dir {artifact_root / 'release_check'} --force",
                artifact_root / "release_check" / "release_check.json",
                "Release check reports release_ready, package_ready, dist_ready, and adoption_check_status adoption_ready.",
            ))
        else:
            checklist.append(checklist_item(
                index,
                priority,
                "repair_user_experience_convergence",
                "Repair priority docs, adoption-check docs, quickstart handoff, doctor checklist, or claim-check next actions.",
                f"falsiflow adoption-check --out-dir {rerun_root}{skip_dist_flag} --force",
                rerun_root / "adoption_check.md",
                "Adoption report includes Falsiflow Adoption Check, Repair Checklist, and adoption_ready.",
            ))
    return checklist

def render_adoption_check_report(summary: dict[str, object]) -> str:
    lines = [
        "# Falsiflow Adoption Check",
        "",
        f"- Status: `{summary.get('status', '')}`",
        f"- Priorities: {summary.get('ready_priority_count', 0)}/{summary.get('priority_count', 0)}",
        f"- Readiness: {summary.get('readiness_pct', 0)}%",
        f"- Release validation: `{summary.get('release_validation_status', '')}`",
        f"- Release validation note: {markdown_cell(summary.get('release_validation_message', ''))}",
        f"- Casebook check: `{summary.get('casebook_check_status', '')}`",
        f"- Failures: {summary.get('failure_count', 0)}",
        "",
        "## Priorities",
        "",
        "| Priority | Status | Checks |",
        "| --- | --- | ---: |",
    ]
    for priority in summary.get("priorities", []):
        if not isinstance(priority, dict):
            continue
        lines.append(
            "| "
            + " | ".join([
                markdown_cell(priority.get("title", "")),
                markdown_cell(priority.get("status", "")),
                f"{priority.get('passed_check_count', 0)}/{priority.get('check_count', 0)}",
            ])
            + " |"
        )

    for priority in summary.get("priorities", []):
        if not isinstance(priority, dict):
            continue
        lines.extend(["", f"## {priority.get('title', '')}", ""])
        checks = priority.get("checks", [])
        if not checks:
            lines.append("No checks recorded.")
        else:
            lines.extend(["| Check | Status | Path | Message |", "| --- | --- | --- | --- |"])
            for check in checks:
                if not isinstance(check, dict):
                    continue
                lines.append(
                    "| "
                    + " | ".join([
                        markdown_cell(check.get("check", "")),
                        markdown_cell(check.get("status", "")),
                        markdown_cell(check.get("path", "")),
                        markdown_cell(check.get("message", "")),
                    ])
                    + " |"
                )
        next_actions = priority.get("next_actions", [])
        if isinstance(next_actions, list) and next_actions:
            lines.extend(["", "Next actions:"])
            for action in next_actions:
                lines.append(f"- {markdown_cell(action)}")

    repair_checklist = summary.get("repair_checklist", [])
    lines.extend(["", "## Repair Checklist", ""])
    if not repair_checklist:
        lines.append("No repair checklist items recorded.")
    else:
        lines.extend(["| Rank | Priority | Action | Command | Expected Artifact | Success Signal |", "| ---: | --- | --- | --- | --- | --- |"])
        for item in repair_checklist:
            if not isinstance(item, dict):
                continue
            lines.append(
                "| "
                + " | ".join([
                    markdown_cell(item.get("rank", "")),
                    f"`{markdown_cell(item.get('priority_id', ''))}`",
                    f"`{markdown_cell(item.get('action_id', ''))}`",
                    f"`{markdown_cell(item.get('command', ''))}`",
                    f"`{markdown_cell(item.get('expected_artifact', ''))}`",
                    markdown_cell(item.get("success_signal", "")),
                ])
                + " |"
            )

    outputs = summary.get("outputs", {})
    lines.extend(["", "## Outputs", ""])
    if not isinstance(outputs, dict) or not outputs:
        lines.append("No outputs recorded.")
    else:
        lines.extend(["| Artifact | Path |", "| --- | --- |"])
        for key, value in outputs.items():
            lines.append(f"| `{markdown_cell(key)}` | `{markdown_cell(value)}` |")

    failures = summary.get("failures", [])
    lines.extend(["", "## Failures", ""])
    if not failures:
        lines.append("No failures found.")
    else:
        lines.extend(["| Stage | ID | Message |", "| --- | --- | --- |"])
        for failure in failures:
            if not isinstance(failure, dict):
                continue
            lines.append(
                "| "
                + " | ".join([
                    markdown_cell(failure.get("stage", "")),
                    markdown_cell(failure.get("id", "")),
                    markdown_cell(failure.get("message", "")),
                ])
                + " |"
            )
    return "\n".join(lines) + "\n"

def build_adoption_check_summary(
    package: dict[str, object],
    dist: dict[str, object],
    quickstart_summary: dict[str, object],
    doctor_summary: dict[str, object],
    claim_check_summary: dict[str, object],
    template_gallery: dict[str, object],
    casebook_check_summary: dict[str, object],
    artifact_root: Path,
    adoption_rerun_root: Path | None = None,
) -> dict[str, object]:
    package_checks = package_check_lookup(package)
    dist_checks = package_check_lookup(dist)
    installed_mode = "installed_metadata_mode" in package_checks
    quickstart_outputs = quickstart_summary.get("outputs", {}) if isinstance(quickstart_summary.get("outputs", {}), dict) else {}
    doctor_outputs = doctor_summary.get("outputs", {}) if isinstance(doctor_summary.get("outputs", {}), dict) else {}
    claim_outputs = claim_check_summary.get("outputs", {}) if isinstance(claim_check_summary.get("outputs", {}), dict) else {}
    gallery_templates = [
        template
        for template in template_gallery.get("templates", [])
        if isinstance(template, dict)
    ]

    open_source_checks = [
        package_check_item(package_checks, "readme_adoption_entry", installed_mode=installed_mode, installed_ok=True),
        package_check_item(package_checks, "quickstart_docs", installed_mode=installed_mode, installed_ok=True),
        package_check_item(package_checks, "walkthrough_commands", installed_mode=installed_mode, installed_ok=True),
        release_check_item(
            "quickstart_ready",
            quickstart_summary.get("status") == "quickstart_ready",
            f"Quickstart ended as {quickstart_summary.get('status', '')}.",
            str(quickstart_outputs.get("quickstart_summary", "")),
        ),
        release_check_item(
            "quickstart_doctor_handoff",
            command_list_contains(quickstart_summary.get("next_commands", []), "doctor --project-dir"),
            "Quickstart tells the user to run doctor next.",
            str(quickstart_outputs.get("quickstart_report", "")),
        ),
    ]

    trusted_audit_checks = [
        package_check_item(package_checks, "audit_review_docs", installed_mode=installed_mode, installed_ok=True),
        package_check_item(package_checks, "claim_check_docs", installed_mode=installed_mode, installed_ok=True),
        package_check_item(package_checks, "doctor_docs", installed_mode=installed_mode, installed_ok=True),
        release_check_item(
            "claim_check_ready",
            claim_check_summary.get("status") == "claim_check_ready",
            f"Claim check ended as {claim_check_summary.get('status', '')}.",
            str(claim_outputs.get("claim_check", "")),
        ),
        release_check_item(
            "doctor_ready",
            doctor_summary.get("status") == "doctor_ready",
            f"Doctor ended as {doctor_summary.get('status', '')}.",
            str(doctor_outputs.get("doctor_summary", "")),
        ),
        release_check_item(
            "doctor_repair_checklist",
            isinstance(doctor_summary.get("repair_checklist", []), list) and bool(doctor_summary.get("repair_checklist", [])),
            "Doctor emits a repair checklist with commands, expected artifacts, and success signals.",
            str(doctor_outputs.get("doctor_report", "")),
        ),
    ]

    generality_checks = [
        package_check_item(package_checks, "template_gallery_docs", installed_mode=installed_mode, installed_ok=True),
        package_check_item(package_checks, "adapter_profiles_docs", installed_mode=installed_mode, installed_ok=True),
        package_check_item(package_checks, "casebook_check_docs", installed_mode=installed_mode, installed_ok=True),
        release_check_item(
            "template_gallery_ready",
            template_gallery.get("status") == "template_gallery_ready",
            f"Template gallery ended as {template_gallery.get('status', '')}.",
            str(template_gallery.get("json_path", "")),
        ),
        release_check_item(
            "template_gallery_breadth",
            int(template_gallery.get("template_count", 0) or 0) >= 4,
            "Template gallery covers at least four starter workflows.",
            str(template_gallery.get("json_path", "")),
        ),
        release_check_item(
            "non_neural_template_breadth",
            int(template_gallery.get("non_neural_template_count", 0) or 0) >= 3,
            "Template gallery includes at least three non-neural starter workflows.",
            str(template_gallery.get("json_path", "")),
        ),
        release_check_item(
            "template_doctor_handoffs",
            bool(gallery_templates) and all(command_list_contains(template.get("first_commands", []), "doctor --project-dir") for template in gallery_templates),
            "Every starter template exposes a doctor handoff in first_commands.",
            str(template_gallery.get("json_path", "")),
        ),
        release_check_item(
            "casebook_check_ready",
            casebook_check_summary.get("status") == "casebook_check_ready",
            f"Casebook check ended as {casebook_check_summary.get('status', '')}.",
            str(casebook_check_summary.get("outputs", {}).get("summary", "")) if isinstance(casebook_check_summary.get("outputs", {}), dict) else "",
        ),
        release_check_item(
            "casebook_positive_and_blocked_paths",
            int(casebook_check_summary.get("positive_demo_ready_count", 0) or 0) >= 4
            and int(casebook_check_summary.get("blocked_path_count", 0) or 0) >= 4
            and int(casebook_check_summary.get("bundle_verified_count", 0) or 0) >= 4,
            "Casebook check proves positive demos, placeholder blockers, and verified bundles across starter templates.",
            str(casebook_check_summary.get("outputs", {}).get("report", "")) if isinstance(casebook_check_summary.get("outputs", {}), dict) else "",
        ),
    ]

    release_distribution_checks = [
        release_check_item(
            "package_ready",
            package.get("status") == "package_ready",
            f"Package checks ended as {package.get('status', '')}.",
            ROOT,
        ),
        release_check_item(
            "dist_ready_or_skipped",
            dist.get("status") in {"dist_ready", "dist_skipped"},
            f"Distribution checks ended as {dist.get('status', '')}.",
            artifact_root / "dist",
        ),
        package_check_any_item(package_checks, "console_script", ["console_script", "installed_console_script"], installed_mode=installed_mode),
        package_check_any_item(package_checks, "template_package_data", ["template_package_data", "template_package_root"], installed_mode=installed_mode),
        package_check_item(package_checks, "gitignore_build_artifacts", installed_mode=installed_mode, installed_ok=True),
        dist_check_item(
            dist_checks,
            "source_build_cache_cleanup",
            dist_status=str(dist.get("status", "")),
            dist_root=artifact_root / "dist",
            skipped_ok=True,
        ),
        package_check_item(package_checks, "manifest_release_docs", installed_mode=installed_mode, installed_ok=True),
        package_check_item(package_checks, "release_checklist", installed_mode=installed_mode, installed_ok=True),
        package_check_item(package_checks, "template_release_docs", installed_mode=installed_mode, installed_ok=True),
        package_check_item(package_checks, "template_install_docs", installed_mode=installed_mode, installed_ok=True),
    ]

    user_experience_checks = [
        package_check_item(package_checks, "adoption_priorities", installed_mode=installed_mode, installed_ok=True),
        package_check_item(package_checks, "adoption_check_docs", installed_mode=installed_mode, installed_ok=True),
        package_check_item(package_checks, "doctor_docs", installed_mode=installed_mode, installed_ok=True),
        package_check_item(package_checks, "quickstart_docs", installed_mode=installed_mode, installed_ok=True),
        release_check_item(
            "quickstart_doctor_handoff",
            command_list_contains(quickstart_summary.get("next_commands", []), "doctor --project-dir"),
            "Quickstart gives a concrete next command for project diagnosis.",
            str(quickstart_outputs.get("quickstart_report", "")),
        ),
        release_check_item(
            "doctor_repair_checklist",
            isinstance(doctor_summary.get("repair_checklist", []), list) and bool(doctor_summary.get("repair_checklist", [])),
            "Doctor gives repair commands and expected artifacts.",
            str(doctor_outputs.get("doctor_report", "")),
        ),
        release_check_item(
            "claim_check_next_actions",
            isinstance(claim_check_summary.get("next_actions", []), list) and bool(claim_check_summary.get("next_actions", [])),
            "Claim check provides next actions for human review or repair.",
            str(claim_outputs.get("claim_check_report", "")),
        ),
    ]

    priorities = [
        adoption_priority(
            "open_source_entry_point",
            "Open-source entry point",
            open_source_checks,
            [
                "Keep README adoption path, quickstart docs, and examples walkthrough in sync with the CLI.",
                "Run `falsiflow quickstart --template biointerface_coatings --out /tmp/falsiflow_quickstart --strict --json`.",
            ],
        ),
        adoption_priority(
            "trusted_audit_experience",
            "Trusted audit experience",
            trusted_audit_checks,
            [
                "Run `falsiflow doctor --project-dir <project> --strict` and inspect doctor_summary.json.",
                "Repair claim-check, audit-review, source, bundle, or verification blockers before sharing a claim.",
            ],
        ),
        adoption_priority(
            "generality_proof",
            "Generality proof",
            generality_checks,
            [
                "Run `falsiflow template-gallery --json` and keep non-neural templates passing.",
                "Add or repair starter templates until cross-domain coverage is visible from first_commands.",
            ],
        ),
        adoption_priority(
            "release_and_distribution",
            "Release and distribution",
            release_distribution_checks,
            [
                "Run `falsiflow release-check --out-dir <dir> --json --force` before tagging a release.",
                "Run adoption-check without `--skip-dist` when validating a distributable source tree.",
            ],
        ),
        adoption_priority(
            "user_experience_convergence",
            "User experience convergence",
            user_experience_checks,
            [
                "Keep the priority order, adoption-check docs, quickstart handoff, and doctor repair checklist aligned.",
                "Use adoption_check.json as the single status artifact when answering priority-completion questions.",
            ],
        ),
    ]

    failures: list[dict[str, str]] = []
    for priority in priorities:
        for check in priority.get("checks", []):
            if isinstance(check, dict) and check.get("status") != "passed":
                failures.append(failure_record(str(priority.get("priority_id", "")), str(check.get("check", "")), str(check.get("message", ""))))

    release_validation_status, release_validation_message = adoption_release_validation_status(str(dist.get("status", "")))
    ready_priority_count = sum(1 for priority in priorities if priority.get("status") == "priority_ready")
    priority_count = len(priorities)
    outputs = {
        "adoption_check": str(artifact_root / "adoption_check.json"),
        "adoption_report": str(artifact_root / "adoption_check.md"),
        "template_gallery": str(template_gallery.get("json_path", artifact_root / "template_gallery.json")),
        "casebook_check": str(casebook_check_summary.get("outputs", {}).get("summary", artifact_root / "casebook_check" / "casebook_check.json")) if isinstance(casebook_check_summary.get("outputs", {}), dict) else str(artifact_root / "casebook_check" / "casebook_check.json"),
        "quickstart_summary": str(quickstart_outputs.get("quickstart_summary", "")),
        "doctor_summary": str(doctor_outputs.get("doctor_summary", "")),
        "claim_check": str(claim_outputs.get("claim_check", "")),
    }
    return {
        "status": "adoption_ready" if ready_priority_count == priority_count else "adoption_blocked",
        "artifact_root": str(artifact_root),
        "package_status": str(package.get("status", "")),
        "dist_status": str(dist.get("status", "")),
        "release_validation_status": release_validation_status,
        "release_validation_message": release_validation_message,
        "quickstart_status": str(quickstart_summary.get("status", "")),
        "doctor_status": str(doctor_summary.get("status", "")),
        "claim_check_status": str(claim_check_summary.get("status", "")),
        "template_gallery_status": str(template_gallery.get("status", "")),
        "casebook_check_status": str(casebook_check_summary.get("status", "")),
        "priority_count": priority_count,
        "ready_priority_count": ready_priority_count,
        "readiness_pct": round((ready_priority_count / priority_count) * 100, 1) if priority_count else 0.0,
        "failure_count": len(failures),
        "priorities": priorities,
        "failures": failures,
        "outputs": outputs,
        "repair_checklist": adoption_repair_checklist(
            priorities,
            artifact_root,
            str(dist.get("status", "")),
            adoption_rerun_root=adoption_rerun_root,
        ),
    }

def write_adoption_check_artifacts(summary: dict[str, object], artifact_root: Path) -> None:
    (artifact_root / "adoption_check.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    (artifact_root / "adoption_check.md").write_text(render_adoption_check_report(summary), encoding="utf-8")

def run_adoption_check(
    artifact_root: Path,
    run_dist: bool = False,
    *,
    source_root: Path = ROOT,
    package_checks_runner: PackageChecksRunner,
    dist_checks_runner: DistChecksRunner,
    template_gallery_runner: TemplateGalleryRunner,
    casebook_check_runner: CasebookCheckRunner,
    quickstart_runner: QuickstartRunner,
    doctor_runner: DoctorRunner,
    default_evidence_path: DefaultEvidencePath,
    template_resolver: TemplateResolver,
    claim_check_runner: ClaimCheckRunner,
) -> dict[str, object]:
    source_root = source_root.resolve()
    artifact_root = artifact_root.resolve()
    artifact_root.mkdir(parents=True, exist_ok=True)
    package = package_checks_runner(source_root)
    dist = dist_checks_runner(source_root, artifact_root, run_dist)

    try:
        template_gallery = template_gallery_runner(
            include_env=False,
            out=artifact_root / "template_gallery.md",
            json_out=artifact_root / "template_gallery.json",
        )
    except Exception as exc:  # pragma: no cover - defensive CLI boundary.
        template_gallery = {
            "status": "template_gallery_blocked",
            "template_count": 0,
            "non_neural_template_count": 0,
            "templates": [],
            "message": str(exc),
        }

    try:
        casebook_check_summary = casebook_check_runner(
            artifact_root / "casebook_check",
            [],
            force=True,
            include_env=False,
        )
    except Exception as exc:  # pragma: no cover - defensive CLI boundary.
        casebook_check_summary = {
            "status": "casebook_check_blocked",
            "template_count": 0,
            "positive_demo_ready_count": 0,
            "blocked_path_count": 0,
            "bundle_verified_count": 0,
            "outputs": {},
            "message": str(exc),
        }

    try:
        quickstart_summary = quickstart_runner(
            "biointerface_coatings",
            artifact_root / "quickstart_project",
            force=True,
            include_env=False,
        )
    except Exception as exc:  # pragma: no cover - defensive CLI boundary.
        quickstart_summary = {
            "status": "quickstart_blocked",
            "template": "biointerface_coatings",
            "project_dir": str(artifact_root / "quickstart_project"),
            "next_commands": [],
            "outputs": {},
            "message": str(exc),
        }

    try:
        quickstart_project_dir = artifact_root / "quickstart_project"
        doctor_summary = doctor_runner(
            quickstart_project_dir,
            quickstart_project_dir / "project.json",
            default_evidence_path(quickstart_project_dir),
            artifact_root / "doctor",
            force=True,
        )
    except Exception as exc:  # pragma: no cover - defensive CLI boundary.
        doctor_summary = {
            "status": "doctor_blocked",
            "project_dir": str(artifact_root / "quickstart_project"),
            "repair_checklist": [],
            "outputs": {},
            "message": str(exc),
        }

    try:
        claim_template_dir = template_resolver("neural_materials", include_env=False)
        if claim_template_dir is None:
            claim_check_summary = {
                "status": "claim_check_blocked",
                "next_actions": [],
                "outputs": {},
                "message": "neural_materials template was not found.",
            }
        else:
            claim_check_summary = claim_check_runner(
                claim_template_dir / "project.json",
                claim_template_dir / "evidence_pass_demo.csv",
                artifact_root / "claim_check",
                force=True,
            )
    except Exception as exc:  # pragma: no cover - defensive CLI boundary.
        claim_check_summary = {
            "status": "claim_check_blocked",
            "next_actions": [],
            "outputs": {},
            "message": str(exc),
        }

    summary = build_adoption_check_summary(
        package,
        dist,
        quickstart_summary,
        doctor_summary,
        claim_check_summary,
        template_gallery,
        casebook_check_summary,
        artifact_root,
    )
    write_adoption_check_artifacts(summary, artifact_root)
    return summary
