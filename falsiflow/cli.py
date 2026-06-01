"""Small public CLI for Falsiflow."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .claim_check import run_claim_check
from .core import falsiflow_schema


SCHEMA_KINDS = ["project", "evidence-row", "all"]


def claim_status(summary: dict[str, object]) -> str:
    return "claim_ready" if summary.get("status") == "claim_check_ready" else "claim_blocked"


def print_check_summary(summary: dict[str, object], out_dir: Path, as_json: bool) -> None:
    status = claim_status(summary)
    if as_json:
        compact = {
            "status": status,
            "claim_check_status": summary.get("status", ""),
            "claim_ready": bool(summary.get("claim_ready")),
            "blocking_stage": summary.get("blocking_stage", ""),
            "failure_count": summary.get("failure_count", 0),
            "blocker_count": summary.get("blocker_count", 0),
            "report": str(out_dir / "claim_check.md"),
            "bundle": str(out_dir / "evidence_bundle.zip"),
            "evidence_todo": summary.get("evidence_todo", []),
        }
        print(json.dumps(compact, indent=2, sort_keys=True))
        return

    print(status)
    print(f"stage: {summary.get('blocking_stage', '')}")
    print(f"failures: {summary.get('failure_count', 0)}")
    evidence_todo = summary.get("evidence_todo", [])
    if isinstance(evidence_todo, list) and evidence_todo:
        print("reasons:")
        for item in evidence_todo[:5]:
            if not isinstance(item, dict):
                continue
            key = "/".join(
                str(item.get(part, "") or "")
                for part in ["gate_id", "candidate_id", "sample_id", "field"]
                if item.get(part)
            )
            reasons = "; ".join(str(reason) for reason in item.get("reasons", []))
            print(f"- {key}: {reasons}")
    print(f"report: {out_dir / 'claim_check.md'}")
    print(f"bundle: {out_dir / 'evidence_bundle.zip'}")


def cmd_check(args: argparse.Namespace) -> int:
    config = args.config.expanduser()
    evidence = args.evidence.expanduser()
    out_dir = args.out_dir.expanduser()
    if not config.exists():
        raise SystemExit(f"Project config does not exist: {config}")
    if not evidence.exists():
        raise SystemExit(f"Evidence file does not exist: {evidence}")

    summary = run_claim_check(config, evidence, out_dir, force=args.force)
    print_check_summary(summary, out_dir, args.json)
    return 0 if claim_status(summary) == "claim_ready" or not args.strict else 2


def cmd_schema(args: argparse.Namespace) -> int:
    if args.kind == "all":
        schema = {kind: falsiflow_schema(kind) for kind in SCHEMA_KINDS if kind != "all"}
    else:
        schema = falsiflow_schema(args.kind)
    text = json.dumps(schema, indent=2, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


def normalize_legacy_claim_check(argv: list[str]) -> list[str]:
    if not argv or argv[0] != "claim-check":
        return argv
    normalized = ["check", *argv[1:]]
    if "--project-dir" not in normalized:
        return normalized

    index = normalized.index("--project-dir")
    try:
        project_dir = Path(normalized[index + 1])
    except IndexError as exc:
        raise SystemExit("claim-check --project-dir requires a value") from exc
    del normalized[index : index + 2]

    if "--config" not in normalized:
        normalized.extend(["--config", str(project_dir / "project.json")])
    if "--evidence" not in normalized:
        normalized.extend(["--evidence", str(project_dir / "evidence.csv")])
    if "--out-dir" not in normalized:
        normalized.extend(["--out-dir", str(project_dir / "claim_check")])
    return normalized


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="falsiflow",
        description="Check numeric claims against source-backed evidence.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="Check whether a numeric claim has reviewable evidence.")
    check.add_argument("--config", type=Path, required=True, help="Project config JSON path.")
    check.add_argument("--evidence", type=Path, required=True, help="Evidence CSV path.")
    check.add_argument("--out-dir", type=Path, default=Path("falsiflow_check"), help="Output directory for check artifacts.")
    check.add_argument("--strict", action="store_true", help="Exit non-zero unless the claim is ready.")
    check.add_argument("--force", action="store_true", help="Allow writing into a non-empty check directory.")
    check.add_argument("--json", action="store_true", help="Print machine-readable check summary.")
    check.set_defaults(func=cmd_check)

    schema = sub.add_parser("schema", help="Print the minimal Falsiflow JSON Schemas.")
    schema.add_argument("--kind", choices=SCHEMA_KINDS, default="all", help="Schema kind to print.")
    schema.add_argument("--out", type=Path, help="Optional JSON output path.")
    schema.set_defaults(func=cmd_schema)
    return parser


def main(argv: list[str] | None = None) -> int:
    argv_list = normalize_legacy_claim_check(list(sys.argv[1:] if argv is None else argv))
    parser = build_parser()
    args = parser.parse_args(argv_list)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
