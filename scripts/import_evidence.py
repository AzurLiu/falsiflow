#!/usr/bin/env python3
"""Import and validate LIMINA evidence records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = ROOT / "data" / "evidence_schema.json"
DEFAULT_INPUT = ROOT / "data" / "evidence_records_seed.json"
DEFAULT_JSONL = ROOT / "data" / "evidence_records.jsonl"
DEFAULT_DB = ROOT / "data" / "limina.duckdb"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_records(path: Path) -> list[dict[str, Any]]:
    raw = load_json(path)
    if isinstance(raw, dict):
        raw = [raw]
    if not isinstance(raw, list) or not all(isinstance(item, dict) for item in raw):
        raise ValueError(f"{path} must contain a JSON object or list of objects")
    return raw


def validate_records(records: list[dict[str, Any]], schema: dict[str, Any]) -> None:
    required = schema["required_fields"]
    ids: set[str] = set()
    errors: list[str] = []

    for index, record in enumerate(records):
        prefix = f"record[{index}]"
        record_id = record.get("id")
        if not record_id:
            errors.append(f"{prefix}: missing id")
        elif record_id in ids:
            errors.append(f"{prefix}: duplicate id {record_id}")
        else:
            ids.add(str(record_id))

        for field in required:
            if field not in record:
                errors.append(f"{prefix} {record_id}: missing {field}")
            elif record[field] in ("", [], None):
                errors.append(f"{prefix} {record_id}: empty {field}")

        if record.get("confidence") not in {"low", "medium", "high"}:
            errors.append(f"{prefix} {record_id}: confidence must be low, medium, or high")

    if errors:
        raise ValueError("\n".join(errors))


def write_jsonl(records: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True, ensure_ascii=True) + "\n")


def write_duckdb(records: list[dict[str, Any]], path: Path) -> bool:
    try:
        import duckdb
    except ModuleNotFoundError:
        return False

    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            **record,
            "readouts": json.dumps(record.get("readouts", []), sort_keys=True),
        }
        for record in records
    ]

    with duckdb.connect(str(path)) as conn:
        conn.execute("drop table if exists evidence")
        conn.execute(
            """
            create table evidence (
                id varchar primary key,
                related_priority varchar,
                material_or_component varchar,
                claim varchar,
                assay_or_context varchar,
                readouts varchar,
                result_summary varchar,
                risk_or_caveat varchar,
                source_title varchar,
                source_url varchar,
                evidence_type varchar,
                confidence varchar
            )
            """
        )
        conn.executemany(
            """
            insert into evidence values (
                $id, $related_priority, $material_or_component, $claim,
                $assay_or_context, $readouts, $result_summary, $risk_or_caveat,
                $source_title, $source_url, $evidence_type, $confidence
            )
            """,
            rows,
        )
    return True


def evidence_markdown(records: list[dict[str, Any]]) -> str:
    lines = [
        "# LIMINA Evidence Register",
        "",
        "| ID | Priority | Component | Evidence | Confidence |",
        "| --- | --- | --- | --- | --- |",
    ]
    for record in sorted(records, key=lambda item: (item["related_priority"], item["id"])):
        lines.append(
            f"| {record['id']} | {record['related_priority']} | "
            f"{record['material_or_component']} | "
            f"{record['claim']} ([source]({record['source_url']})) | "
            f"{record['confidence']} |"
        )
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate and import LIMINA evidence records.")
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--jsonl", type=Path, default=DEFAULT_JSONL)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--report", type=Path, default=ROOT / "reports" / "evidence_register.md")
    parser.add_argument("--no-db", action="store_true", help="Skip DuckDB export.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    schema = load_json(args.schema)
    records = load_records(args.input)
    validate_records(records, schema)
    write_jsonl(records, args.jsonl)
    db_written = False
    if not args.no_db:
        db_written = write_duckdb(records, args.db)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(evidence_markdown(records), encoding="utf-8")
    print(f"Imported {len(records)} evidence records")
    print(f"Wrote {args.jsonl}")
    if not args.no_db:
        if db_written:
            print(f"Wrote {args.db}")
        else:
            print("Skipped DuckDB export because duckdb is not installed in this Python environment")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
