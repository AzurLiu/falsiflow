"""Command-line interface for Falsiflow."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import webbrowser
from pathlib import Path


from .adapters import adapter_profile_names, write_limina_conversion, write_wide_lab_conversion
from .adoption import (
    adoption_release_validation_status,
    adoption_repair_checklist,
    build_adoption_check_summary,
    release_validation_status_for_dist,
    run_adoption_check as run_adoption_check_core,
    write_adoption_check_artifacts,
)
from .bundle import (
    build_bundle,
    render_bundle_verification_report,
    render_source_manifest_report,
    source_manifest,
    verification_issue,
    verify_bundle,
    verify_bundle_zip,
)
from .browser_demo import (
    run_try as run_try_core,
    run_wizard,
    run_workbench_check as run_workbench_check_core,
    write_workbench_uploads as write_workbench_uploads_core,
)
from .casebook_check import run_casebook_check as run_casebook_check_core
from .claim_check import run_claim_check
from .discovery import run_discover
from .doctor import default_project_evidence_path, run_doctor
from .demo import run_demo as run_demo_core
from .quickstart import run_quickstart as run_quickstart_core
from .scaffold import run_scaffold, run_template_scaffold
from .release import (
    dist_release_checks,
    failure_record,
    get_nested,
    package_init_version,
    package_release_checks,
    pyproject_data,
    release_check_item,
    render_release_check_report,
    run_release_check as run_release_check_core,
    schema_filename,
)
from .local_server import (
    check_launchpad_http,
    ensure_try_output as ensure_try_output_core,
    make_httpd as make_httpd_core,
    onboard_summary,
    serve_summary,
)
from .public_release import (
    run_demo_package as run_demo_package_core,
    run_external_evidence_template as run_external_evidence_template_core,
    run_external_check as run_external_check_core,
    run_launch_kit as run_launch_kit_core,
    run_publish_kit as run_publish_kit_core,
    run_static_demo as run_static_demo_core,
)
from .template_check import run_template_check, safe_template_child_path
from .template_discovery import (
    PACKAGE_TEMPLATE_ROOT,
    REPO_TEMPLATE_ROOT,
    TEMPLATE_ROOTS,
    all_template_roots,
    env_template_roots,
    template_path,
    template_records,
    template_root,
)
from .template_gallery import run_template_gallery as run_template_gallery_core
from .template_pack import (
    render_template_pack_verification_report,
    run_template_pack as run_template_pack_core,
    verify_template_pack,
    verify_template_pack_zip,
)
from .template_registry import (
    read_json_object,
    run_template_lock,
    run_template_registry,
    safe_template_identifier,
)
from .template_provenance import (
    run_template_attestation,
    run_template_policy,
    run_verify_template_attestation,
    run_verify_template_policy,
)
from .template_release import (
    render_template_release_verification_report,
    run_template_release,
    run_verify_template_release,
)
from .template_install import (
    run_template_install as run_template_install_core,
    run_template_install_workflow,
)
from .core import (
    configured_evidence_keys,
    discover_claim_summary_paths,
    evidence_rows_by_key,
    falsiflow_schema,
    load_project,
    read_csv_rows_with_diagnostics,
    validate_project_config,
    write_portfolio_artifacts,
    write_render_artifacts,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_KINDS = [
    "project",
    "evidence-row",
    "evidence-record",
    "candidate-recipe",
    "discovery-summary",
    "claim-summary",
    "audit-review",
    "portfolio-summary",
    "import-coverage",
    "source-manifest",
    "bundle-manifest",
    "bundle-verification",
    "claim-check",
    "quickstart-summary",
    "doctor-summary",
    "demo-summary",
    "template-check",
    "template-pack-manifest",
    "template-pack-verification",
    "template-install",
    "template-registry",
    "template-lock",
    "template-attestation",
    "template-attestation-verification",
    "template-policy",
    "template-policy-verification",
    "template-release",
    "template-release-verification",
    "template-gallery",
    "casebook-check",
    "external-evidence",
    "external-readiness",
    "adoption-check",
    "release-check",
    "all",
]


def cmd_init(args: argparse.Namespace) -> int:
    source = template_path(args.template, args.template_root)
    if source is None:
        raise SystemExit(f"Unknown template `{args.template}`. Run `falsiflow templates` to list available templates.")
    if args.out.exists() and any(args.out.iterdir()):
        raise SystemExit(f"Refusing to overwrite non-empty directory: {args.out}")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, args.out, dirs_exist_ok=True)
    print(f"Initialized Falsiflow project from `{args.template}` at {args.out}")
    return 0


def prepare_output_directory(path: Path, label: str, force: bool = False) -> None:
    if path.exists() and any(path.iterdir()):
        if not force:
            raise SystemExit(f"Refusing to overwrite non-empty {label} without --force: {path}")
        resolved = path.resolve()
        protected = {Path.cwd().resolve(), Path.home().resolve(), Path("/").resolve()}
        if resolved in protected:
            raise SystemExit(f"Refusing to remove protected {label}: {path}")
        shutil.rmtree(path)
    path.parent.mkdir(parents=True, exist_ok=True)


def remove_generated_path(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    elif path.exists() or path.is_symlink():
        path.unlink()


def cmd_scaffold(args: argparse.Namespace) -> int:
    summary = run_scaffold(
        args.out,
        project_id=args.project_id,
        project_name=args.project_name,
        domain=args.domain,
        claim_id=args.claim_id,
        claim_statement=args.claim_statement,
        gate=args.gate,
        gate_title=args.gate_title,
        rule=args.rule,
        sample=args.sample,
        candidate_id=args.candidate_id,
        sample_id=args.sample_id,
    )
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print("Falsiflow scaffold: scaffolded")
        print(f"Gates: {summary['gate_count']}")
        print(f"Required evidence rows: {summary['required_evidence_rows']}")
        print(f"Wrote {summary['project_path']}")
        print(f"Wrote {summary['evidence_template_path']}")
        print(f"Wrote {summary['source_files_dir']}")
        print(f"Wrote {summary['readme_path']}")
    return 0


def cmd_template_scaffold(args: argparse.Namespace) -> int:
    summary = run_template_scaffold(
        args.out,
        template_id=args.template_id,
        template_name=args.template_name,
        template_description=args.template_description,
        project_id=args.project_id,
        project_name=args.project_name,
        domain=args.domain,
        claim_id=args.claim_id,
        claim_statement=args.claim_statement,
        gate=args.gate,
        gate_title=args.gate_title,
        rule=args.rule,
        sample=args.sample,
        candidate_id=args.candidate_id,
        sample_id=args.sample_id,
        check_out_dir=args.check_out_dir,
        force=args.force,
        template_check_runner=run_template_check,
    )
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow template-scaffold: {summary['status']}")
        print(f"Template: {summary['template_id']}")
        print(f"Gates: {summary['gate_count']}")
        print(f"Required evidence rows: {summary['required_evidence_rows']}")
        print(f"Template check: {summary['template_check_status']}")
        print(f"Wrote {summary['template_manifest_path']}")
        print(f"Wrote {summary['project_path']}")
        print(f"Wrote {summary['pass_evidence_path']}")
        print(f"Wrote {summary['placeholder_evidence_path']}")
        print(f"Wrote {summary['source_file_path']}")
    return 0 if summary["status"] == "template_scaffolded" else 2


def cmd_render(args: argparse.Namespace) -> int:
    project = load_project(args.config)
    if args.evidence is not None and not args.evidence.exists():
        raise SystemExit(f"Evidence file does not exist: {args.evidence}")
    evidence_rows, evidence_issues = read_csv_rows_with_diagnostics(args.evidence)
    rendered = write_render_artifacts(project, evidence_rows, args.out_dir, evidence_file_issues=evidence_issues)
    audit = rendered["audit"]
    print(f"Falsiflow render: {audit['status']}")
    print(f"Claim ready: {str(bool(audit['claim_ready'])).lower()}")
    print(f"Wrote {args.out_dir / 'measurement_template.csv'}")
    print(f"Wrote {args.out_dir / 'claim_audit.json'}")
    print(f"Wrote {args.out_dir / 'claim_audit.md'}")
    print(f"Wrote {args.out_dir / 'audit_review.json'}")
    print(f"Wrote {args.out_dir / 'audit_review.md'}")
    print(f"Wrote {args.out_dir / 'claim_summary.json'}")
    print(f"Wrote {args.out_dir / 'next_actions.json'}")
    print(f"Wrote {args.out_dir / 'dashboard.html'}")
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    project = load_project(args.config)
    if not args.evidence.exists():
        raise SystemExit(f"Evidence file does not exist: {args.evidence}")
    evidence_rows, evidence_issues = read_csv_rows_with_diagnostics(args.evidence)
    rendered = write_render_artifacts(project, evidence_rows, args.out_dir, evidence_file_issues=evidence_issues)
    audit = rendered["audit"]
    print(f"Falsiflow audit: {audit['status']}")
    print(f"Claim ready: {str(bool(audit['claim_ready'])).lower()}")
    print(f"Wrote {args.out_dir / 'claim_audit.json'}")
    print(f"Wrote {args.out_dir / 'claim_audit.md'}")
    print(f"Wrote {args.out_dir / 'audit_review.json'}")
    print(f"Wrote {args.out_dir / 'audit_review.md'}")
    print(f"Wrote {args.out_dir / 'claim_summary.json'}")
    print(f"Wrote {args.out_dir / 'next_actions.json'}")
    print(f"Wrote {args.out_dir / 'dashboard.html'}")
    return 0 if audit["claim_ready"] or not args.strict else 2


def cmd_bundle(args: argparse.Namespace) -> int:
    bundle = build_bundle(args.config, args.evidence, args.out_dir, args.zip_out, force=args.force)

    print(f"Falsiflow bundle: {bundle['status']}")
    print(f"Claim ready: {str(bool(bundle['claim_ready'])).lower()}")
    print(f"Source status: {bundle['source_status']}")
    print(f"Artifacts: {bundle['artifact_count']}")
    print(f"Copied source files: {bundle['source_file_count']}")
    print(f"Wrote {args.out_dir / 'bundle_manifest.json'}")
    if args.zip_out is not None:
        print(f"Wrote {args.zip_out}")
    return 0 if bundle["status"] == "bundle_ready" or not args.strict else 2


def cmd_verify_bundle(args: argparse.Namespace) -> int:
    report = verify_bundle_zip(args.zip_path) if args.zip_path is not None else verify_bundle(args.bundle_dir)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    if args.report_out:
        args.report_out.parent.mkdir(parents=True, exist_ok=True)
        args.report_out.write_text(render_bundle_verification_report(report), encoding="utf-8")
    print(f"Falsiflow verify-bundle: {report['status']}")
    print(f"Integrity: {report['integrity_status']}")
    print(f"Bundle status: {report['bundle_status']}")
    print(f"Artifacts checked: {report['checked_artifact_count']}/{report['artifact_count']}")
    print(f"Issues: {report['issue_count']}")
    if args.out:
        print(f"Wrote {args.out}")
    if args.report_out:
        print(f"Wrote {args.report_out}")
    if report["status"] == "bundle_failed":
        return 2
    if args.strict and report["status"] != "bundle_verified":
        return 2
    return 0


def resolve_claim_check_paths(args: argparse.Namespace) -> tuple[Path, Path, Path]:
    project_dir = args.project_dir.expanduser() if getattr(args, "project_dir", None) is not None else None
    config = args.config.expanduser() if args.config is not None else None
    evidence = args.evidence.expanduser() if args.evidence is not None else None
    out_dir = args.out_dir.expanduser() if args.out_dir is not None else None

    if project_dir is not None:
        config = config or project_dir / "project.json"
        evidence = evidence or project_dir / "evidence_pass_demo.csv"
        out_dir = out_dir or project_dir / "claim_check"

    missing = []
    if config is None:
        missing.append("--config or --project-dir")
    if evidence is None:
        missing.append("--evidence or --project-dir")
    if out_dir is None:
        missing.append("--out-dir or --project-dir")
    if missing:
        raise SystemExit("Missing required claim-check path(s): " + ", ".join(missing))
    if not config.exists():
        raise SystemExit(f"Project config does not exist: {config}")
    if not evidence.exists():
        raise SystemExit(f"Evidence file does not exist: {evidence}")
    return config, evidence, out_dir


def cmd_claim_check(args: argparse.Namespace) -> int:
    config, evidence, out_dir = resolve_claim_check_paths(args)
    summary = run_claim_check(config, evidence, out_dir, force=args.force)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow claim-check: {summary['status']}")
        print(f"Config: {config}")
        print(f"Evidence: {evidence}")
        print(f"Claim ready: {str(bool(summary['claim_ready'])).lower()}")
        print(f"Audit review: {summary['audit_review_status']}")
        print(f"Sources: {summary['source_status']}")
        print(f"Bundle: {summary['bundle_status']}")
        print(f"Verification: {summary['verification_status']}")
        print(f"Failures: {summary['failure_count']}")
        print(f"Wrote {out_dir / 'claim_check.json'}")
        print(f"Wrote {out_dir / 'claim_check.md'}")
        print(f"Wrote {out_dir / 'evidence_bundle.zip'}")
        print(f"Wrote {out_dir / 'evidence_bundle_verify.json'}")
        print(f"Wrote {out_dir / 'evidence_bundle_verify.md'}")
    return 0 if summary["status"] == "claim_check_ready" or not args.strict else 2


def run_quickstart(template: str, out_dir: Path, template_roots: list[Path] | None = None, force: bool = False, include_env: bool = True) -> dict[str, object]:
    return run_quickstart_core(
        template,
        out_dir,
        template_roots=template_roots,
        force=force,
        include_env=include_env,
        template_resolver=template_path,
    )


def cmd_quickstart(args: argparse.Namespace) -> int:
    summary = run_quickstart(args.template, args.out, args.template_root, force=args.force)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow quickstart: {summary['status']}")
        print(f"Template: {summary['template']}")
        print(f"Project: {summary['project_dir']}")
        print(f"Claim check: {summary['claim_check_status']}")
        print(f"Verification: {summary['verification_status']}")
        print(f"Failures: {summary['failure_count']}")
        outputs = summary.get("outputs", {})
        if isinstance(outputs, dict):
            print(f"Wrote {outputs.get('quickstart_summary', '')}")
            print(f"Wrote {outputs.get('quickstart_report', '')}")
            print(f"Wrote {outputs.get('claim_check', '')}")
            print(f"Wrote {outputs.get('evidence_bundle_zip', '')}")
        next_commands = summary.get("next_commands", [])
        if isinstance(next_commands, list) and next_commands:
            print(f"Next: {next_commands[0]}")
    return 0 if summary["status"] == "quickstart_ready" or not args.strict else 2


def run_try(template: str, out_dir: Path, template_roots: list[Path] | None = None, force: bool = False, include_env: bool = True) -> dict[str, object]:
    return run_try_core(
        template,
        out_dir,
        template_roots=template_roots,
        force=force,
        include_env=include_env,
        quickstart_runner=run_quickstart,
    )


def cmd_try(args: argparse.Namespace) -> int:
    summary = run_try(args.template, args.out_dir, args.template_root, force=args.force)
    outputs = summary.get("outputs", {}) if isinstance(summary.get("outputs"), dict) else {}
    launchpad_path = Path(str(outputs.get("launchpad", ""))) if outputs.get("launchpad") else None
    if args.open and launchpad_path is not None:
        webbrowser.open(launchpad_path.resolve().as_uri())
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow try: {summary['status']}")
        print(f"Template: {summary['template']}")
        print(f"Project: {summary['project_dir']}")
        print(f"Claim check: {summary['claim_check_status']}")
        print(f"Verification: {summary['verification_status']}")
        print(f"Open: {outputs.get('launchpad', outputs.get('try_report', ''))}")
        print(f"Report: {outputs.get('try_report', '')}")
        print(f"Workbench: {outputs.get('workbench', '')}")
        print(f"Dashboard: {outputs.get('dashboard', '')}")
        print(f"Wizard: {outputs.get('wizard', '')}")
        next_commands = summary.get("next_commands", [])
        if isinstance(next_commands, list) and next_commands:
            print(f"Next: {next_commands[0]}")
    return 0 if summary["status"] == "try_ready" or not args.strict else 2


def cmd_wizard(args: argparse.Namespace) -> int:
    summary = run_wizard(args.out, force=args.force)
    if args.open:
        webbrowser.open(args.out.resolve().as_uri())
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow wizard: {summary['status']}")
        print(f"Open: {summary['wizard_path']}")
        print(f"Next: {summary['next_commands'][1]}")
    return 0


def write_workbench_uploads(out_dir: Path, payload: dict[str, object]) -> tuple[str, Path, Path, Path]:
    return write_workbench_uploads_core(out_dir, payload, template_resolver=template_path)


def run_workbench_check(out_dir: Path, payload: dict[str, object]) -> dict[str, object]:
    return run_workbench_check_core(out_dir, payload, template_resolver=template_path)


def cmd_discover(args: argparse.Namespace) -> int:
    summary = run_discover(args.goal, args.out_dir, force=args.force)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow discover: {summary['status']}")
        print(f"Goal: {summary['goal']}")
        print(f"Top candidate: {summary['top_candidate']}")
        print(f"AI used: {str(bool(summary['ai_used'])).lower()}")
        print(f"Claim ready: {str(bool(summary['claim_ready'])).lower()}")
        print(f"Wrote {summary['outputs']['summary']}")
        print(f"Wrote {summary['outputs']['candidate_queue']}")
        print(f"Wrote {summary['outputs']['project_draft']}")
    return 0


def cmd_agent_discover(args: argparse.Namespace) -> int:
    summary = run_discover(args.goal, args.out_dir, force=args.force)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow agent discover: {summary['status']}")
        print("Agent boundary: structured candidate proposal only; Core still decides claim readiness.")
        print(f"Goal: {summary['goal']}")
        print(f"Top candidate: {summary['top_candidate']}")
        print(f"AI used: {str(bool(summary['ai_used'])).lower()}")
        print(f"Claim ready: {str(bool(summary['claim_ready'])).lower()}")
        print(f"Wrote {summary['outputs']['summary']}")
        print(f"Wrote {summary['outputs']['candidate_queue']}")
        print(f"Wrote {summary['outputs']['project_draft']}")
    return 0


def cmd_candidate_rank(args: argparse.Namespace) -> int:
    summary = run_discover(args.goal, args.out_dir, force=args.force)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow candidate rank: {summary['status']}")
        print(f"Goal: {summary['goal']}")
        print(f"Top candidate: {summary['top_candidate']}")
        print(f"Candidate count: {summary['candidate_count']}")
        print(f"Claim ready: {str(bool(summary['claim_ready'])).lower()}")
        print(f"Wrote {summary['outputs']['candidate_queue']}")
        print(f"Wrote {summary['outputs']['ranking']}")
    return 0


def cmd_assay_plan(args: argparse.Namespace) -> int:
    summary = run_discover(args.goal, args.out_dir, force=args.force)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow assay-plan: {summary['status']}")
        print(f"Goal: {summary['goal']}")
        print(f"Top candidate: {summary['top_candidate']}")
        print("Boundary: assay/RFQ drafts still require measured source-backed evidence.")
        print(f"Wrote {summary['outputs']['assay_plan']}")
        print(f"Wrote {summary['outputs']['rfq_package']}")
        print(f"Wrote {summary['outputs']['project_draft']}")
    return 0


def ensure_try_output(template: str, out_dir: Path, template_roots: list[Path] | None, force: bool, include_env: bool = True) -> dict[str, object]:
    return ensure_try_output_core(
        template,
        out_dir,
        template_roots,
        force,
        include_env=include_env,
        try_runner=run_try,
    )


def make_httpd(out_dir: Path, host: str, port: int):
    return make_httpd_core(
        out_dir,
        host,
        port,
        template_records_provider=template_records,
        workbench_checker=run_workbench_check,
    )


def cmd_serve(args: argparse.Namespace) -> int:
    entry_command = str(getattr(args, "entry_command", "serve"))
    try_summary = ensure_try_output(args.template, args.out_dir, args.template_root, force=args.force)
    httpd = make_httpd(args.out_dir, args.host, args.port)
    actual_port = int(httpd.server_address[1])
    summary = serve_summary(args.out_dir, try_summary, args.host, actual_port, entry_command=entry_command)
    url = str(summary["url"])

    if args.check:
        check_status, status_code = check_launchpad_http(httpd, url)
        summary = serve_summary(args.out_dir, try_summary, args.host, actual_port, check_status=check_status, status_code=status_code, entry_command=entry_command)
        if args.json:
            print(json.dumps(summary, indent=2, sort_keys=True))
        else:
            print(f"Falsiflow {entry_command}: {summary['status']}")
            print(f"URL: {summary['url']}")
            print(f"HTTP check: {summary['check_status']} {summary['status_code']}")
            print(f"Wrote {args.out_dir / 'serve_summary.json'}")
        return 0 if summary["status"] == "serve_ready" else 2

    if args.open:
        webbrowser.open(url)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True), flush=True)
    else:
        print(f"Falsiflow {entry_command}: serving")
        print(f"URL: {url}")
        print(f"Directory: {args.out_dir}")
        print("Press Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
    return 0


def cmd_start(args: argparse.Namespace) -> int:
    args.entry_command = "start"
    args.force = bool(args.reset)
    args.open = not bool(args.no_open)
    return cmd_serve(args)


def cmd_onboard(args: argparse.Namespace) -> int:
    try_summary = ensure_try_output(args.template, args.out_dir, args.template_root, force=bool(args.reset))
    httpd = make_httpd(args.out_dir, args.host, args.port)
    actual_port = int(httpd.server_address[1])
    start_summary = serve_summary(args.out_dir, try_summary, args.host, actual_port, entry_command="start")
    summary = onboard_summary(args.out_dir, start_summary)
    summary_path = args.out_dir / "onboard_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    if args.check:
        url = str(start_summary["url"])
        check_status, status_code = check_launchpad_http(httpd, url)
        start_summary = serve_summary(
            args.out_dir,
            try_summary,
            args.host,
            actual_port,
            check_status=check_status,
            status_code=status_code,
            entry_command="start",
        )
        summary = onboard_summary(args.out_dir, start_summary)
        summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
        if args.json:
            print(json.dumps(summary, indent=2, sort_keys=True))
        else:
            print(f"Falsiflow onboard: {summary['status']}")
            print(f"Local app: {summary['launchpad_url']}")
            print(f"HTTP check: {start_summary['check_status']} {start_summary['status_code']}")
            print(f"Wrote {summary_path}")
        return 0 if summary["status"] == "onboard_ready" else 2

    if not args.no_open:
        webbrowser.open(str(summary["launchpad_url"]))
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True), flush=True)
    else:
        print("Falsiflow onboard: serving")
        print(f"Local app: {summary['launchpad_url']}")
        print(f"Report: {summary['try_report_url']}")
        print(f"Wizard: {summary['wizard_url']}")
        print(f"Wrote {summary_path}")
        print("Press Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
    return 0


def run_static_demo(template: str, out_dir: Path, template_roots: list[Path] | None = None, force: bool = False) -> dict[str, object]:
    return run_static_demo_core(template, out_dir, template_roots, force=force, try_runner=run_try)


def run_demo_package(template: str, out_dir: Path, template_roots: list[Path] | None = None, force: bool = False) -> dict[str, object]:
    return run_demo_package_core(template, out_dir, template_roots, force=force, try_runner=run_try)


def run_publish_kit(
    out_dir: Path,
    template: str,
    template_roots: list[Path] | None = None,
    repo_slug: str = "",
    public_demo_url: str = "",
    tag: str = "v0.1.1",
    force: bool = False,
) -> dict[str, object]:
    return run_publish_kit_core(
        out_dir,
        template,
        template_roots,
        repo_slug=repo_slug,
        public_demo_url=public_demo_url,
        tag=tag,
        force=force,
        try_runner=run_try,
    )


def run_launch_kit(
    out_dir: Path,
    template: str,
    template_roots: list[Path] | None = None,
    repo_slug: str = "",
    public_demo_url: str = "",
    tag: str = "v0.1.1",
    force: bool = False,
) -> dict[str, object]:
    return run_launch_kit_core(
        out_dir,
        template,
        template_roots,
        repo_slug=repo_slug,
        public_demo_url=public_demo_url,
        tag=tag,
        force=force,
        try_runner=run_try,
    )


def run_external_evidence_template(
    out: Path,
    repo_url: str = "",
    public_demo_url: str = "",
    pypi_package_url: str = "",
    force: bool = False,
) -> dict[str, object]:
    return run_external_evidence_template_core(out, repo_url=repo_url, public_demo_url=public_demo_url, pypi_package_url=pypi_package_url, force=force)


def run_external_check(out_dir: Path, force: bool = False, evidence: Path | None = None) -> dict[str, object]:
    return run_external_check_core(out_dir, force=force, root=ROOT, evidence_path=evidence)


def cmd_static_demo(args: argparse.Namespace) -> int:
    static_summary = run_static_demo(args.template, args.out_dir, args.template_root, force=args.force)
    if args.open:
        webbrowser.open(Path(str(static_summary["index"])).resolve().as_uri())
    if args.json:
        print(json.dumps(static_summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow static-demo: {static_summary['status']}")
        print(f"Site: {static_summary['site_dir']}")
        print(f"Open: {static_summary['index']}")
        print("Host the directory with GitHub Pages, Netlify, or any static file server.")
    return 0 if static_summary["status"] == "static_demo_ready" else 2


def cmd_demo_package(args: argparse.Namespace) -> int:
    summary = run_demo_package(args.template, args.out_dir, args.template_root, force=args.force)
    if args.open:
        webbrowser.open(Path(str(summary["local_preview"])).resolve().as_uri())
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow demo-package: {summary['status']}")
        print(f"Site: {summary['site_dir']}")
        print(f"Open: {summary['local_preview']}")
        print(f"Wrote {summary['outputs']['summary']}")
        print(f"Wrote {summary['outputs']['publish_checklist']}")
    return 0 if summary["status"] == "demo_package_ready" else 2


def cmd_publish_kit(args: argparse.Namespace) -> int:
    summary = run_publish_kit(
        args.out_dir,
        args.template,
        args.template_root,
        repo_slug=args.repo_slug,
        public_demo_url=args.public_demo_url,
        tag=args.tag,
        force=args.force,
    )
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow publish-kit: {summary['status']}")
        print(f"External readiness: {summary['external_status']}")
        print(f"Repository URL: {summary['repo_url']}")
        print(f"Public demo URL: {summary['public_demo_url']}")
        print(f"Wrote {summary['outputs']['summary']}")
        print(f"Wrote {summary['outputs']['report']}")
        print(f"Wrote {summary['outputs']['github_commands']}")
    return 0 if summary["status"] == "publish_kit_ready" else 2


def cmd_launch_kit(args: argparse.Namespace) -> int:
    summary = run_launch_kit(
        args.out_dir,
        args.template,
        args.template_root,
        repo_slug=args.repo_slug,
        public_demo_url=args.public_demo_url,
        tag=args.tag,
        force=args.force,
    )
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow launch-kit: {summary['status']}")
        print(f"External readiness: {summary['external_status']}")
        print(f"Repository URL: {summary['repo_url']}")
        print(f"Public demo URL: {summary['public_demo_url']}")
        print(f"Wrote {summary['outputs']['summary']}")
        print(f"Wrote {summary['outputs']['proof_card_report']}")
        print(f"Wrote {summary['outputs']['announcement']}")
        print(f"Wrote {summary['outputs']['demo_script']}")
    return 0 if summary["status"] == "launch_kit_ready" else 2


def cmd_external_evidence(args: argparse.Namespace) -> int:
    summary = run_external_evidence_template(
        args.out,
        repo_url=args.repo_url,
        public_demo_url=args.public_demo_url,
        pypi_package_url=args.pypi_package_url,
        force=args.force,
    )
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow external-evidence: {summary['status']}")
        print(f"Wrote {summary['outputs']['evidence']}")
        print(f"Wrote {summary['outputs']['report']}")
    return 0 if summary["status"] == "external_evidence_template_ready" else 2


def cmd_external_check(args: argparse.Namespace) -> int:
    summary = run_external_check(args.out_dir, force=args.force, evidence=args.evidence)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow external-check: {summary['status']}")
        print(f"Checks: {summary['ready_check_count']}/{summary['check_count']}")
        print(f"Blockers: {summary['blocker_count']}")
        print(f"Wrote {summary['outputs']['summary']}")
        print(f"Wrote {summary['outputs']['report']}")
        for blocker in summary.get("blockers", []):
            if isinstance(blocker, dict):
                print(f"blocked: {blocker.get('check', '')}: {blocker.get('message', '')}")
    return 0 if summary["status"] == "external_ready" or not args.strict else 2


def resolve_doctor_paths(args: argparse.Namespace) -> tuple[Path | None, Path, Path, Path]:
    project_dir = args.project_dir.expanduser() if getattr(args, "project_dir", None) is not None else None
    config = args.config.expanduser() if args.config is not None else None
    evidence = args.evidence.expanduser() if args.evidence is not None else None
    out_dir = args.out_dir.expanduser() if args.out_dir is not None else None

    if project_dir is not None:
        config = config or project_dir / "project.json"
        evidence = evidence or default_project_evidence_path(project_dir)
        out_dir = out_dir or project_dir / "doctor"

    missing = []
    if config is None:
        missing.append("--config or --project-dir")
    if evidence is None:
        missing.append("--evidence or --project-dir")
    if out_dir is None:
        missing.append("--out-dir or --project-dir")
    if missing:
        raise SystemExit("Missing required doctor path(s): " + ", ".join(missing))
    return project_dir, config, evidence, out_dir


def cmd_doctor(args: argparse.Namespace) -> int:
    project_dir, config, evidence, out_dir = resolve_doctor_paths(args)
    summary = run_doctor(project_dir, config, evidence, out_dir, force=args.force)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow doctor: {summary['status']}")
        print(f"Project: {summary['project_dir']}")
        print(f"Project config: {summary['project_status']}")
        print(f"Evidence: {summary['evidence_status']}")
        print(f"Claim check: {summary['claim_check_status']}")
        print(f"Verification: {summary['verification_status']}")
        print(f"Failures: {summary['failure_count']}")
        repair_checklist = summary.get("repair_checklist", [])
        if isinstance(repair_checklist, list) and repair_checklist:
            first_repair = repair_checklist[0]
            if isinstance(first_repair, dict):
                label = "Next review" if summary["status"] == "doctor_ready" else "First repair"
                print(f"{label}: {first_repair.get('action_id', '')}")
                print(f"Run: {first_repair.get('command', '')}")
        outputs = summary.get("outputs", {})
        if isinstance(outputs, dict):
            print(f"Wrote {outputs.get('doctor_summary', '')}")
            print(f"Wrote {outputs.get('doctor_report', '')}")
            print(f"Wrote {outputs.get('claim_check', '')}")
    return 0 if summary["status"] == "doctor_ready" or not args.strict else 2


def run_demo(template: str, out_dir: Path, force: bool = False) -> dict[str, object]:
    return run_demo_core(template, out_dir, force=force)


def cmd_demo(args: argparse.Namespace) -> int:
    summary = run_demo(args.template, args.out_dir, force=args.force)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow demo: {summary['status']}")
        print(f"Template: {summary['template']}")
        print(f"Claim ready: {str(bool(summary['claim_ready'])).lower()}")
        print(f"Sources: {summary['source_status']}")
        print(f"Bundle: {summary['bundle_status']}")
        print(f"Verification: {summary['verification_status']}")
        print(f"Wrote {args.out_dir / 'demo_summary.json'}")
        print(f"Wrote {summary['bundle_zip']}")
        print(f"Wrote {summary['bundle_verification_report']}")
    return 0 if summary["status"] == "demo_ready" else 2


def cmd_next(args: argparse.Namespace) -> int:
    project = load_project(args.config)
    if args.evidence is not None and not args.evidence.exists():
        raise SystemExit(f"Evidence file does not exist: {args.evidence}")
    evidence_rows, evidence_issues = read_csv_rows_with_diagnostics(args.evidence)
    rendered = write_render_artifacts(project, evidence_rows, args.out_dir, evidence_file_issues=evidence_issues)
    for action in rendered["audit"].get("next_actions", []):
        print(f"{action['rank']}. {action['action_id']}: {action['why']}")
    print(f"Wrote {args.out_dir / 'claim_audit.md'}")
    print(f"Wrote {args.out_dir / 'audit_review.md'}")
    print(f"Wrote {args.out_dir / 'claim_summary.json'}")
    print(f"Wrote {args.out_dir / 'next_actions.json'}")
    print(f"Wrote {args.out_dir / 'dashboard.html'}")
    return 0



def cmd_sources(args: argparse.Namespace) -> int:
    project = load_project(args.config)
    if not args.evidence.exists():
        raise SystemExit(f"Evidence file does not exist: {args.evidence}")
    evidence_rows, evidence_issues = read_csv_rows_with_diagnostics(args.evidence)
    manifest = source_manifest(project, evidence_rows, evidence_issues)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    if args.report_out is not None:
        args.report_out.parent.mkdir(parents=True, exist_ok=True)
        args.report_out.write_text(render_source_manifest_report(manifest), encoding="utf-8")
    print(f"Falsiflow sources: {manifest['status']}")
    print(f"Referenced source files: {manifest['referenced_source_file_count']}")
    print(f"Present: {manifest['present_source_file_count']}")
    print(f"Missing: {manifest['missing_source_file_count']}")
    print(f"Outside allowed roots: {manifest['outside_allowed_roots_count']}")
    print(f"Blank source rows: {manifest['blank_source_row_count']}")
    print(f"Wrote {args.out}")
    if args.report_out is not None:
        print(f"Wrote {args.report_out}")
    return 0 if manifest["status"] == "sources_ready" or not args.strict else 2


def cmd_ingest_limina_source_values(args: argparse.Namespace) -> int:
    summary = write_limina_conversion(
        inputs=args.input,
        evidence_out=args.out,
        summary_out=args.summary_out,
        project_out=args.project_out,
        default_candidate=args.default_candidate,
        default_gate=args.default_gate,
        project_id=args.project_id,
        claim_id=args.claim_id,
        claim_statement=args.claim_statement,
        source_file_base_dir=args.source_file_base_dir,
        allowed_source_roots=args.allowed_source_root,
    )
    print(f"Falsiflow LIMINA ingest: {summary['status']}")
    print(f"Evidence rows: {summary['evidence_rows']}")
    print(f"Gates: {', '.join(summary['gates'])}")
    print(f"Wrote {args.out}")
    if args.project_out:
        print(f"Wrote {args.project_out}")
    if args.summary_out:
        print(f"Wrote {args.summary_out}")
    return 0


def key_record(key: tuple[str, str, str, str]) -> dict[str, str]:
    gate_id, candidate_id, sample_id, field = key
    return {
        "gate_id": gate_id,
        "candidate_id": candidate_id,
        "sample_id": sample_id,
        "field": field,
    }


def evidence_coverage_report(project: dict[str, object], evidence_rows: list[dict[str, str]]) -> dict[str, object]:
    required_keys = configured_evidence_keys(project)
    rows_by_key = evidence_rows_by_key(evidence_rows)
    imported_keys = set(rows_by_key)
    matched_keys = required_keys & imported_keys
    missing_keys = sorted(required_keys - imported_keys)
    extra_keys = sorted(imported_keys - required_keys)
    duplicate_configured_keys = sorted(key for key, rows in rows_by_key.items() if key in required_keys and len(rows) > 1)
    duplicate_extra_keys = sorted(key for key, rows in rows_by_key.items() if key not in required_keys and len(rows) > 1)

    gate_rows = []
    gate_ids = [str(gate.get("id", "")).strip() for gate in project.get("gates", []) if isinstance(gate, dict)]
    for gate_id in gate_ids:
        gate_required = {key for key in required_keys if key[0] == gate_id}
        gate_matched = gate_required & matched_keys
        gate_missing = sorted(gate_required - matched_keys)
        gate_rows.append({
            "gate_id": gate_id,
            "required_evidence_rows": len(gate_required),
            "matched_evidence_rows": len(gate_matched),
            "missing_evidence_rows": len(gate_missing),
            "completion_pct": round((len(gate_matched) / len(gate_required) * 100), 2) if gate_required else 0.0,
            "missing_keys": [key_record(key) for key in gate_missing[:50]],
        })

    blocked = bool(missing_keys or duplicate_configured_keys)
    return {
        "status": "coverage_blocked" if blocked else "coverage_ready",
        "project_id": str(project.get("project", {}).get("id", "")),
        "claim_id": str(project.get("claim", {}).get("id", "")),
        "required_evidence_rows": len(required_keys),
        "matched_evidence_rows": len(matched_keys),
        "missing_evidence_rows": len(missing_keys),
        "extra_evidence_rows": len(extra_keys),
        "duplicate_configured_keys": len(duplicate_configured_keys),
        "duplicate_extra_keys": len(duplicate_extra_keys),
        "completion_pct": round((len(matched_keys) / len(required_keys) * 100), 2) if required_keys else 0.0,
        "gates": gate_rows,
        "missing_keys": [key_record(key) for key in missing_keys[:200]],
        "extra_keys": [key_record(key) for key in extra_keys[:200]],
        "duplicate_configured": [key_record(key) for key in duplicate_configured_keys[:200]],
        "duplicate_extra": [key_record(key) for key in duplicate_extra_keys[:200]],
    }


def cmd_ingest_wide_csv(args: argparse.Namespace) -> int:
    summary = write_wide_lab_conversion(
        inputs=args.input,
        evidence_out=args.out,
        summary_out=args.summary_out,
        profile=args.profile,
        gate_id=args.gate_id,
        candidate_id=args.candidate_id,
        sample_id_column=args.sample_id_column,
        field_columns=args.field,
        exclude_columns=args.exclude_column,
        gate_id_column=args.gate_id_column,
        candidate_id_column=args.candidate_id_column,
        source_file=args.source_file,
        source_file_column=args.source_file_column,
        measured_at=args.measured_at,
        measured_at_column=args.measured_at_column,
        operator_or_agent=args.operator_or_agent,
        operator_or_agent_column=args.operator_or_agent_column,
        instrument_id=args.instrument_id,
        instrument_id_column=args.instrument_id_column,
        notes=args.notes,
        notes_column=args.notes_column,
    )
    if args.config is not None:
        project = load_project(args.config)
        evidence_rows, evidence_issues = read_csv_rows_with_diagnostics(args.out)
        coverage = evidence_coverage_report(project, evidence_rows)
        coverage["evidence_file_issue_count"] = len(evidence_issues)
        coverage["evidence_file_error_count"] = sum(1 for issue in evidence_issues if issue.get("level") == "error")
        coverage["evidence_file_warning_count"] = sum(1 for issue in evidence_issues if issue.get("level") == "warning")
        summary["coverage"] = coverage
        if args.coverage_out is not None:
            args.coverage_out.parent.mkdir(parents=True, exist_ok=True)
            args.coverage_out.write_text(json.dumps(coverage, indent=2, sort_keys=True), encoding="utf-8")
        if args.summary_out is not None:
            args.summary_out.parent.mkdir(parents=True, exist_ok=True)
            args.summary_out.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Falsiflow wide CSV ingest: {summary['status']}")
    print(f"Adapter profile: {summary.get('adapter_profile', '')}")
    print(f"Evidence rows: {summary['evidence_rows']}")
    print(f"Skipped rows: {summary['skipped_rows']}")
    print(f"Skipped blank values: {summary['skipped_values']}")
    print(f"Gates: {', '.join(summary['gates'])}")
    if "coverage" in summary:
        coverage = summary["coverage"]
        print(f"Coverage: {coverage['status']}")
        print(f"Matched: {coverage['matched_evidence_rows']} / {coverage['required_evidence_rows']}")
        print(f"Missing: {coverage['missing_evidence_rows']}")
        print(f"Extra: {coverage['extra_evidence_rows']}")
    print(f"Wrote {args.out}")
    if args.coverage_out:
        print(f"Wrote {args.coverage_out}")
    if args.summary_out:
        print(f"Wrote {args.summary_out}")
    if args.strict and summary.get("coverage", {}).get("status") == "coverage_blocked":
        return 2
    return 0


def cmd_templates(args: argparse.Namespace) -> int:
    records = template_records(args.template_root)
    if args.json:
        print(json.dumps(records, indent=2, sort_keys=True))
    else:
        for record in records:
            print(f"{record['template']}\t{record['status']}\t{record['domain']}\t{record['project_id']}")
    return 0


def run_template_gallery(
    extra_roots: list[Path] | None = None,
    include_env: bool = True,
    out: Path | None = None,
    json_out: Path | None = None,
) -> dict[str, object]:
    return run_template_gallery_core(
        extra_roots,
        include_env=include_env,
        out=out,
        json_out=json_out,
        template_records_provider=template_records,
        template_roots_provider=all_template_roots,
    )


def cmd_template_gallery(args: argparse.Namespace) -> int:
    summary = run_template_gallery(args.template_root, out=args.out, json_out=args.json_out)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow template-gallery: {summary['status']}")
        print(f"Templates: {summary['valid_template_count']}/{summary['template_count']}")
        print(f"Domains: {summary['domain_count']}")
        print(f"Non-neural templates: {summary['non_neural_template_count']}")
        print(f"Issues: {summary['issue_count']}")
        if args.out:
            print(f"Wrote {args.out}")
        if args.json_out:
            print(f"Wrote {args.json_out}")
    return 0 if summary["status"] == "template_gallery_ready" else 2


def run_casebook_check(
    artifact_root: Path,
    extra_roots: list[Path] | None = None,
    force: bool = False,
    include_env: bool = True,
) -> dict[str, object]:
    return run_casebook_check_core(
        artifact_root,
        extra_roots,
        force=force,
        include_env=include_env,
        template_records_provider=template_records,
        template_check_runner=run_template_check,
    )


def cmd_casebook_check(args: argparse.Namespace) -> int:
    summary = run_casebook_check(args.out_dir, args.template_root, force=args.force)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow casebook-check: {summary['status']}")
        print(f"Templates: {summary['ready_template_count']}/{summary['template_count']}")
        print(f"Positive demos: {summary['positive_demo_ready_count']}")
        print(f"Blocked paths: {summary['blocked_path_count']}")
        print(f"Verified bundles: {summary['bundle_verified_count']}")
        print(f"Failures: {summary['failure_count']}")
        print(f"Wrote {args.out_dir / 'casebook_check.json'}")
        print(f"Wrote {args.out_dir / 'casebook_check.md'}")
        for failure in summary["failures"]:
            print(f"failure: {failure['stage']}:{failure['id']}: {failure['message']}")
    return 0 if summary["status"] == "casebook_check_ready" else 2


def cmd_schema(args: argparse.Namespace) -> int:
    schema = falsiflow_schema(args.kind)
    payload = json.dumps(schema, indent=2, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(f"{payload}\n", encoding="utf-8")
        print(f"Wrote {args.out}")
    else:
        print(payload)
    return 0


def cmd_template_check(args: argparse.Namespace) -> int:
    summary = run_template_check(args.template_dir, args.out_dir, force=args.force)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow template-check: {summary['status']}")
        print(f"Template: {summary['template_id']}")
        print(f"Pass audit: {summary['pass_audit_status']}")
        print(f"Placeholder claim ready: {str(bool(summary['placeholder_claim_ready'])).lower()}")
        print(f"Verification: {summary['verification_status']}")
        print(f"Failures: {summary['failure_count']}")
        print(f"Wrote {args.out_dir / 'template_check.json'}")
        print(f"Wrote {args.out_dir / 'template_check.md'}")
    return 0 if summary["status"] == "template_ready" else 2


def run_template_pack(
    template_dir: Path,
    out_dir: Path,
    zip_out: Path,
    verification_out: Path | None = None,
    report_out: Path | None = None,
    force: bool = False,
) -> dict[str, object]:
    return run_template_pack_core(
        template_dir,
        out_dir,
        zip_out,
        verification_out=verification_out,
        report_out=report_out,
        force=force,
        template_check_runner=run_template_check,
    )


def cmd_template_pack(args: argparse.Namespace) -> int:
    zip_out = args.zip_out or args.out_dir.with_suffix(".zip")
    verification_out = args.verify_out or zip_out.with_suffix(".verification.json")
    report_out = args.report_out or zip_out.with_suffix(".verification.md")
    summary = run_template_pack(
        args.template_dir,
        args.out_dir,
        zip_out,
        verification_out=verification_out,
        report_out=report_out,
        force=args.force,
    )
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow template-pack: {summary['status']}")
        print(f"Template: {summary['template_id']}")
        print(f"Template check: {summary['template_check_status']}")
        print(f"Verification: {summary['verification_status']}")
        print(f"Artifacts: {summary['artifact_count']}")
        print(f"Wrote {summary['manifest_path']}")
        print(f"Wrote {summary['zip_path']}")
        print(f"Wrote {summary['verification_report_path']}")
    return 0 if summary["status"] == "template_pack_ready" else 2


def cmd_verify_template_pack(args: argparse.Namespace) -> int:
    report = verify_template_pack_zip(args.zip_path) if args.zip_path is not None else verify_template_pack(args.pack_dir)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    if args.report_out:
        args.report_out.parent.mkdir(parents=True, exist_ok=True)
        args.report_out.write_text(render_template_pack_verification_report(report), encoding="utf-8")
    print(f"Falsiflow verify-template-pack: {report['status']}")
    print(f"Integrity: {report['integrity_status']}")
    print(f"Template pack status: {report['template_pack_status']}")
    print(f"Artifacts checked: {report['checked_artifact_count']}/{report['artifact_count']}")
    print(f"Issues: {report['issue_count']}")
    if args.out:
        print(f"Wrote {args.out}")
    if args.report_out:
        print(f"Wrote {args.report_out}")
    if report["status"] == "template_pack_failed":
        return 2
    if args.strict and report["status"] != "template_pack_verified":
        return 2
    return 0


def cmd_template_registry(args: argparse.Namespace) -> int:
    registry = run_template_registry(args.pack_zip, out=args.out, report_out=args.report_out, base_url=args.base_url)
    if args.json:
        print(json.dumps(registry, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow template-registry: {registry['status']}")
        print(f"Templates: {registry['verified_template_count']}/{registry['template_count']}")
        print(f"Issues: {registry['issue_count']}")
        if args.out:
            print(f"Wrote {args.out}")
        if args.report_out:
            print(f"Wrote {args.report_out}")
    return 0 if registry["status"] == "template_registry_ready" else 2


def cmd_template_lock(args: argparse.Namespace) -> int:
    lock = run_template_lock(args.registry, args.template, version=args.version, out=args.out, cache_dir=args.cache_dir)
    if args.json:
        print(json.dumps(lock, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow template-lock: {lock['status']}")
        print(f"Template: {lock['template_id']}")
        print(f"Source SHA-256: {lock['source_sha256']}")
        print(f"Issues: {lock['issue_count']}")
        print(f"Wrote {args.out}")
    return 0 if lock["status"] == "template_locked" else 2


def cmd_template_attest(args: argparse.Namespace) -> int:
    attestation = run_template_attestation(
        args.subject,
        subject_type=args.subject_type,
        out=args.out,
        signing_key=args.signing_key,
        key_id=args.key_id,
        builder=args.builder,
    )
    if args.json:
        print(json.dumps(attestation, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow template-attest: {attestation['status']}")
        print(f"Subject: {attestation['subject_type']}")
        print(f"Subject SHA-256: {attestation['subject_sha256']}")
        print(f"Signature: {attestation['signature_type']}")
        print(f"Issues: {attestation['issue_count']}")
        print(f"Wrote {args.out}")
    return 0 if attestation["status"] == "template_attested" else 2


def cmd_verify_template_attestation(args: argparse.Namespace) -> int:
    verification = run_verify_template_attestation(args.attestation, subject_path=args.subject, signing_key=args.signing_key)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(verification, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps(verification, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow verify-template-attestation: {verification['status']}")
        print(f"Subject: {verification['subject_type']}")
        print(f"Subject SHA-256: {verification['subject_sha256']}")
        print(f"Signature verified: {str(bool(verification['signature_verified'])).lower()}")
        print(f"Issues: {verification['issue_count']}")
        if args.out:
            print(f"Wrote {args.out}")
    if verification["status"] == "template_attestation_failed":
        return 2
    if args.strict and verification["status"] != "template_attestation_verified":
        return 2
    return 0


def cmd_template_policy(args: argparse.Namespace) -> int:
    policy = run_template_policy(
        args.lock,
        args.attestation,
        out=args.out,
        signing_key=args.signing_key,
        policy_id=args.policy_id,
        owner=args.owner,
    )
    if args.json:
        print(json.dumps(policy, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow template-policy: {policy['status']}")
        print(f"Policy: {policy['policy_id']}")
        print(f"Template: {policy['template_id']}@{policy['template_version']}")
        print(f"Trusted key: {policy['trusted_key_id']}")
        print(f"Issues: {policy['issue_count']}")
        print(f"Wrote {args.out}")
    return 0 if policy["status"] == "template_policy_ready" else 2


def cmd_verify_template_policy(args: argparse.Namespace) -> int:
    verification = run_verify_template_policy(args.policy, args.lock, args.attestation, signing_key=args.signing_key)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(verification, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps(verification, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow verify-template-policy: {verification['status']}")
        print(f"Policy: {verification['policy_id']}")
        print(f"Template: {verification['template_id']}@{verification['template_version']}")
        print(f"Attestation: {verification['attestation_status']}")
        print(f"Issues: {verification['issue_count']}")
        if args.out:
            print(f"Wrote {args.out}")
    if verification["status"] == "template_policy_failed":
        return 2
    if args.strict and verification["status"] != "template_policy_verified":
        return 2
    return 0


def cmd_template_release(args: argparse.Namespace) -> int:
    summary = run_template_release(
        args.pack_zip,
        args.registry,
        args.lock,
        args.attestation,
        args.policy,
        args.out,
        signing_key=args.signing_key,
    )
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow template-release: {summary['status']}")
        print(f"Template: {summary['template_id']}@{summary['template_version']}")
        print(f"Policy: {summary['policy_verification_status']}")
        print(f"Issues: {summary['issue_count']}")
        print(f"Wrote {summary['release_zip_path']}")
    return 0 if summary["status"] == "template_release_ready" else 2


def cmd_verify_template_release(args: argparse.Namespace) -> int:
    verification = run_verify_template_release(args.release, signing_key=args.signing_key)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(verification, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.report_out:
        args.report_out.parent.mkdir(parents=True, exist_ok=True)
        args.report_out.write_text(render_template_release_verification_report(verification), encoding="utf-8")
    if args.json:
        print(json.dumps(verification, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow verify-template-release: {verification['status']}")
        print(f"Template: {verification['template_id']}@{verification['template_version']}")
        print(f"Policy: {verification['policy_verification_status']}")
        print(f"Issues: {verification['issue_count']}")
        if args.out:
            print(f"Wrote {args.out}")
        if args.report_out:
            print(f"Wrote {args.report_out}")
    if verification["status"] == "template_release_failed":
        return 2
    if args.strict and verification["status"] != "template_release_verified":
        return 2
    return 0


def run_template_install(
    zip_path: Path,
    templates_dir: Path,
    check_out_dir: Path | None = None,
    force: bool = False,
    attestation_verification: dict[str, object] | None = None,
    attestation_required: bool = False,
    policy_verification: dict[str, object] | None = None,
) -> dict[str, object]:
    return run_template_install_core(
        zip_path,
        templates_dir,
        check_out_dir=check_out_dir,
        force=force,
        attestation_verification=attestation_verification,
        attestation_required=attestation_required,
        policy_verification=policy_verification,
        template_check_runner=run_template_check,
    )


def template_install_print_context(args: argparse.Namespace) -> tuple[bool, bool, bool]:
    has_lock = args.lock_path is not None or args.release_path is not None
    show_attestation = bool(args.attestation_path is not None or args.require_attestation or args.policy_path is not None or args.release_path is not None)
    show_policy = bool(args.policy_path is not None or args.release_path is not None)
    return has_lock, show_attestation, show_policy


def print_template_install_summary(summary: dict[str, object], args: argparse.Namespace) -> None:
    has_lock, show_attestation, show_policy = template_install_print_context(args)
    print(f"Falsiflow template-install: {summary['status']}")
    if summary.get("template_id"):
        print(f"Template: {summary['template_id']}")
    if summary.get("verification_status"):
        print(f"Verification: {summary['verification_status']}")
    if summary.get("template_check_status"):
        print(f"Template check: {summary['template_check_status']}")
    if args.release_path is not None or summary.get("release_status"):
        print(f"Release: {summary.get('release_status', '')}")
    if has_lock or summary.get("lock_status"):
        print(f"Lock: {summary.get('lock_status', '')}")
    if show_attestation or summary.get("attestation_status") not in {None, "", "not_checked"}:
        print(f"Attestation: {summary.get('attestation_status', '')}")
    if show_policy or summary.get("policy_status") not in {None, "", "not_checked"}:
        print(f"Policy: {summary.get('policy_status', '')}")
    if summary.get("status") == "template_installed":
        print(f"Installed files: {summary['installed_file_count']}")
        print(f"Wrote {summary['install_dir']}")
        print(f"Wrote {summary['registry_path']}")
    else:
        print(f"Issues: {summary.get('issue_count', 0)}")


def cmd_template_install(args: argparse.Namespace) -> int:
    summary = run_template_install_workflow(
        args.zip_path,
        args.templates_dir,
        lock_path=args.lock_path,
        release_path=args.release_path,
        check_out_dir=args.check_out_dir,
        cache_dir=args.cache_dir,
        attestation_path=args.attestation_path,
        signing_key=args.signing_key,
        policy_path=args.policy_path,
        require_attestation=args.require_attestation,
        force=args.force,
        template_check_runner=run_template_check,
        release_verifier=run_verify_template_release,
        attestation_verifier=run_verify_template_attestation,
        policy_verifier=run_verify_template_policy,
    )
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print_template_install_summary(summary, args)
    return 0 if summary["status"] == "template_installed" else 2


def run_adoption_check(artifact_root: Path, run_dist: bool = False) -> dict[str, object]:
    return run_adoption_check_core(
        artifact_root,
        run_dist=run_dist,
        source_root=ROOT,
        package_checks_runner=package_release_checks,
        dist_checks_runner=dist_release_checks,
        template_gallery_runner=run_template_gallery,
        casebook_check_runner=run_casebook_check,
        quickstart_runner=run_quickstart,
        doctor_runner=run_doctor,
        default_evidence_path=default_project_evidence_path,
        template_resolver=template_path,
        claim_check_runner=run_claim_check,
    )


def cmd_adoption_check(args: argparse.Namespace) -> int:
    prepare_output_directory(args.out_dir, "adoption-check output directory", force=args.force)
    summary = run_adoption_check(args.out_dir, run_dist=not args.skip_dist)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow adoption-check: {summary['status']}")
        print(f"Priorities: {summary['ready_priority_count']}/{summary['priority_count']}")
        print(f"Readiness: {summary['readiness_pct']}%")
        print(f"Release validation: {summary['release_validation_status']}")
        print(f"Package: {summary['package_status']}")
        print(f"Distribution: {summary['dist_status']}")
        print(f"Quickstart: {summary['quickstart_status']}")
        print(f"Doctor: {summary['doctor_status']}")
        print(f"Claim check: {summary['claim_check_status']}")
        print(f"Template gallery: {summary['template_gallery_status']}")
        print(f"Casebook check: {summary['casebook_check_status']}")
        print(f"Failures: {summary['failure_count']}")
        repair_checklist = summary.get("repair_checklist", [])
        if isinstance(repair_checklist, list) and repair_checklist:
            first_repair = repair_checklist[0]
            if isinstance(first_repair, dict):
                label = "Next check" if summary["status"] == "adoption_ready" else "First repair"
                print(f"{label}: {first_repair.get('action_id', '')}")
                print(f"Run: {first_repair.get('command', '')}")
        print(f"Wrote {args.out_dir / 'adoption_check.json'}")
        print(f"Wrote {args.out_dir / 'adoption_check.md'}")
        for failure in summary["failures"]:
            print(f"failure: {failure['stage']}:{failure['id']}: {failure['message']}")
    return 0 if summary["status"] == "adoption_ready" else 2


def run_release_check(artifact_root: Path, run_dist: bool = True) -> dict[str, object]:
    return run_release_check_core(
        artifact_root,
        run_dist=run_dist,
        source_root=ROOT,
        schema_kinds=SCHEMA_KINDS,
        schema_provider=falsiflow_schema,
        template_records_provider=template_records,
        template_resolver=template_path,
        demo_runner=run_demo,
        demo_package_runner=run_demo_package,
        external_check_runner=run_external_check,
        publish_kit_runner=run_publish_kit,
        launch_kit_runner=run_launch_kit,
        quickstart_runner=run_quickstart,
        doctor_runner=run_doctor,
        default_evidence_path=default_project_evidence_path,
        claim_check_runner=run_claim_check,
        template_gallery_runner=run_template_gallery,
        casebook_check_runner=run_casebook_check,
        template_check_runner=run_template_check,
        template_pack_runner=run_template_pack,
        template_registry_runner=run_template_registry,
        template_lock_runner=run_template_lock,
        template_attestation_runner=run_template_attestation,
        verify_template_attestation_runner=run_verify_template_attestation,
        template_policy_runner=run_template_policy,
        verify_template_policy_runner=run_verify_template_policy,
        template_release_runner=run_template_release,
        verify_template_release_runner=run_verify_template_release,
        template_install_runner=run_template_install,
        read_json_object_runner=read_json_object,
        bundle_builder=build_bundle,
        bundle_zip_verifier=verify_bundle_zip,
        bundle_verification_report_renderer=render_bundle_verification_report,
        template_release_verification_report_renderer=render_template_release_verification_report,
        portfolio_writer=write_portfolio_artifacts,
        adoption_summary_builder=build_adoption_check_summary,
        adoption_artifact_writer=write_adoption_check_artifacts,
        release_validation_status_for_dist_runner=release_validation_status_for_dist,
    )


def cmd_release_check(args: argparse.Namespace) -> int:
    prepare_output_directory(args.out_dir, "release-check output directory", force=args.force)
    summary = run_release_check(args.out_dir, run_dist=not args.skip_dist)
    (args.out_dir / "release_check.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    (args.out_dir / "release_check.md").write_text(render_release_check_report(summary), encoding="utf-8")
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow release-check: {summary['status']}")
        print(f"Package: {summary['package_status']}")
        print(f"Distribution: {summary['dist_status']}")
        print(f"Release validation: {summary['release_validation_status']}")
        print(f"Demo: {summary['demo_status']}")
        print(f"Demo package: {summary['demo_package_status']}")
        print(f"Publish kit: {summary['publish_kit_status']}")
        print(f"Launch kit: {summary['launch_kit_status']}")
        print(f"External readiness: {summary['external_check_status']}")
        print(f"Schemas: {summary['schema_count']}")
        print(f"Template gallery: {summary['template_gallery_status']}")
        print(f"Casebook check: {summary['casebook_check_status']}")
        print(f"Template checks: {summary['template_check_ready_count']}/{summary['template_check_count']}")
        print(f"Template pack: {summary['template_pack_status']} / {summary['template_pack_verification_status']}")
        print(f"Template registry: {summary['template_registry_status']}")
        print(f"Template lock: {summary['template_lock_status']}")
        print(f"Template attestation: {summary['template_attestation_status']} / {summary['template_attestation_verification_status']}")
        print(f"Template policy: {summary['template_policy_status']} / {summary['template_policy_verification_status']}")
        print(f"Template release: {summary['template_release_status']} / {summary['template_release_verification_status']}")
        print(f"Template install: {summary['template_install_status']}")
        print(f"Quickstart: {summary['quickstart_status']}")
        print(f"Doctor: {summary['doctor_status']}")
        print(f"Claim check: {summary['claim_check_status']}")
        adoption_summary = summary.get("adoption_check_summary", {})
        if isinstance(adoption_summary, dict):
            print(f"Adoption check: {summary['adoption_check_status']} ({adoption_summary.get('ready_priority_count', 0)}/{adoption_summary.get('priority_count', 0)} priorities)")
            print(f"Adoption release validation: {adoption_summary.get('release_validation_status', '')}")
            repair_checklist = adoption_summary.get("repair_checklist", [])
            if isinstance(repair_checklist, list) and repair_checklist:
                first_repair = repair_checklist[0]
                if isinstance(first_repair, dict):
                    label = "Next adoption check" if summary["adoption_check_status"] == "adoption_ready" else "First adoption repair"
                    print(f"{label}: {first_repair.get('action_id', '')}")
                    print(f"Run: {first_repair.get('command', '')}")
        else:
            print(f"Adoption check: {summary['adoption_check_status']}")
        print(f"Templates: {summary['template_count']}")
        print(f"Ready audits: {summary['audit_ready_count']}")
        print(f"Verified bundles: {summary['bundle_verified_count']}")
        print(f"Failures: {summary['failure_count']}")
        print(f"Wrote {args.out_dir / 'release_check.json'}")
        print(f"Wrote {args.out_dir / 'release_check.md'}")
        print(f"Wrote {args.out_dir / 'adoption_check.json'}")
        print(f"Wrote {args.out_dir / 'adoption_check.md'}")
        for failure in summary["failures"]:
            print(f"failure: {failure['stage']}:{failure['id']}: {failure['message']}")
    return 0 if summary["status"] == "release_ready" else 2


def run_selftest(artifact_root: Path, keep_artifacts: bool) -> dict[str, object]:
    failures: list[dict[str, str]] = []
    schemas: list[dict[str, object]] = []
    for kind in SCHEMA_KINDS:
        try:
            schema = falsiflow_schema(kind)
            ok = isinstance(schema, dict) and bool(schema)
            schemas.append({"kind": kind, "status": "passed" if ok else "failed"})
            if not ok:
                failures.append({"stage": "schema", "id": kind, "message": "Schema payload was empty."})
        except Exception as exc:  # pragma: no cover - defensive CLI boundary.
            schemas.append({"kind": kind, "status": "failed"})
            failures.append({"stage": "schema", "id": kind, "message": str(exc)})

    try:
        records = template_records(include_env=False)
    except Exception as exc:  # pragma: no cover - defensive CLI boundary.
        records = []
        failures.append({"stage": "template_discovery", "id": "templates", "message": str(exc)})
    if not records:
        failures.append({"stage": "template_discovery", "id": "templates", "message": "No starter templates found."})

    templates: list[dict[str, object]] = []
    claim_summary_paths: list[Path] = []
    for record in records:
        template_id = record["template"]
        template_dir = Path(record["path"])
        config_path = Path(record["project_config"])
        evidence_path = template_dir / "evidence_pass_demo.csv"
        audit_dir = artifact_root / template_id
        template_result: dict[str, object] = {
            "template": template_id,
            "validation_status": record["status"],
            "project_id": record["project_id"],
            "audit_status": "not_run",
            "claim_ready": False,
            "audit_dir": str(audit_dir) if keep_artifacts else "",
        }

        if record["status"] != "valid":
            failures.append({
                "stage": "template_validation",
                "id": template_id,
                "message": f"Template config is {record['status']}.",
            })
            templates.append(template_result)
            continue
        if not evidence_path.exists():
            failures.append({
                "stage": "template_audit",
                "id": template_id,
                "message": "Missing evidence_pass_demo.csv.",
            })
            templates.append(template_result)
            continue

        try:
            project = load_project(config_path)
            rows, evidence_issues = read_csv_rows_with_diagnostics(evidence_path)
            rendered = write_render_artifacts(project, rows, audit_dir, evidence_file_issues=evidence_issues)
            audit = rendered["audit"]
            template_result["audit_status"] = audit["status"]
            template_result["claim_ready"] = bool(audit["claim_ready"])
            template_result["evidence_error_count"] = audit["evidence_error_count"]
            template_result["evidence_warning_count"] = audit["evidence_warning_count"]
            if audit["claim_ready"]:
                claim_summary_paths.append(audit_dir / "claim_summary.json")
            else:
                failures.append({
                    "stage": "template_audit",
                    "id": template_id,
                    "message": f"Demo audit ended as {audit['status']}.",
                })
        except Exception as exc:  # pragma: no cover - defensive CLI boundary.
            template_result["audit_status"] = "failed"
            failures.append({"stage": "template_audit", "id": template_id, "message": str(exc)})
        templates.append(template_result)

    portfolio: dict[str, object] | None = None
    if claim_summary_paths:
        try:
            portfolio_dir = artifact_root / "portfolio"
            portfolio = write_portfolio_artifacts(claim_summary_paths, portfolio_dir)
            if portfolio["blocked_count"] != 0:
                failures.append({
                    "stage": "portfolio",
                    "id": "starter_templates",
                    "message": f"Portfolio has {portfolio['blocked_count']} blocked claim(s).",
                })
        except Exception as exc:  # pragma: no cover - defensive CLI boundary.
            failures.append({"stage": "portfolio", "id": "starter_templates", "message": str(exc)})
    else:
        failures.append({
            "stage": "portfolio",
            "id": "starter_templates",
            "message": "No ready template audit summaries were produced.",
        })

    audit_ready_count = sum(1 for template in templates if template.get("claim_ready") is True)
    summary: dict[str, object] = {
        "status": "passed" if not failures else "failed",
        "schema_count": len(schemas),
        "schemas": schemas,
        "template_count": len(templates),
        "audit_ready_count": audit_ready_count,
        "failure_count": len(failures),
        "failures": failures,
        "templates": templates,
        "portfolio_status": portfolio["status"] if portfolio else "not_run",
        "portfolio_claim_count": portfolio["claim_count"] if portfolio else 0,
        "artifact_root": str(artifact_root) if keep_artifacts else "",
    }
    return summary


def cmd_selftest(args: argparse.Namespace) -> int:
    if args.out_dir:
        args.out_dir.mkdir(parents=True, exist_ok=True)
        summary = run_selftest(args.out_dir, keep_artifacts=True)
    else:
        with tempfile.TemporaryDirectory(prefix="falsiflow_selftest_") as tmp:
            summary = run_selftest(Path(tmp), keep_artifacts=False)

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Falsiflow selftest: {summary['status']}")
        print(f"Schemas: {summary['schema_count']}")
        print(f"Templates: {summary['template_count']}")
        print(f"Ready demo audits: {summary['audit_ready_count']}")
        print(f"Portfolio: {summary['portfolio_status']}")
        if summary["artifact_root"]:
            print(f"Wrote {summary['artifact_root']}")
        for failure in summary["failures"]:
            print(f"failure: {failure['stage']}:{failure['id']}: {failure['message']}")
    return 0 if summary["status"] == "passed" else 2


def cmd_validate(args: argparse.Namespace) -> int:
    project = load_project(args.config)
    validation = validate_project_config(project)
    print(f"Falsiflow validate: {validation['status']}")
    print(f"Errors: {validation['error_count']}")
    print(f"Warnings: {validation['warning_count']}")
    for issue in validation.get("issues", []):
        print(f"{issue['level']}: {issue['path']}: {issue['message']}")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(validation, indent=2, sort_keys=True), encoding="utf-8")
        print(f"Wrote {args.out}")
    return 0 if validation["valid"] or not args.strict else 2


def cmd_portfolio(args: argparse.Namespace) -> int:
    inputs = args.input or [Path.cwd() / "data" / "falsiflow"]
    summary_paths = discover_claim_summary_paths(inputs)
    if not summary_paths:
        raise SystemExit("No claim_summary.json files found.")
    portfolio = write_portfolio_artifacts(summary_paths, args.out_dir)
    print(f"Falsiflow portfolio: {portfolio['status']}")
    print(f"Claims: {portfolio['claim_count']}")
    print(f"Ready: {portfolio['ready_count']}")
    print(f"Blocked: {portfolio['blocked_count']}")
    print(f"Wrote {args.out_dir / 'portfolio_summary.json'}")
    print(f"Wrote {args.out_dir / 'portfolio_summary.md'}")
    print(f"Wrote {args.out_dir / 'portfolio_dashboard.html'}")
    return 0 if portfolio["blocked_count"] == 0 or not args.strict else 2


def add_discovery_arguments(target: argparse.ArgumentParser, default_out_dir: Path = Path("falsiflow_discovery")) -> None:
    target.add_argument("--goal", required=True, help="Research goal to turn into evidence records, candidates, gates, and an assay plan.")
    target.add_argument("--out-dir", type=Path, default=default_out_dir, help="Directory for discovery artifacts.")
    target.add_argument("--force", action="store_true", help="Allow replacing an existing discovery directory.")
    target.add_argument("--json", action="store_true", help="Print machine-readable discovery summary.")


def add_wide_csv_arguments(target: argparse.ArgumentParser) -> None:
    target.add_argument("--input", type=Path, action="append", required=True, help="Wide lab CSV. Repeatable.")
    target.add_argument("--out", type=Path, required=True, help="Falsiflow evidence CSV to write.")
    target.add_argument("--summary-out", type=Path, help="Optional conversion summary JSON.")
    target.add_argument("--config", type=Path, help="Optional project config for import coverage precheck.")
    target.add_argument("--coverage-out", type=Path, help="Optional coverage precheck JSON output path.")
    target.add_argument("--strict", action="store_true", help="Exit non-zero when project coverage is blocked.")
    target.add_argument("--profile", choices=adapter_profile_names(), default="generic-wide", help="Column mapping profile for common lab, vendor, or instrument CSV shapes.")
    target.add_argument("--gate-id", required=True)
    target.add_argument("--candidate-id", required=True)
    target.add_argument("--sample-id-column", default="", help="Column containing sample ids. Defaults to the selected profile.")
    target.add_argument("--field", action="append", default=[], help="Value column to import. Repeatable. Defaults to all non-metadata columns.")
    target.add_argument("--exclude-column", action="append", default=[], help="Column to ignore when auto-selecting value columns.")
    target.add_argument("--gate-id-column", default="")
    target.add_argument("--candidate-id-column", default="")
    target.add_argument("--source-file", default="")
    target.add_argument("--source-file-column", default="")
    target.add_argument("--measured-at", default="")
    target.add_argument("--measured-at-column", default="")
    target.add_argument("--operator-or-agent", default="")
    target.add_argument("--operator-or-agent-column", default="")
    target.add_argument("--instrument-id", default="")
    target.add_argument("--instrument-id-column", default="")
    target.add_argument("--notes", default="")
    target.add_argument("--notes-column", default="")


def is_subparser_action(action: argparse.Action) -> bool:
    return isinstance(action, argparse._SubParsersAction)


def subparser_help(action: argparse._SubParsersAction, name: str) -> str:
    for choice in action._choices_actions:
        if choice.dest == name:
            return str(choice.help or "")
    return ""


def action_value_label(action: argparse.Action) -> str:
    if getattr(action, "nargs", None) == 0:
        return ""
    if action.metavar:
        return str(action.metavar)
    if action.choices:
        return "{" + ",".join(str(choice) for choice in action.choices) + "}"
    return action.dest.upper()


def cli_argument_record(action: argparse.Action) -> dict[str, object] | None:
    if action.dest in {"help", "func"} or is_subparser_action(action):
        return None
    names = list(action.option_strings) if action.option_strings else [action.metavar or action.dest]
    default = getattr(action, "default", None)
    if default is argparse.SUPPRESS or default is None:
        default_text = ""
    else:
        default_text = str(default)
    return {
        "names": names,
        "value": action_value_label(action),
        "required": bool(getattr(action, "required", False) or not action.option_strings),
        "default": default_text,
        "choices": [str(choice) for choice in action.choices] if action.choices else [],
        "help": str(action.help or ""),
    }


def parser_command_records(parser: argparse.ArgumentParser, prefix: tuple[str, ...] = ()) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for action in parser._actions:
        if not is_subparser_action(action):
            continue
        for name, subparser in action.choices.items():
            command = (*prefix, name)
            child_records = parser_command_records(subparser, command)
            options = [
                record
                for record in (cli_argument_record(child_action) for child_action in subparser._actions)
                if record is not None
            ]
            records.append({
                "command": " ".join(command),
                "help": subparser_help(action, name),
                "usage": subparser.format_usage().replace("usage: ", "").strip(),
                "options": options,
                "children": [str(child["command"]) for child in child_records],
            })
            records.extend(child_records)
    return records


def cli_command_category(command: str) -> str:
    root = command.split()[0]
    if root in {"start", "onboard", "try", "serve", "wizard", "quickstart", "doctor"}:
        return "First-run and browser workflows"
    if root in {"discover", "agent", "candidate", "assay-plan", "evidence", "ingest-wide-csv", "ingest-limina-source-values"}:
        return "Discovery and evidence import"
    if root in {"template-scaffold", "templates", "template-gallery", "template-check", "template-pack", "verify-template-pack", "template-registry", "template-lock", "template-attest", "verify-template-attestation", "template-policy", "verify-template-policy", "template-release", "verify-template-release", "template-install"}:
        return "Template supply chain"
    if root in {"static-demo", "demo-package", "publish-kit", "launch-kit", "casebook-check", "external-evidence", "external-check", "adoption-check", "release-check", "selftest", "schema", "cli-reference"}:
        return "Release and public adoption"
    if root in {"validate", "render", "audit", "claim-check", "bundle", "verify-bundle", "next", "sources", "portfolio", "demo"}:
        return "Core audit and bundle operations"
    return "Project setup"


def build_cli_reference(parser: argparse.ArgumentParser) -> dict[str, object]:
    commands = parser_command_records(parser)
    categories: dict[str, list[str]] = {}
    for record in commands:
        command = str(record["command"])
        categories.setdefault(cli_command_category(command), []).append(command)
    return {
        "status": "cli_reference_ready",
        "command_count": len(commands),
        "categories": categories,
        "commands": commands,
    }


def render_cli_reference_markdown(reference: dict[str, object]) -> str:
    commands = [record for record in reference.get("commands", []) if isinstance(record, dict)]
    categories = reference.get("categories", {}) if isinstance(reference.get("categories"), dict) else {}
    lines = [
        "# Falsiflow CLI Reference",
        "",
        "This reference is generated from the active `argparse` command tree.",
        "",
        f"- Status: `{reference.get('status', '')}`",
        f"- Commands: {reference.get('command_count', 0)}",
        "",
        "Regenerate it with:",
        "",
        "```bash",
        "falsiflow cli-reference --out docs/falsiflow_cli_reference.md",
        "```",
        "",
        "## Command Families",
        "",
    ]
    for category in sorted(categories):
        values = categories.get(category, [])
        if not isinstance(values, list):
            continue
        joined = ", ".join(f"`falsiflow {command}`" for command in values)
        lines.append(f"- {category}: {joined}")
    lines.extend(["", "## Command Index", "", "| Command | Summary |", "| --- | --- |"])
    for record in commands:
        lines.append(f"| `falsiflow {record.get('command', '')}` | {record.get('help', '')} |")
    lines.extend(["", "## Commands", ""])
    for record in commands:
        lines.extend([
            f"### `falsiflow {record.get('command', '')}`",
            "",
            str(record.get("help", "")),
            "",
            "```text",
            str(record.get("usage", "")),
            "```",
            "",
        ])
        children = record.get("children", [])
        if isinstance(children, list) and children:
            lines.append("Nested commands:")
            for child in children:
                lines.append(f"- `falsiflow {child}`")
            lines.append("")
        options = record.get("options", [])
        if isinstance(options, list) and options:
            lines.extend(["| Argument | Value | Required | Default | Help |", "| --- | --- | --- | --- | --- |"])
            for option in options:
                if not isinstance(option, dict):
                    continue
                names = option.get("names", [])
                names_text = ", ".join(str(name) for name in names) if isinstance(names, list) else str(names)
                lines.append(
                    "| "
                    + " | ".join([
                        f"`{names_text}`",
                        f"`{option.get('value', '')}`",
                        "`yes`" if option.get("required") else "`no`",
                        f"`{option.get('default', '')}`",
                        str(option.get("help", "")).replace("|", "\\|"),
                    ])
                    + " |"
                )
            lines.append("")
        else:
            lines.append("No command-specific arguments.")
            lines.append("")
    return "\n".join(lines)


def cmd_cli_reference(args: argparse.Namespace) -> int:
    reference = build_cli_reference(build_parser())
    markdown = render_cli_reference_markdown(reference)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(f"{markdown}\n", encoding="utf-8")
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(reference, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps(reference, indent=2, sort_keys=True))
    elif args.out:
        print(f"Falsiflow cli-reference: {reference['status']}")
        print(f"Commands: {reference['command_count']}")
        print(f"Wrote {args.out}")
        if args.json_out:
            print(f"Wrote {args.json_out}")
    else:
        print(markdown)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="falsiflow", description="Evidence-gated R&D workflow engine.")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Copy a starter Falsiflow template.")
    init.add_argument("--template", default="neural_materials")
    init.add_argument("--template-root", type=Path, action="append", default=[], help="Extra template root to search before bundled templates. Repeatable.")
    init.add_argument("--out", type=Path, required=True)
    init.set_defaults(func=cmd_init)

    start = sub.add_parser("start", help="Open the beginner-friendly local Falsiflow app.")
    start.add_argument("--template", default="biointerface_coatings", help="Starter example to show. Defaults to biointerface_coatings.")
    start.add_argument("--template-root", type=Path, action="append", default=[], help="Extra template root to search before bundled templates. Repeatable.")
    start.add_argument("--out-dir", type=Path, default=Path("falsiflow_start"), help="Directory for the local app files.")
    start.add_argument("--host", default="127.0.0.1", help="Host interface for the local server.")
    start.add_argument("--port", type=int, default=0, help="Port for the local app. Defaults to a free port.")
    start.add_argument("--reset", action="store_true", help="Regenerate the local app output directory before opening it.")
    start.add_argument("--no-open", action="store_true", help="Do not open the browser automatically.")
    start.add_argument("--check", action="store_true", help="Start the server, fetch index.html once, write serve_summary.json, and exit.")
    start.add_argument("--json", action="store_true", help="Print machine-readable local app summary.")
    start.set_defaults(func=cmd_start)

    onboard = sub.add_parser("onboard", help="Run the beginner onboarding check and write next-step guidance.")
    onboard.add_argument("--template", default="biointerface_coatings", help="Starter example to show. Defaults to biointerface_coatings.")
    onboard.add_argument("--template-root", type=Path, action="append", default=[], help="Extra template root to search before bundled templates. Repeatable.")
    onboard.add_argument("--out-dir", type=Path, default=Path("falsiflow_onboard"), help="Directory for onboarding files.")
    onboard.add_argument("--host", default="127.0.0.1", help="Host interface for the local check server.")
    onboard.add_argument("--port", type=int, default=0, help="Port for the local check server. Defaults to a free port.")
    onboard.add_argument("--reset", action="store_true", help="Regenerate the onboarding output directory before checking it.")
    onboard.add_argument("--no-open", action="store_true", help="Do not open the browser after onboarding.")
    onboard.add_argument("--check", action="store_true", help="Run the onboarding HTTP check and exit.")
    onboard.add_argument("--json", action="store_true", help="Print machine-readable onboarding summary.")
    onboard.set_defaults(func=cmd_onboard)

    static_demo = sub.add_parser("static-demo", help="Export a hostable static demo site for zero-install visitors.")
    static_demo.add_argument("--template", default="biointerface_coatings", help="Starter template to export. Defaults to biointerface_coatings.")
    static_demo.add_argument("--template-root", type=Path, action="append", default=[], help="Extra template root to search before bundled templates. Repeatable.")
    static_demo.add_argument("--out-dir", type=Path, default=Path("falsiflow_static_demo"), help="Directory for static demo files.")
    static_demo.add_argument("--force", action="store_true", help="Allow replacing an existing static demo directory.")
    static_demo.add_argument("--open", action="store_true", help="Open the exported index.html in the default browser.")
    static_demo.add_argument("--json", action="store_true", help="Print machine-readable static demo summary.")
    static_demo.set_defaults(func=cmd_static_demo)

    demo_package = sub.add_parser("demo-package", help="Prepare a GitHub Pages/Netlify-ready static demo package.")
    demo_package.add_argument("--template", default="biointerface_coatings", help="Starter template to export. Defaults to biointerface_coatings.")
    demo_package.add_argument("--template-root", type=Path, action="append", default=[], help="Extra template root to search before bundled templates. Repeatable.")
    demo_package.add_argument("--out-dir", type=Path, default=Path("falsiflow_public_demo"), help="Directory for publishable demo files.")
    demo_package.add_argument("--force", action="store_true", help="Allow replacing an existing demo package directory.")
    demo_package.add_argument("--open", action="store_true", help="Open the exported index.html in the default browser.")
    demo_package.add_argument("--json", action="store_true", help="Print machine-readable demo package summary.")
    demo_package.set_defaults(func=cmd_demo_package)

    publish_kit = sub.add_parser("publish-kit", help="Generate a local handoff kit for GitHub Pages, external readiness, and PyPI release steps.")
    publish_kit.add_argument("--template", default="biointerface_coatings", help="Starter template to export in the public demo package.")
    publish_kit.add_argument("--template-root", type=Path, action="append", default=[], help="Extra template root to search before bundled templates. Repeatable.")
    publish_kit.add_argument("--out-dir", type=Path, default=Path("falsiflow_publish_kit"), help="Directory for publish handoff artifacts.")
    publish_kit.add_argument("--repo-slug", default="", help="Optional GitHub repo slug such as OWNER/falsiflow.")
    publish_kit.add_argument("--public-demo-url", default="", help="Optional hosted public demo URL.")
    publish_kit.add_argument("--tag", default="v0.1.1", help="Release tag to include in generated GitHub commands.")
    publish_kit.add_argument("--force", action="store_true", help="Allow replacing an existing publish-kit directory.")
    publish_kit.add_argument("--json", action="store_true", help="Print machine-readable publish handoff summary.")
    publish_kit.set_defaults(func=cmd_publish_kit)

    launch_kit = sub.add_parser("launch-kit", help="Generate public launch copy, demo script, proof card, and maintainer checklist.")
    launch_kit.add_argument("--template", default="biointerface_coatings", help="Starter template to use in the nested public demo package.")
    launch_kit.add_argument("--template-root", type=Path, action="append", default=[], help="Extra template root to search before bundled templates. Repeatable.")
    launch_kit.add_argument("--out-dir", type=Path, default=Path("falsiflow_launch_kit"), help="Directory for public launch materials.")
    launch_kit.add_argument("--repo-slug", default="", help="Optional GitHub repo slug such as OWNER/falsiflow.")
    launch_kit.add_argument("--public-demo-url", default="", help="Optional hosted public demo URL.")
    launch_kit.add_argument("--tag", default="v0.1.1", help="Release tag to include in launch materials.")
    launch_kit.add_argument("--force", action="store_true", help="Allow replacing an existing launch-kit directory.")
    launch_kit.add_argument("--json", action="store_true", help="Print machine-readable launch kit summary.")
    launch_kit.set_defaults(func=cmd_launch_kit)

    external_evidence = sub.add_parser("external-evidence", help="Write a structured JSON template for hosted demo, PyPI, pipx, and Windows validation evidence.")
    external_evidence.add_argument("--out", type=Path, default=Path("falsiflow_external_evidence.json"), help="Path for the external evidence JSON template.")
    external_evidence.add_argument("--repo-url", default="", help="Optional public repository URL to prefill.")
    external_evidence.add_argument("--public-demo-url", default="", help="Optional hosted public demo URL to prefill.")
    external_evidence.add_argument("--pypi-package-url", default="", help="Optional public PyPI project URL to prefill.")
    external_evidence.add_argument("--force", action="store_true", help="Allow replacing an existing external evidence file.")
    external_evidence.add_argument("--json", action="store_true", help="Print machine-readable external evidence summary.")
    external_evidence.set_defaults(func=cmd_external_evidence)

    external_check = sub.add_parser("external-check", help="Check public release dependencies such as hosted demo URL, repo URL, PyPI package URL, pipx, and Windows validation.")
    external_check.add_argument("--out-dir", type=Path, default=Path("falsiflow_external_check"), help="Directory for external readiness artifacts.")
    external_check.add_argument("--evidence", type=Path, default=None, help="Optional structured external evidence JSON from `falsiflow external-evidence`.")
    external_check.add_argument("--force", action="store_true", help="Allow replacing an existing external-check directory.")
    external_check.add_argument("--strict", action="store_true", help="Exit non-zero unless every external readiness check passes.")
    external_check.add_argument("--json", action="store_true", help="Print machine-readable external readiness summary.")
    external_check.set_defaults(func=cmd_external_check)

    discover = sub.add_parser("discover", help="Generate a structured, non-AI discovery candidate queue and project draft.")
    add_discovery_arguments(discover)
    discover.set_defaults(func=cmd_discover)

    agent = sub.add_parser("agent", help="Optional agent interfaces that still emit auditable Falsiflow artifacts.")
    agent_sub = agent.add_subparsers(dest="agent_command", required=True)
    agent_discover = agent_sub.add_parser("discover", help="Generate a structured discovery package through the agent-facing interface.")
    add_discovery_arguments(agent_discover)
    agent_discover.set_defaults(func=cmd_agent_discover)

    candidate = sub.add_parser("candidate", help="Candidate queue utilities.")
    candidate_sub = candidate.add_subparsers(dest="candidate_command", required=True)
    candidate_rank = candidate_sub.add_parser("rank", help="Rank candidate recipes for a research goal and write ranking artifacts.")
    add_discovery_arguments(candidate_rank, default_out_dir=Path("falsiflow_candidate_rank"))
    candidate_rank.set_defaults(func=cmd_candidate_rank)

    assay_plan = sub.add_parser("assay-plan", help="Draft assay and RFQ packages for the top candidate from a research goal.")
    add_discovery_arguments(assay_plan, default_out_dir=Path("falsiflow_assay_plan"))
    assay_plan.set_defaults(func=cmd_assay_plan)

    evidence = sub.add_parser("evidence", help="Evidence import utilities.")
    evidence_sub = evidence.add_subparsers(dest="evidence_command", required=True)
    evidence_import = evidence_sub.add_parser("import", help="Convert a wide lab CSV into Falsiflow evidence rows.")
    add_wide_csv_arguments(evidence_import)
    evidence_import.set_defaults(func=cmd_ingest_wide_csv)

    try_cmd = sub.add_parser("try", help="Run a 30-second starter demo and write a local browser launchpad.")
    try_cmd.add_argument("--template", default="biointerface_coatings", help="Starter template to run. Defaults to biointerface_coatings.")
    try_cmd.add_argument("--template-root", type=Path, action="append", default=[], help="Extra template root to search before bundled templates. Repeatable.")
    try_cmd.add_argument("--out-dir", type=Path, default=Path("falsiflow_try"), help="Directory for the demo project, JSON, launchpad, and HTML report.")
    try_cmd.add_argument("--force", action="store_true", help="Allow replacing an existing try output directory.")
    try_cmd.add_argument("--open", action="store_true", help="Open the local launchpad in the default browser after writing it.")
    try_cmd.add_argument("--strict", action="store_true", help="Exit non-zero unless the starter claim is ready.")
    try_cmd.add_argument("--json", action="store_true", help="Print machine-readable try summary.")
    try_cmd.set_defaults(func=cmd_try)

    wizard = sub.add_parser("wizard", help="Write a static browser wizard for drafting a claim gate.")
    wizard.add_argument("--out", type=Path, default=Path("falsiflow_wizard.html"), help="HTML wizard file to write.")
    wizard.add_argument("--force", action="store_true", help="Allow replacing an existing wizard HTML file.")
    wizard.add_argument("--open", action="store_true", help="Open the wizard in the default browser after writing it.")
    wizard.add_argument("--json", action="store_true", help="Print machine-readable wizard summary.")
    wizard.set_defaults(func=cmd_wizard)

    serve = sub.add_parser("serve", help="Generate and serve the local Falsiflow browser demo on localhost.")
    serve.add_argument("--template", default="biointerface_coatings", help="Starter template to run when generating the demo.")
    serve.add_argument("--template-root", type=Path, action="append", default=[], help="Extra template root to search before bundled templates. Repeatable.")
    serve.add_argument("--out-dir", type=Path, default=Path("falsiflow_try"), help="Directory containing or receiving index.html and try_report.html.")
    serve.add_argument("--host", default="127.0.0.1", help="Host interface for the local server.")
    serve.add_argument("--port", type=int, default=8765, help="Port for the local server. Use 0 to choose a free port.")
    serve.add_argument("--force", action="store_true", help="Regenerate the try output directory before serving.")
    serve.add_argument("--open", action="store_true", help="Open the local demo URL in the default browser.")
    serve.add_argument("--check", action="store_true", help="Start the server, fetch index.html once, write serve_summary.json, and exit.")
    serve.add_argument("--json", action="store_true", help="Print machine-readable serve summary.")
    serve.set_defaults(func=cmd_serve)

    quickstart = sub.add_parser("quickstart", help="Create a starter project and immediately run the one-command claim gate.")
    quickstart.add_argument("--template", default="neural_materials")
    quickstart.add_argument("--template-root", type=Path, action="append", default=[], help="Extra template root to search before bundled templates. Repeatable.")
    quickstart.add_argument("--out", type=Path, required=True, help="Project directory to create.")
    quickstart.add_argument("--force", action="store_true", help="Allow replacing an existing quickstart project directory.")
    quickstart.add_argument("--strict", action="store_true", help="Exit non-zero unless the quickstart claim check is ready.")
    quickstart.add_argument("--json", action="store_true", help="Print machine-readable quickstart summary.")
    quickstart.set_defaults(func=cmd_quickstart)

    doctor = sub.add_parser("doctor", help="Diagnose a project directory and run the complete claim gate with actionable next steps.")
    doctor.add_argument("--project-dir", type=Path, help="Project directory containing project.json and an evidence CSV; defaults --out-dir to PROJECT_DIR/doctor.")
    doctor.add_argument("--config", type=Path, help="Project config JSON path. Defaults to PROJECT_DIR/project.json when --project-dir is used.")
    doctor.add_argument("--evidence", type=Path, help="Evidence CSV path. Defaults to PROJECT_DIR/evidence_pass_demo.csv, evidence.csv, or evidence_template.csv when --project-dir is used.")
    doctor.add_argument("--out-dir", type=Path, help="Output directory. Defaults to PROJECT_DIR/doctor when --project-dir is used.")
    doctor.add_argument("--force", action="store_true", help="Allow writing into a non-empty doctor output directory.")
    doctor.add_argument("--strict", action="store_true", help="Exit non-zero unless the doctor summary is ready.")
    doctor.add_argument("--json", action="store_true", help="Print machine-readable doctor summary.")
    doctor.set_defaults(func=cmd_doctor)

    scaffold = sub.add_parser("scaffold", help="Create a custom Falsiflow project from gates and fields.")
    scaffold.add_argument("--out", type=Path, required=True, help="Directory to create.")
    scaffold.add_argument("--project-id", required=True)
    scaffold.add_argument("--project-name", default="")
    scaffold.add_argument("--domain", default="custom-rd")
    scaffold.add_argument("--claim-id", required=True)
    scaffold.add_argument("--claim-statement", required=True)
    scaffold.add_argument(
        "--gate",
        action="append",
        required=True,
        help="Gate definition as `gate_id:field_a,field_b`. Repeatable.",
    )
    scaffold.add_argument("--gate-title", action="append", default=[], help="Optional title as `gate_id=Human title`. Repeatable.")
    scaffold.add_argument(
        "--sample",
        action="append",
        default=[],
        help="Sample as `candidate_id:sample_id` for all gates, or `gate_id:candidate_id:sample_id`. Repeatable.",
    )
    scaffold.add_argument(
        "--rule",
        action="append",
        default=[],
        help="Acceptance rule as `gate_id:field:operator:value[:reason]`. Repeatable.",
    )
    scaffold.add_argument("--candidate-id", default="candidate_a", help="Default candidate_id when --sample is omitted.")
    scaffold.add_argument("--sample-id", default="sample_001", help="Default sample_id when --sample is omitted.")
    scaffold.add_argument("--json", action="store_true", help="Print machine-readable scaffold summary.")
    scaffold.set_defaults(func=cmd_scaffold)

    template_scaffold = sub.add_parser("template-scaffold", help="Create a reusable starter template with pass and placeholder demos.")
    template_scaffold.add_argument("--out", type=Path, required=True, help="Template directory to create.")
    template_scaffold.add_argument("--template-id", required=True)
    template_scaffold.add_argument("--template-name", default="")
    template_scaffold.add_argument("--template-description", default="")
    template_scaffold.add_argument("--project-id", default="")
    template_scaffold.add_argument("--project-name", default="")
    template_scaffold.add_argument("--domain", default="custom-rd")
    template_scaffold.add_argument("--claim-id", default="")
    template_scaffold.add_argument("--claim-statement", required=True)
    template_scaffold.add_argument(
        "--gate",
        action="append",
        required=True,
        help="Gate definition as `gate_id:field_a,field_b`. Repeatable.",
    )
    template_scaffold.add_argument("--gate-title", action="append", default=[], help="Optional title as `gate_id=Human title`. Repeatable.")
    template_scaffold.add_argument(
        "--sample",
        action="append",
        default=[],
        help="Sample as `candidate_id:sample_id` for all gates, or `gate_id:candidate_id:sample_id`. Repeatable.",
    )
    template_scaffold.add_argument(
        "--rule",
        action="append",
        default=[],
        help="Acceptance rule as `gate_id:field:operator:value[:reason]`. Repeatable.",
    )
    template_scaffold.add_argument("--candidate-id", default="candidate_a", help="Default candidate_id when --sample is omitted.")
    template_scaffold.add_argument("--sample-id", default="sample_001", help="Default sample_id when --sample is omitted.")
    template_scaffold.add_argument("--check-out-dir", type=Path, help="Optional directory for template-check artifacts.")
    template_scaffold.add_argument("--force", action="store_true", help="Allow replacing a non-empty template or check output directory.")
    template_scaffold.add_argument("--json", action="store_true", help="Print machine-readable template-scaffold summary.")
    template_scaffold.set_defaults(func=cmd_template_scaffold)

    templates = sub.add_parser("templates", help="List available starter templates.")
    templates.add_argument("--template-root", type=Path, action="append", default=[], help="Extra template root to list before bundled templates. Repeatable.")
    templates.add_argument("--json", action="store_true", help="Print machine-readable template metadata.")
    templates.set_defaults(func=cmd_templates)

    template_gallery = sub.add_parser("template-gallery", help="Write a Markdown and JSON gallery of starter template use cases.")
    template_gallery.add_argument("--template-root", type=Path, action="append", default=[], help="Extra template root to include before bundled templates. Repeatable.")
    template_gallery.add_argument("--out", type=Path, help="Optional Markdown gallery output path.")
    template_gallery.add_argument("--json-out", type=Path, help="Optional JSON gallery output path.")
    template_gallery.add_argument("--json", action="store_true", help="Print machine-readable template-gallery summary.")
    template_gallery.set_defaults(func=cmd_template_gallery)

    casebook_check = sub.add_parser("casebook-check", help="Verify public casebook starter proofs and blocked-path demos.")
    casebook_check.add_argument("--template-root", type=Path, action="append", default=[], help="Extra template root to include before bundled templates. Repeatable.")
    casebook_check.add_argument("--out-dir", type=Path, required=True, help="Directory for casebook-check artifacts and reports.")
    casebook_check.add_argument("--json", action="store_true", help="Print machine-readable casebook-check summary.")
    casebook_check.add_argument("--force", action="store_true", help="Allow writing into a non-empty casebook-check directory.")
    casebook_check.set_defaults(func=cmd_casebook_check)

    cli_reference = sub.add_parser("cli-reference", help="Generate the Markdown and JSON command reference from argparse.")
    cli_reference.add_argument("--out", type=Path, help="Optional Markdown reference output path.")
    cli_reference.add_argument("--json-out", type=Path, help="Optional JSON reference output path.")
    cli_reference.add_argument("--json", action="store_true", help="Print machine-readable CLI reference summary.")
    cli_reference.set_defaults(func=cmd_cli_reference)

    schema = sub.add_parser("schema", help="Print machine-readable Falsiflow JSON Schemas.")
    schema.add_argument("--kind", choices=SCHEMA_KINDS, default="project")
    schema.add_argument("--out", type=Path, help="Optional JSON output path.")
    schema.set_defaults(func=cmd_schema)

    selftest = sub.add_parser("selftest", help="Verify packaged schemas, templates, demo audits, and portfolio output.")
    selftest.add_argument("--out-dir", type=Path, help="Optional directory for selftest artifacts.")
    selftest.add_argument("--json", action="store_true", help="Print machine-readable selftest results.")
    selftest.set_defaults(func=cmd_selftest)

    demo = sub.add_parser("demo", help="Run the end-to-end starter walkthrough and produce a verified bundle.")
    demo.add_argument("--out-dir", type=Path, required=True, help="Directory for demo project and artifacts.")
    demo.add_argument("--template", default="neural_materials", help="Starter template to run. Defaults to neural_materials.")
    demo.add_argument("--json", action="store_true", help="Print machine-readable demo summary.")
    demo.add_argument("--force", action="store_true", help="Allow replacing a non-empty demo output directory.")
    demo.set_defaults(func=cmd_demo)

    template_check = sub.add_parser("template-check", help="Validate an external or bundled starter template end to end.")
    template_check.add_argument("--template-dir", type=Path, required=True, help="Directory containing template.json, project.json, evidence demos, and source_files/.")
    template_check.add_argument("--out-dir", type=Path, required=True, help="Directory for template-check artifacts and reports.")
    template_check.add_argument("--json", action="store_true", help="Print machine-readable template-check summary.")
    template_check.add_argument("--force", action="store_true", help="Allow writing into a non-empty template-check directory.")
    template_check.set_defaults(func=cmd_template_check)

    template_pack = sub.add_parser("template-pack", help="Package a checked starter template into a verifiable zip artifact.")
    template_pack.add_argument("--template-dir", type=Path, required=True, help="Template directory to package.")
    template_pack.add_argument("--out-dir", type=Path, required=True, help="Directory for the unpacked template pack.")
    template_pack.add_argument("--zip-out", type=Path, help="Zip archive path. Defaults to OUT_DIR with .zip suffix.")
    template_pack.add_argument("--verify-out", type=Path, help="Optional JSON verification output path. Defaults next to the zip.")
    template_pack.add_argument("--report-out", type=Path, help="Optional Markdown verification report output path. Defaults next to the zip.")
    template_pack.add_argument("--force", action="store_true", help="Allow replacing a non-empty template pack directory.")
    template_pack.add_argument("--json", action="store_true", help="Print machine-readable template-pack summary.")
    template_pack.set_defaults(func=cmd_template_pack)

    verify_template_pack_cmd = sub.add_parser("verify-template-pack", help="Verify a template pack directory or zip archive against its manifest and hashes.")
    verify_template_target = verify_template_pack_cmd.add_mutually_exclusive_group(required=True)
    verify_template_target.add_argument("--pack-dir", type=Path, help="Template pack directory containing template_pack_manifest.json.")
    verify_template_target.add_argument("--zip", dest="zip_path", type=Path, help="Template pack zip archive to verify without manual extraction.")
    verify_template_pack_cmd.add_argument("--out", type=Path, help="Optional JSON verification report output path.")
    verify_template_pack_cmd.add_argument("--report-out", type=Path, help="Optional Markdown verification report output path.")
    verify_template_pack_cmd.add_argument("--strict", action="store_true", help="Exit non-zero unless the template pack is verified and ready.")
    verify_template_pack_cmd.set_defaults(func=cmd_verify_template_pack)

    template_registry = sub.add_parser("template-registry", help="Build a verified local registry from one or more template-pack zip archives.")
    template_registry.add_argument("--pack-zip", type=Path, action="append", required=True, help="Template pack zip archive to index. Repeatable.")
    template_registry.add_argument("--out", type=Path, required=True, help="JSON registry output path.")
    template_registry.add_argument("--report-out", type=Path, help="Optional Markdown registry report output path.")
    template_registry.add_argument("--base-url", default="", help="Optional public base URL for registry source_url entries.")
    template_registry.add_argument("--json", action="store_true", help="Print machine-readable template-registry summary.")
    template_registry.set_defaults(func=cmd_template_registry)

    template_lock = sub.add_parser("template-lock", help="Lock a template registry entry to an exact source zip hash.")
    template_lock.add_argument("--registry", type=Path, required=True, help="Template registry JSON path.")
    template_lock.add_argument("--template", required=True, help="Template id to lock.")
    template_lock.add_argument("--version", default="", help="Optional exact template version to lock when a registry has multiple versions.")
    template_lock.add_argument("--out", type=Path, required=True, help="Template lock JSON output path.")
    template_lock.add_argument("--cache-dir", type=Path, help="Optional cache directory for verifying source_url entries.")
    template_lock.add_argument("--json", action="store_true", help="Print machine-readable template-lock summary.")
    template_lock.set_defaults(func=cmd_template_lock)

    template_attest = sub.add_parser("template-attest", help="Create a provenance attestation for a template registry or lockfile.")
    template_attest.add_argument("--subject", type=Path, required=True, help="Template registry or lock JSON file to attest.")
    template_attest.add_argument("--subject-type", choices=["template-registry", "template-lock"], default="", help="Optional subject type. Inferred from the subject when omitted.")
    template_attest.add_argument("--out", type=Path, required=True, help="Template attestation JSON output path.")
    template_attest.add_argument("--builder", default="", help="Builder or CI identity to record in the attestation payload.")
    template_attest.add_argument("--key-id", default="", help="Optional identifier for the signing key.")
    template_attest.add_argument("--signing-key", default="", help="Optional HMAC signing key. Defaults to FALSIFLOW_TEMPLATE_ATTESTATION_KEY.")
    template_attest.add_argument("--json", action="store_true", help="Print machine-readable template-attestation summary.")
    template_attest.set_defaults(func=cmd_template_attest)

    verify_template_attestation = sub.add_parser("verify-template-attestation", help="Verify a template provenance attestation against its subject and optional HMAC key.")
    verify_template_attestation.add_argument("--attestation", type=Path, required=True, help="Template attestation JSON path.")
    verify_template_attestation.add_argument("--subject", type=Path, help="Optional subject path override.")
    verify_template_attestation.add_argument("--signing-key", default="", help="Optional HMAC signing key. Defaults to FALSIFLOW_TEMPLATE_ATTESTATION_KEY.")
    verify_template_attestation.add_argument("--out", type=Path, help="Optional JSON verification report output path.")
    verify_template_attestation.add_argument("--strict", action="store_true", help="Exit non-zero unless the attestation signature is verified.")
    verify_template_attestation.add_argument("--json", action="store_true", help="Print machine-readable template-attestation verification.")
    verify_template_attestation.set_defaults(func=cmd_verify_template_attestation)

    template_policy = sub.add_parser("template-policy", help="Create a reusable trust policy from a verified template lock attestation.")
    template_policy.add_argument("--lock", type=Path, required=True, help="Template lock JSON path.")
    template_policy.add_argument("--attestation", type=Path, required=True, help="Template-lock attestation JSON path.")
    template_policy.add_argument("--out", type=Path, required=True, help="Template policy JSON output path.")
    template_policy.add_argument("--policy-id", default="", help="Optional stable policy id. Defaults to template_id@version.")
    template_policy.add_argument("--owner", default="", help="Optional owner or team name recorded in the policy.")
    template_policy.add_argument("--signing-key", default="", help="HMAC signing key for verifying the attestation. Defaults to FALSIFLOW_TEMPLATE_ATTESTATION_KEY.")
    template_policy.add_argument("--json", action="store_true", help="Print machine-readable template-policy summary.")
    template_policy.set_defaults(func=cmd_template_policy)

    verify_template_policy = sub.add_parser("verify-template-policy", help="Verify a template trust policy against a lock and attestation.")
    verify_template_policy.add_argument("--policy", type=Path, required=True, help="Template policy JSON path.")
    verify_template_policy.add_argument("--lock", type=Path, required=True, help="Template lock JSON path.")
    verify_template_policy.add_argument("--attestation", type=Path, required=True, help="Template-lock attestation JSON path.")
    verify_template_policy.add_argument("--signing-key", default="", help="HMAC signing key for verifying the attestation. Defaults to FALSIFLOW_TEMPLATE_ATTESTATION_KEY.")
    verify_template_policy.add_argument("--out", type=Path, help="Optional JSON policy verification report output path.")
    verify_template_policy.add_argument("--strict", action="store_true", help="Exit non-zero unless the template policy is verified.")
    verify_template_policy.add_argument("--json", action="store_true", help="Print machine-readable template-policy verification.")
    verify_template_policy.set_defaults(func=cmd_verify_template_policy)

    template_release = sub.add_parser("template-release", help="Package a verified template pack, lock, attestation, and policy into one release zip.")
    template_release.add_argument("--pack-zip", type=Path, required=True, help="Verified template-pack zip archive.")
    template_release.add_argument("--registry", type=Path, required=True, help="Template registry JSON path.")
    template_release.add_argument("--lock", type=Path, required=True, help="Template lock JSON path.")
    template_release.add_argument("--attestation", type=Path, required=True, help="Template-lock attestation JSON path.")
    template_release.add_argument("--policy", type=Path, required=True, help="Template adoption policy JSON path.")
    template_release.add_argument("--out", type=Path, required=True, help="Template release zip output path.")
    template_release.add_argument("--signing-key", default="", help="HMAC signing key for verifying the attestation and policy before packaging.")
    template_release.add_argument("--json", action="store_true", help="Print machine-readable template-release summary.")
    template_release.set_defaults(func=cmd_template_release)

    verify_template_release = sub.add_parser("verify-template-release", help="Verify a template release zip before installation.")
    verify_template_release.add_argument("--release", type=Path, required=True, help="Template release zip path.")
    verify_template_release.add_argument("--signing-key", default="", help="HMAC signing key for verifying the release attestation and policy.")
    verify_template_release.add_argument("--out", type=Path, help="Optional JSON release verification report output path.")
    verify_template_release.add_argument("--report-out", type=Path, help="Optional Markdown release verification report output path.")
    verify_template_release.add_argument("--strict", action="store_true", help="Exit non-zero unless the template release is verified.")
    verify_template_release.add_argument("--json", action="store_true", help="Print machine-readable template-release verification.")
    verify_template_release.set_defaults(func=cmd_verify_template_release)

    template_install = sub.add_parser("template-install", help="Verify and install a template-pack zip into a reusable template root.")
    template_install_source = template_install.add_mutually_exclusive_group(required=True)
    template_install_source.add_argument("--zip", dest="zip_path", type=Path, help="Template pack zip archive to verify and install.")
    template_install_source.add_argument("--lock", dest="lock_path", type=Path, help="Template lock JSON file to verify before installing.")
    template_install_source.add_argument("--release", dest="release_path", type=Path, help="Template release zip to verify and install.")
    template_install.add_argument("--templates-dir", type=Path, required=True, help="Template root where the verified template directory will be installed.")
    template_install.add_argument("--check-out-dir", type=Path, help="Optional directory for installed-template check artifacts.")
    template_install.add_argument("--cache-dir", type=Path, help="Optional cache directory for lockfile source_url downloads.")
    template_install.add_argument("--attestation", dest="attestation_path", type=Path, help="Optional template-lock attestation to verify before installing from --lock.")
    template_install.add_argument("--signing-key", default="", help="Optional HMAC signing key for --attestation. Defaults to FALSIFLOW_TEMPLATE_ATTESTATION_KEY.")
    template_install.add_argument("--policy", dest="policy_path", type=Path, help="Optional template policy to verify before installing from --lock.")
    template_install.add_argument("--require-attestation", action="store_true", help="Block installation unless --attestation verifies with a trusted signature.")
    template_install.add_argument("--force", action="store_true", help="Allow replacing an installed template with the same id.")
    template_install.add_argument("--json", action="store_true", help="Print machine-readable template-install summary.")
    template_install.set_defaults(func=cmd_template_install)

    adoption_check = sub.add_parser("adoption-check", help="Audit the five adoption priorities as a machine-readable readiness gate.")
    adoption_check.add_argument("--out-dir", type=Path, required=True, help="Directory for adoption-check artifacts and reports.")
    adoption_check.add_argument("--json", action="store_true", help="Print machine-readable adoption-check results.")
    adoption_check.add_argument("--force", action="store_true", help="Allow writing into a non-empty adoption-check directory.")
    adoption_check.add_argument("--skip-dist", action="store_true", help="Skip wheel/sdist build and isolated wheel install checks.")
    adoption_check.set_defaults(func=cmd_adoption_check)

    release_check = sub.add_parser("release-check", help="Run the full pre-release gate: schemas, templates, bundles, zip verification, and portfolio.")
    release_check.add_argument("--out-dir", type=Path, required=True, help="Directory for release-check artifacts and reports.")
    release_check.add_argument("--json", action="store_true", help="Print machine-readable release-check results.")
    release_check.add_argument("--force", action="store_true", help="Allow replacing a non-empty release-check directory.")
    release_check.add_argument("--skip-dist", action="store_true", help="Skip wheel/sdist build and isolated wheel install checks.")
    release_check.set_defaults(func=cmd_release_check)

    validate = sub.add_parser("validate", help="Validate a Falsiflow project config.")
    validate.add_argument("--config", type=Path, required=True)
    validate.add_argument("--out", type=Path, help="Optional validation JSON output path.")
    validate.add_argument("--strict", action="store_true", help="Exit non-zero when validation has errors.")
    validate.set_defaults(func=cmd_validate)

    portfolio = sub.add_parser("portfolio", help="Aggregate claim_summary.json files into a portfolio dashboard.")
    portfolio.add_argument("--input", type=Path, action="append", help="Audit directory, claim_summary.json, or root to scan. Repeatable.")
    portfolio.add_argument("--out-dir", type=Path, required=True)
    portfolio.add_argument("--strict", action="store_true", help="Exit non-zero when any claim is blocked.")
    portfolio.set_defaults(func=cmd_portfolio)

    render = sub.add_parser("render", help="Render measurement templates and an audit report.")
    render.add_argument("--config", type=Path, required=True)
    render.add_argument("--evidence", type=Path)
    render.add_argument("--out-dir", type=Path, required=True)
    render.set_defaults(func=cmd_render)

    audit = sub.add_parser("audit", help="Audit evidence against configured gates.")
    audit.add_argument("--config", type=Path, required=True)
    audit.add_argument("--evidence", type=Path, required=True)
    audit.add_argument("--out-dir", type=Path, required=True)
    audit.add_argument("--strict", action="store_true", help="Exit non-zero when claim_ready is false.")
    audit.set_defaults(func=cmd_audit)

    claim_check = sub.add_parser("claim-check", help="Run audit, source provenance, evidence bundle, and zip verification in one command.")
    claim_check.add_argument("--project-dir", type=Path, help="Project directory containing project.json and evidence_pass_demo.csv; defaults --out-dir to PROJECT_DIR/claim_check.")
    claim_check.add_argument("--config", type=Path, help="Project config JSON path. Defaults to PROJECT_DIR/project.json when --project-dir is used.")
    claim_check.add_argument("--evidence", type=Path, help="Evidence CSV path. Defaults to PROJECT_DIR/evidence_pass_demo.csv when --project-dir is used.")
    claim_check.add_argument("--out-dir", type=Path, help="Output directory. Defaults to PROJECT_DIR/claim_check when --project-dir is used.")
    claim_check.add_argument("--strict", action="store_true", help="Exit non-zero unless the complete claim check is ready.")
    claim_check.add_argument("--force", action="store_true", help="Allow writing into a non-empty claim-check directory.")
    claim_check.add_argument("--json", action="store_true", help="Print machine-readable claim-check summary.")
    claim_check.set_defaults(func=cmd_claim_check)

    bundle = sub.add_parser("bundle", help="Build a portable evidence bundle with audit artifacts, sources, and hashes.")
    bundle.add_argument("--config", type=Path, required=True)
    bundle.add_argument("--evidence", type=Path, required=True)
    bundle.add_argument("--out-dir", type=Path, required=True)
    bundle.add_argument("--zip-out", type=Path, help="Optional zip archive path for the bundle directory.")
    bundle.add_argument("--strict", action="store_true", help="Exit non-zero when audit or source provenance is blocked.")
    bundle.add_argument("--force", action="store_true", help="Allow writing into a non-empty bundle directory.")
    bundle.set_defaults(func=cmd_bundle)

    verify_bundle_cmd = sub.add_parser("verify-bundle", help="Verify a bundle directory or zip archive against its manifest and hashes.")
    verify_target = verify_bundle_cmd.add_mutually_exclusive_group(required=True)
    verify_target.add_argument("--bundle-dir", type=Path, help="Bundle directory containing bundle_manifest.json.")
    verify_target.add_argument("--zip", dest="zip_path", type=Path, help="Bundle zip archive to verify without manual extraction.")
    verify_bundle_cmd.add_argument("--out", type=Path, help="Optional JSON verification report output path.")
    verify_bundle_cmd.add_argument("--report-out", type=Path, help="Optional Markdown verification report output path.")
    verify_bundle_cmd.add_argument("--strict", action="store_true", help="Exit non-zero unless the bundle is verified and bundle_ready.")
    verify_bundle_cmd.set_defaults(func=cmd_verify_bundle)

    next_cmd = sub.add_parser("next", help="Print the next evidence-filling actions.")
    next_cmd.add_argument("--config", type=Path, required=True)
    next_cmd.add_argument("--evidence", type=Path)
    next_cmd.add_argument("--out-dir", type=Path, required=True)
    next_cmd.set_defaults(func=cmd_next)

    sources = sub.add_parser("sources", help="Write a source-file provenance manifest for evidence rows.")
    sources.add_argument("--config", type=Path, required=True)
    sources.add_argument("--evidence", type=Path, required=True)
    sources.add_argument("--out", type=Path, required=True, help="Source manifest JSON output path.")
    sources.add_argument("--report-out", type=Path, help="Optional Markdown report output path.")
    sources.add_argument("--strict", action="store_true", help="Exit non-zero when required source provenance is incomplete.")
    sources.set_defaults(func=cmd_sources)

    ingest = sub.add_parser("ingest-limina-source-values", help="Convert LIMINA source-value sheets into Falsiflow evidence.")
    ingest.add_argument("--input", type=Path, action="append", required=True, help="LIMINA source-value CSV. Repeatable.")
    ingest.add_argument("--out", type=Path, required=True, help="Falsiflow evidence CSV to write.")
    ingest.add_argument("--summary-out", type=Path, help="Optional conversion summary JSON.")
    ingest.add_argument("--project-out", type=Path, help="Optional generated Falsiflow project JSON.")
    ingest.add_argument("--default-candidate", required=True)
    ingest.add_argument("--default-gate", default="h_a_medium_stability")
    ingest.add_argument("--project-id", default="limina_nhi_pedot_habc_falsiflow")
    ingest.add_argument("--claim-id", default="limina_nhi_pedot_habc_evidence_completeness")
    ingest.add_argument(
        "--claim-statement",
        default=(
            "LIMINA NHI-PEDOT H-A/H-B/H-C evidence pack is complete enough for "
            "Falsiflow provenance audit. This is not a material suitability claim."
        ),
    )
    ingest.add_argument("--source-file-base-dir", default=".")
    ingest.add_argument("--allowed-source-root", action="append", default=["data/source_files"])
    ingest.set_defaults(func=cmd_ingest_limina_source_values)

    wide = sub.add_parser("ingest-wide-csv", help="Convert a wide lab CSV into Falsiflow evidence rows.")
    add_wide_csv_arguments(wide)
    wide.set_defaults(func=cmd_ingest_wide_csv)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
