#!/usr/bin/env python3
"""Rank LIMINA seed material candidates."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.limina_score import load_json, score_all, to_markdown


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rank LIMINA material candidates.")
    parser.add_argument(
        "--profile",
        type=Path,
        default=ROOT / "data" / "limina_scoring_profile.json",
        help="Scoring profile JSON path.",
    )
    parser.add_argument(
        "--candidates",
        type=Path,
        default=ROOT / "data" / "material_candidates_seed.json",
        help="Candidate JSON path.",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format.",
    )
    parser.add_argument("--out", type=Path, default=None, help="Optional output path.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    profile = load_json(args.profile)
    candidates = load_json(args.candidates)
    scored = score_all(candidates, profile)

    if args.format == "json":
        output = json.dumps(
            [
                {
                    "id": item.id,
                    "name": item.name,
                    "priority": item.priority,
                    "weighted_score": item.weighted_score,
                    "gate_failures": item.gate_failures,
                }
                for item in scored
            ],
            indent=2,
            sort_keys=True,
        )
    else:
        output = to_markdown(scored)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
    else:
        print(output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
