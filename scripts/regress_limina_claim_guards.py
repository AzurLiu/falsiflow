#!/usr/bin/env python3
"""Regression-test LIMINA claim guards against full-pass synthetic fixtures."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_OUT = ROOT / "data" / "limina_claim_guard_regression.json"
REPORT_OUT = ROOT / "reports" / "limina_claim_guard_regression.md"

H_A_RAW_PASS_FIXTURE = ROOT / "data" / "fixtures" / "nhi_pedot_h_a_raw_full_pass_fixture.csv"
COUPON_PASS_FIXTURE = ROOT / "data" / "fixtures" / "nhi_pedot_runs_full_pass_fixture.csv"
LONG_PASS_FIXTURE = ROOT / "data" / "fixtures" / "nhi_pedot_long_full_pass_fixture.csv"
ZRC_PASS_FIXTURE = ROOT / "data" / "fixtures" / "zrc_nd_validation_runs_full_pass_fixture.csv"
ZRC_BIO_PASS_FIXTURE = ROOT / "data" / "fixtures" / "zrc_nd_bio_runs_full_pass_fixture.csv"


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    return value if isinstance(value, dict) else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def run_step(step_id: str, argv: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, *argv],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return {
        "id": step_id,
        "argv": [sys.executable, *argv],
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def assert_condition(assertions: list[dict[str, Any]], name: str, passed: bool, detail: str) -> None:
    assertions.append({
        "name": name,
        "passed": passed,
        "detail": detail,
    })


def candidate_by_id(audit: dict[str, Any], technology_id: str) -> dict[str, Any]:
    for item in audit.get("candidate_audits", []):
        if item.get("technology_id") == technology_id:
            return item
    return {}


def render_report(result: dict[str, Any]) -> str:
    summaries = result["summaries"]
    assertions = result["assertions"]
    steps = result["steps"]
    audit = summaries["claim_audit"]
    nhi = audit["nhi"]
    zrc = audit.get("zrc", {})
    lines = [
        "# LIMINA Claim Guard Regression",
        "",
        "This regression proves that full-pass synthetic fixtures cannot support a material suitability claim.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Temporary output directory:** `{result['tmp_dir']}`",
        "",
        "## Key Outcomes",
        "",
        f"- H-A synthetic fixture interpretation: `{summaries['h_a']['status']}`",
        f"- Coupon synthetic fixture evaluator: `{summaries['coupon']['status']}`",
        f"- Long synthetic fixture evaluator: `{summaries['long']['status']}`",
        f"- ZRC-ND synthetic fixture evaluator: `{summaries['zrc']['status']}`",
        f"- ZRC-ND biological synthetic fixture evaluator: `{summaries['zrc_bio']['status']}`",
        f"- ZRC-ND synthetic readiness: `{summaries['zrc_readiness']['readiness']}`",
        f"- Forward package state: `{summaries['forward']['status']}`",
        f"- Final claim audit: claim_ready=`{str(audit['claim_ready']).lower()}`, status=`{audit['status']}`",
        "",
        "## NHI Provenance Rejection",
        "",
        "| Source | Rows | Measured | Synthetic | Placeholder | Claimable |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for label, provenance in nhi.get("provenance", {}).items():
        lines.append(
            f"| `{label}` | {provenance.get('row_count', 0)} | "
            f"{provenance.get('measured_row_count', 0)} | "
            f"{provenance.get('synthetic_row_count', 0)} | "
            f"{provenance.get('placeholder_row_count', 0)} | "
            f"`{str(provenance.get('claimable_measurement_source')).lower()}` |"
        )

    lines.extend([
        "",
        "## ZRC-ND Provenance Rejection",
        "",
        "| Source | Rows | Measured | Synthetic | Placeholder | Claimable |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ])
    for label, provenance in zrc.get("provenance", {}).items():
        lines.append(
            f"| `{label}` | {provenance.get('row_count', 0)} | "
            f"{provenance.get('measured_row_count', 0)} | "
            f"{provenance.get('synthetic_row_count', 0)} | "
            f"{provenance.get('placeholder_row_count', 0)} | "
            f"`{str(provenance.get('claimable_measurement_source')).lower()}` |"
        )

    lines.extend([
        "",
        "## Assertions",
        "",
        "| Assertion | Result | Detail |",
        "| --- | --- | --- |",
    ])
    for item in assertions:
        status = "pass" if item["passed"] else "fail"
        detail = str(item["detail"]).replace("|", "\\|").replace("\n", " ")
        lines.append(f"| `{item['name']}` | `{status}` | {detail} |")

    lines.extend([
        "",
        "## Commands",
        "",
        "| Step | Return code |",
        "| --- | ---: |",
    ])
    for step in steps:
        lines.append(f"| `{step['id']}` | {step['returncode']} |")

    lines.extend([
        "",
        "## Boundary",
        "",
        "Synthetic fixtures are allowed to exercise evaluator logic only. The claim audit must still require non-synthetic measured rows before LIMINA says a material technology is suitable.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    tmp_root = Path(tempfile.mkdtemp(prefix="limina_claim_guard_regression_"))
    paths = {
        "h_a_active": tmp_root / "h_a_active.csv",
        "h_a_merge_json": tmp_root / "h_a_merge.json",
        "h_a_merge_report": tmp_root / "h_a_merge.md",
        "h_a_qc_json": tmp_root / "h_a_qc.json",
        "h_a_qc_report": tmp_root / "h_a_qc.md",
        "h_a_json": tmp_root / "h_a_interpretation.json",
        "h_a_report": tmp_root / "h_a_interpretation.md",
        "forward_json": tmp_root / "forward.json",
        "forward_csv": tmp_root / "forward.csv",
        "forward_report": tmp_root / "forward.md",
        "coupon_json": tmp_root / "coupon_results.json",
        "coupon_report": tmp_root / "coupon_results.md",
        "long_json": tmp_root / "long_results.json",
        "long_report": tmp_root / "long_results.md",
        "zrc_json": tmp_root / "zrc_results.json",
        "zrc_report": tmp_root / "zrc_results.md",
        "zrc_bio_json": tmp_root / "zrc_bio_results.json",
        "zrc_bio_report": tmp_root / "zrc_bio_results.md",
        "zrc_readiness_json": tmp_root / "zrc_readiness.json",
        "zrc_readiness_report": tmp_root / "zrc_readiness.md",
        "audit_json": tmp_root / "claim_audit.json",
        "audit_report": tmp_root / "claim_audit.md",
    }

    step_defs = [
        ("generate_h_a_raw_fixture", ["scripts/generate_nhi_pedot_h_a_raw_fixture_data.py"]),
        ("generate_coupon_fixture", ["scripts/generate_nhi_pedot_fixture_data.py"]),
        ("generate_long_fixture", ["scripts/generate_nhi_pedot_long_fixture_data.py"]),
        (
            "merge_h_a_full_pass_fixture",
            [
                "scripts/merge_nhi_pedot_h_a_raw_measurements.py",
                "--raw",
                str(H_A_RAW_PASS_FIXTURE),
                "--out",
                str(paths["h_a_active"]),
                "--json-out",
                str(paths["h_a_merge_json"]),
                "--report",
                str(paths["h_a_merge_report"]),
            ],
        ),
        (
            "qc_h_a_full_pass_fixture",
            [
                "scripts/qc_nhi_pedot_h_a_intake.py",
                "--runs",
                str(paths["h_a_active"]),
                "--json-out",
                str(paths["h_a_qc_json"]),
                "--report",
                str(paths["h_a_qc_report"]),
            ],
        ),
        (
            "interpret_h_a_full_pass_fixture",
            [
                "scripts/interpret_nhi_pedot_h_a_sentinel.py",
                "--runs",
                str(paths["h_a_active"]),
                "--json-out",
                str(paths["h_a_json"]),
                "--report",
                str(paths["h_a_report"]),
            ],
        ),
        (
            "generate_forward_package",
            [
                "scripts/generate_nhi_pedot_forward_gate_package.py",
                "--h-a",
                str(paths["h_a_json"]),
                "--json-out",
                str(paths["forward_json"]),
                "--csv-out",
                str(paths["forward_csv"]),
                "--report",
                str(paths["forward_report"]),
            ],
        ),
        (
            "evaluate_coupon_full_pass_fixture",
            [
                "scripts/evaluate_nhi_pedot_runs.py",
                "--runs",
                str(COUPON_PASS_FIXTURE),
                "--results",
                str(paths["coupon_json"]),
                "--report",
                str(paths["coupon_report"]),
            ],
        ),
        (
            "evaluate_long_full_pass_fixture",
            [
                "scripts/evaluate_nhi_pedot_long_runs.py",
                "--runs",
                str(LONG_PASS_FIXTURE),
                "--results",
                str(paths["long_json"]),
                "--report",
                str(paths["long_report"]),
            ],
        ),
        (
            "evaluate_zrc_full_pass_fixture",
            [
                "scripts/evaluate_zrc_nd_validation_runs.py",
                "--runs",
                str(ZRC_PASS_FIXTURE),
                "--results",
                str(paths["zrc_json"]),
                "--report",
                str(paths["zrc_report"]),
            ],
        ),
        (
            "evaluate_zrc_bio_full_pass_fixture",
            [
                "scripts/evaluate_zrc_nd_bio_runs.py",
                "--runs",
                str(ZRC_BIO_PASS_FIXTURE),
                "--results",
                str(paths["zrc_bio_json"]),
                "--report",
                str(paths["zrc_bio_report"]),
            ],
        ),
        (
            "audit_zrc_with_full_pass_fixtures",
            [
                "scripts/audit_zrc_nd_readiness.py",
                "--results",
                str(paths["zrc_json"]),
                "--bio-results",
                str(paths["zrc_bio_json"]),
                "--json-out",
                str(paths["zrc_readiness_json"]),
                "--out",
                str(paths["zrc_readiness_report"]),
            ],
        ),
        (
            "audit_claim_with_full_pass_fixtures",
            [
                "scripts/audit_limina_suitability_claim.py",
                "--zrc-readiness",
                str(paths["zrc_readiness_json"]),
                "--zrc-runs",
                str(ZRC_PASS_FIXTURE),
                "--zrc-bio-runs",
                str(ZRC_BIO_PASS_FIXTURE),
                "--nhi-h-a",
                str(paths["h_a_json"]),
                "--nhi-h-a-runs",
                str(paths["h_a_active"]),
                "--nhi-forward",
                str(paths["forward_json"]),
                "--nhi-results",
                str(paths["coupon_json"]),
                "--nhi-runs",
                str(COUPON_PASS_FIXTURE),
                "--nhi-long-results",
                str(paths["long_json"]),
                "--nhi-long-runs",
                str(LONG_PASS_FIXTURE),
                "--json-out",
                str(paths["audit_json"]),
                "--report",
                str(paths["audit_report"]),
            ],
        ),
    ]

    steps = [run_step(step_id, argv) for step_id, argv in step_defs]
    failed_steps = [step for step in steps if step["returncode"] != 0]

    h_a = read_json(paths["h_a_json"]) if paths["h_a_json"].exists() else {}
    h_a_qc = read_json(paths["h_a_qc_json"]) if paths["h_a_qc_json"].exists() else {}
    forward = read_json(paths["forward_json"]) if paths["forward_json"].exists() else {}
    coupon = read_json(paths["coupon_json"]) if paths["coupon_json"].exists() else {}
    long = read_json(paths["long_json"]) if paths["long_json"].exists() else {}
    zrc_results = read_json(paths["zrc_json"]) if paths["zrc_json"].exists() else {}
    zrc_bio_results = read_json(paths["zrc_bio_json"]) if paths["zrc_bio_json"].exists() else {}
    zrc_readiness = read_json(paths["zrc_readiness_json"]) if paths["zrc_readiness_json"].exists() else {}
    audit = read_json(paths["audit_json"]) if paths["audit_json"].exists() else {}
    nhi = candidate_by_id(audit, "limina_nhi_pedot_laminin_v0_1")
    zrc = candidate_by_id(audit, "limina_zrc_nd_v0_1")

    coupon_status = coupon.get("summary", {}).get("status", "missing")
    long_status = long.get("summary", {}).get("status", "missing")
    zrc_status = zrc_results.get("summary", {}).get("status", "missing")
    zrc_bio_status = zrc_bio_results.get("summary", {}).get("status", "missing")
    zrc_readiness_status = zrc_readiness.get("readiness", "missing")
    h_a_status = h_a.get("status", "missing")
    forward_status = forward.get("status", "missing")

    provenance = nhi.get("provenance", {})
    h_a_source = provenance.get("h_a_sentinel", {})
    coupon_source = provenance.get("coupon", {})
    long_source = provenance.get("long_duration", {})
    zrc_provenance = zrc.get("provenance", {})
    zrc_source = zrc_provenance.get("non_cell", {})
    zrc_bio_source = zrc_provenance.get("biological", {})

    assertions: list[dict[str, Any]] = []
    assert_condition(
        assertions,
        "all_commands_succeeded",
        not failed_steps,
        "failed steps: " + ", ".join(step["id"] for step in failed_steps) if failed_steps else "all steps returned 0",
    )
    assert_condition(
        assertions,
        "coupon_fixture_exercises_full_pass",
        coupon_status == "nhi_pedot_passes_gates",
        f"coupon evaluator status={coupon_status}",
    )
    assert_condition(
        assertions,
        "long_fixture_exercises_full_pass",
        long_status == "nhi_pedot_long_passes_gates",
        f"long evaluator status={long_status}",
    )
    assert_condition(
        assertions,
        "zrc_fixture_exercises_full_pass",
        zrc_status == "lead_passes_non_cell_gates",
        f"zrc evaluator status={zrc_status}",
    )
    assert_condition(
        assertions,
        "zrc_bio_fixture_exercises_full_pass",
        zrc_bio_status == "bio_followup_passes_gates",
        f"zrc bio evaluator status={zrc_bio_status}",
    )
    assert_condition(
        assertions,
        "zrc_readiness_fixture_can_reach_suitable",
        zrc_readiness.get("suitable") is True and zrc_readiness_status == "suitable",
        f"zrc readiness={zrc_readiness_status}; suitable={zrc_readiness.get('suitable')}",
    )
    assert_condition(
        assertions,
        "h_a_fixture_rejected_before_interpretation",
        h_a_status == "h_a_invalid_provenance" and h_a_qc.get("intake_ready") is False,
        f"h_a status={h_a_status}; h_a_qc intake_ready={h_a_qc.get('intake_ready')}",
    )
    assert_condition(
        assertions,
        "forward_package_not_activated_by_fixture",
        forward_status == "preregistered_waiting_for_h_a",
        f"forward status={forward_status}",
    )
    assert_condition(
        assertions,
        "audit_refuses_synthetic_claim",
        audit.get("claim_ready") is False and audit.get("status") == "no_suitable_material_claim_ready",
        f"claim_ready={audit.get('claim_ready')}; status={audit.get('status')}",
    )
    assert_condition(
        assertions,
        "h_a_source_non_claimable",
        h_a_source.get("claimable_measurement_source") is False and h_a_source.get("synthetic_row_count", 0) > 0,
        f"claimable={h_a_source.get('claimable_measurement_source')}; synthetic={h_a_source.get('synthetic_row_count')}",
    )
    assert_condition(
        assertions,
        "coupon_source_non_claimable",
        coupon_source.get("claimable_measurement_source") is False and coupon_source.get("synthetic_row_count", 0) > 0,
        f"claimable={coupon_source.get('claimable_measurement_source')}; synthetic={coupon_source.get('synthetic_row_count')}",
    )
    assert_condition(
        assertions,
        "long_source_non_claimable",
        long_source.get("claimable_measurement_source") is False and long_source.get("synthetic_row_count", 0) > 0,
        f"claimable={long_source.get('claimable_measurement_source')}; synthetic={long_source.get('synthetic_row_count')}",
    )
    assert_condition(
        assertions,
        "zrc_source_non_claimable",
        zrc_source.get("claimable_measurement_source") is False and zrc_source.get("synthetic_row_count", 0) > 0,
        f"claimable={zrc_source.get('claimable_measurement_source')}; synthetic={zrc_source.get('synthetic_row_count')}",
    )
    assert_condition(
        assertions,
        "zrc_bio_source_non_claimable",
        zrc_bio_source.get("claimable_measurement_source") is False and zrc_bio_source.get("synthetic_row_count", 0) > 0,
        f"claimable={zrc_bio_source.get('claimable_measurement_source')}; synthetic={zrc_bio_source.get('synthetic_row_count')}",
    )

    status = "pass" if assertions and all(item["passed"] for item in assertions) else "fail"
    result = {
        "status": status,
        "tmp_dir": str(tmp_root),
        "fixtures": {
            "h_a_raw_full_pass": rel(H_A_RAW_PASS_FIXTURE),
            "coupon_full_pass": rel(COUPON_PASS_FIXTURE),
            "long_full_pass": rel(LONG_PASS_FIXTURE),
            "zrc_full_pass": rel(ZRC_PASS_FIXTURE),
            "zrc_bio_full_pass": rel(ZRC_BIO_PASS_FIXTURE),
        },
        "temporary_outputs": {key: str(value) for key, value in paths.items()},
        "summaries": {
            "h_a": {
                "status": h_a_status,
                "intake_ready": h_a_qc.get("intake_ready"),
                "provenance": h_a.get("provenance", {}),
            },
            "coupon": {
                "status": coupon_status,
                "rows": coupon.get("summary", {}).get("rows", 0),
            },
            "long": {
                "status": long_status,
                "rows": long.get("summary", {}).get("rows", 0),
            },
            "zrc": {
                "status": zrc_status,
                "rows": zrc_results.get("summary", {}).get("rows", 0),
            },
            "zrc_bio": {
                "status": zrc_bio_status,
                "rows": zrc_bio_results.get("summary", {}).get("rows", 0),
            },
            "zrc_readiness": {
                "readiness": zrc_readiness_status,
                "suitable": zrc_readiness.get("suitable"),
            },
            "forward": {
                "status": forward_status,
                "rows": forward.get("row_count", 0),
            },
            "claim_audit": {
                "claim_ready": audit.get("claim_ready"),
                "status": audit.get("status"),
                "nhi": nhi,
                "zrc": zrc,
            },
        },
        "assertions": assertions,
        "steps": steps,
    }

    write_json(DATA_OUT, result)
    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.write_text(render_report(result), encoding="utf-8")

    print(f"LIMINA claim guard regression: {status}")
    print(f"Wrote {DATA_OUT}")
    print(f"Wrote {REPORT_OUT}")
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
