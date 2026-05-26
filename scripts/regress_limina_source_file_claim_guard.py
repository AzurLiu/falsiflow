#!/usr/bin/env python3
"""Regression-test claim provenance source_file requirements."""

from __future__ import annotations

import csv
import json
import tempfile
from pathlib import Path
from typing import Any

from audit_limina_suitability_claim import ROOT, provenance


DATA_OUT = ROOT / "data" / "limina_source_file_claim_guard_regression.json"
REPORT_OUT = ROOT / "reports" / "limina_source_file_claim_guard_regression.md"

FIELDS = ["run_id", "date", "operator_or_agent", "source_file", "notes"]


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def build_manifest(path: Path, allowed_root: Path) -> None:
    payload = {
        "status": "source_file_manifest_ready",
        "allowed_roots": [
            {
                "root_id": "tmp_regression_allowed_root",
                "path": str(allowed_root),
                "scope": "temporary regression source files",
                "purpose": "Positive-control source-file guard regression root.",
            }
        ],
        "rejected_source_markers": ["synthetic", "fixture", "placeholder"],
    }
    write_json(path, payload)


def assertion(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "passed": passed, "detail": detail}


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# LIMINA Source-File Claim Guard Regression",
        "",
        "This regression checks that measured-looking rows cannot become claimable unless they cite an existing source_file under the manifest.",
        "",
        f"**Status:** `{result['status']}`",
        f"**Missing-source claimable:** `{str(result['missing_source']['claimable_measurement_source']).lower()}`",
        f"**Positive-control claimable:** `{str(result['positive_source']['claimable_measurement_source']).lower()}`",
        "",
        "## Assertions",
        "",
        "| Assertion | Result | Detail |",
        "| --- | --- | --- |",
    ]
    for item in result["assertions"]:
        status = "pass" if item["passed"] else "fail"
        detail = str(item["detail"]).replace("|", "\\|").replace("\n", " ")
        lines.append(f"| `{item['name']}` | `{status}` | {detail} |")
    lines.extend([
        "",
        "## Boundary",
        "",
        "The positive-control source file is temporary regression scaffolding only. It is not LIMINA material evidence.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="limina_source_file_guard_") as tmp:
        tmp_root = Path(tmp)
        allowed_root = tmp_root / "allowed_sources"
        allowed_root.mkdir(parents=True)
        real_source = allowed_root / "instrument_export.csv"
        real_source.write_text("run_id,value\nmeasured_like_positive,1\n", encoding="utf-8")
        manifest = tmp_root / "manifest.json"
        build_manifest(manifest, allowed_root)

        missing_csv = tmp_root / "missing_source.csv"
        write_csv(
            missing_csv,
            [
                {
                    "run_id": "measured_like_missing_source",
                    "date": "2026-05-23",
                    "operator_or_agent": "external_lab_regression",
                    "source_file": "",
                    "notes": "measured-looking row without raw source file",
                },
                {
                    "run_id": "measured_like_missing_file",
                    "date": "2026-05-23",
                    "operator_or_agent": "external_lab_regression",
                    "source_file": str(allowed_root / "missing_export.csv"),
                    "notes": "measured-looking row with missing raw source file",
                },
            ],
        )
        positive_csv = tmp_root / "positive_source.csv"
        write_csv(
            positive_csv,
            [
                {
                    "run_id": "measured_like_positive",
                    "date": "2026-05-23",
                    "operator_or_agent": "external_lab_regression",
                    "source_file": str(real_source),
                    "notes": "temporary positive-control row",
                }
            ],
        )

        missing_source = provenance(missing_csv, manifest)
        positive_source = provenance(positive_csv, manifest)

    missing_markers = [
        marker
        for example in missing_source.get("placeholder_examples", [])
        for marker in example.get("markers", [])
    ]
    assertions = [
        assertion(
            "missing_source_not_claimable",
            missing_source.get("claimable_measurement_source") is False,
            f"claimable={missing_source.get('claimable_measurement_source')}",
        ),
        assertion(
            "blank_source_file_is_placeholder",
            "source_file=missing" in missing_markers,
            f"placeholder_markers={missing_markers}",
        ),
        assertion(
            "missing_source_file_is_issue",
            missing_source.get("source_file_issue_count") == 1,
            f"source_file_issue_count={missing_source.get('source_file_issue_count')}",
        ),
        assertion(
            "existing_allowed_source_can_be_claimable",
            positive_source.get("claimable_measurement_source") is True
            and positive_source.get("measured_row_count") == 1,
            (
                f"claimable={positive_source.get('claimable_measurement_source')}; "
                f"measured={positive_source.get('measured_row_count')}"
            ),
        ),
    ]
    status = "pass" if all(item["passed"] for item in assertions) else "fail"
    result = {
        "status": status,
        "missing_source": missing_source,
        "positive_source": positive_source,
        "assertions": assertions,
    }
    write_json(DATA_OUT, result)
    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.write_text(render_report(result), encoding="utf-8")
    print(f"LIMINA source-file claim guard regression: {status}")
    print(f"Wrote {DATA_OUT}")
    print(f"Wrote {REPORT_OUT}")
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
