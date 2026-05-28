"""Command-line interface for synthetic-response-metrics."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from synthetic_response_metrics.core import DispersionConfig, compute_dispersion
from synthetic_response_metrics.io import load_records, write_json


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="srm")
    subparsers = parser.add_subparsers(dest="command", required=True)

    compute = subparsers.add_parser("compute", help="Compute response-dispersion metrics.")
    compute.add_argument("input", help="CSV, JSON, or JSONL response file.")
    compute.add_argument("-o", "--output", help="Write result JSON to this path.")
    compute.add_argument("--threshold", type=float, default=0.70, help="Max-similarity alert threshold.")
    compute.add_argument("--min-answers", type=int, default=2, help="Minimum valid answers per question.")
    compute.add_argument("--min-token-length", type=int, default=3, help="Minimum normalized token length.")
    compute.add_argument("--language", default="auto", choices=["auto", "en", "es"], help="Stopword language.")
    compute.add_argument("--stopwords-file", help="Optional newline-delimited stopwords file.")
    compute.add_argument(
        "--duplicate-policy",
        default="latest",
        choices=["latest", "first", "error", "keep_all"],
        help="How repeated question_id/agent_id records are handled.",
    )
    compute.add_argument("--include-pairs", action="store_true", help="Include top similar agent pairs.")
    compute.add_argument("--top-pairs-limit", type=int, default=5, help="Number of pair rows to include.")
    return parser


def _load_stopwords(path: str | None) -> set[str] | None:
    if not path:
        return None
    source = Path(path)
    with source.open("r", encoding="utf-8-sig") as handle:
        return {
            stripped
            for line in handle
            if (stripped := line.strip()) and not stripped.startswith("#")
        }


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "compute":
        try:
            records = load_records(args.input)
            result = compute_dispersion(
                records,
                DispersionConfig(
                    threshold_max_similarity=args.threshold,
                    min_answers=args.min_answers,
                    min_token_length=args.min_token_length,
                    language=args.language,
                    stopwords=_load_stopwords(args.stopwords_file),
                    duplicate_policy=args.duplicate_policy,
                    include_pairs=args.include_pairs,
                    top_pairs_limit=args.top_pairs_limit,
                ),
            ).to_dict()
            if args.output:
                write_json(args.output, result)
            else:
                json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
                sys.stdout.write("\n")
            return 0
        except Exception as exc:
            sys.stderr.write(f"srm: error: {exc}\n")
            return 1

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
