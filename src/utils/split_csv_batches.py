#!/usr/bin/env python3
"""Split a CSV file into a fixed number of batches."""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    from src.utils.csv_batch_utils import (
        DEFAULT_MAX_ROWS_PER_BATCH,
        load_csv_rows,
        split_csv,
        suggest_batches,
    )
except ImportError:
    from csv_batch_utils import (  # type: ignore
        DEFAULT_MAX_ROWS_PER_BATCH,
        load_csv_rows,
        split_csv,
        suggest_batches,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Split a CSV file into X output batches."
    )
    parser.add_argument("csv_file", type=Path, help="Path to the source CSV file.")
    parser.add_argument(
        "batches",
        type=int,
        nargs="?",
        help=(
            "Number of output batches to generate. If omitted, suggests batches "
            f"of {DEFAULT_MAX_ROWS_PER_BATCH} rows."
        ),
    )
    parser.add_argument(
        "--delimiter",
        default=",",
        help="CSV delimiter used in the file. Default: ','.",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="File encoding. Default: utf-8.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.batches is None:
        _, rows = load_csv_rows(
            csv_file=args.csv_file,
            delimiter=args.delimiter,
            encoding=args.encoding,
        )
        total_rows = len(rows)
        suggested_batches = suggest_batches(total_rows)

        print(f"Total data rows in CSV: {total_rows}")
        print(
            "Suggested number of batches for up to "
            f"{DEFAULT_MAX_ROWS_PER_BATCH} rows each: {suggested_batches}"
        )
        return 0

    output_dir, total_rows, batch_details = split_csv(
        csv_file=args.csv_file,
        batches=args.batches,
        delimiter=args.delimiter,
        encoding=args.encoding,
    )

    print(f"Batches created in: {output_dir}")
    print(f"Total data rows in CSV: {total_rows}")
    for batch_file, row_count in batch_details:
        print(f"{batch_file.name}: {row_count} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
