from __future__ import annotations

import csv
import math
from pathlib import Path

from constants import DEFAULT_MAX_ROWS_PER_CSV_BATCH


def get_batch_sizes(total_rows: int, batches: int) -> list[int]:
    if batches <= 0:
        raise ValueError("The number of batches must be greater than 0.")

    if total_rows <= 0:
        raise ValueError("The CSV file has no data rows to split.")

    if batches > total_rows:
        raise ValueError(
            "The number of batches cannot be greater than the number of data rows."
        )

    base_size, remainder = divmod(total_rows, batches)
    return [base_size + (1 if index < remainder else 0) for index in range(batches)]


def suggest_batches(
    total_rows: int, max_rows_per_batch: int = DEFAULT_MAX_ROWS_PER_CSV_BATCH
) -> int:
    if max_rows_per_batch <= 0:
        raise ValueError("The maximum rows per batch must be greater than 0.")

    return max(1, math.ceil(total_rows / max_rows_per_batch))


def load_csv_rows(
    csv_file: Path, delimiter: str = ",", encoding: str = "utf-8"
) -> tuple[list[str], list[list[str]]]:
    if not csv_file.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_file}")

    if csv_file.suffix.lower() != ".csv":
        raise ValueError(f"Expected a .csv file, got: {csv_file.name}")

    with csv_file.open("r", newline="", encoding=encoding) as source_file:
        reader = csv.reader(source_file, delimiter=delimiter)

        try:
            header = next(reader)
        except StopIteration as error:
            raise ValueError("The CSV file is empty.") from error

        rows = list(reader)

    if not rows:
        raise ValueError("The CSV file has no data rows to split.")

    if header:
        header[0] = header[0].lstrip("\ufeff")

    return header, rows


def _write_batch(
    header: list[str],
    rows: list[list[str]],
    output_dir: Path,
    file_stem: str,
    batch_index: int,
    delimiter: str = ",",
    output_encoding: str = "utf-8",
) -> Path:
    output_file = output_dir / f"{file_stem}_batch_{batch_index:03d}.csv"
    with output_file.open("w", newline="", encoding=output_encoding) as batch_file:
        writer = csv.writer(batch_file, delimiter=delimiter)
        writer.writerow(header)
        writer.writerows(rows)
    return output_file


def stream_csv_batches(
    csv_file: Path,
    max_rows_per_batch: int = DEFAULT_MAX_ROWS_PER_CSV_BATCH,
    delimiter: str = ",",
    encoding: str = "utf-8",
    output_dir: Path | None = None,
    output_encoding: str = "utf-8",
) -> tuple[Path, int, list[tuple[Path, int]]]:
    """Stream through a CSV file writing batch files incrementally.

    Rows are processed one at a time so only up to max_rows_per_batch rows
    are held in memory at once, regardless of the total file size.
    """
    if not csv_file.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_file}")

    if csv_file.suffix.lower() != ".csv":
        raise ValueError(f"Expected a .csv file, got: {csv_file.name}")

    target_dir = output_dir or csv_file.parent / csv_file.stem
    target_dir.mkdir(parents=True, exist_ok=True)

    batch_details: list[tuple[Path, int]] = []
    total_rows = 0
    batch_index = 0
    current_batch: list[list[str]] = []

    with csv_file.open("r", newline="", encoding=encoding) as source_file:
        reader = csv.reader(source_file, delimiter=delimiter)

        try:
            header = next(reader)
        except StopIteration as error:
            raise ValueError("The CSV file is empty.") from error

        if header:
            header[0] = header[0].lstrip("\ufeff")

        for row in reader:
            current_batch.append(row)
            total_rows += 1
            if len(current_batch) >= max_rows_per_batch:
                batch_index += 1
                batch_file = _write_batch(
                    header, current_batch, target_dir, csv_file.stem,
                    batch_index, delimiter, output_encoding,
                )
                batch_details.append((batch_file, len(current_batch)))
                current_batch = []

        if current_batch:
            batch_index += 1
            batch_file = _write_batch(
                header, current_batch, target_dir, csv_file.stem,
                batch_index, delimiter, output_encoding,
            )
            batch_details.append((batch_file, len(current_batch)))

    if total_rows == 0:
        raise ValueError("The CSV file has no data rows to split.")

    return target_dir, total_rows, batch_details


def write_csv_batches(
    header: list[str],
    rows: list[list[str]],
    batch_sizes: list[int],
    output_dir: Path,
    file_stem: str,
    delimiter: str = ",",
    output_encoding: str = "utf-8",
) -> list[tuple[Path, int]]:
    output_dir.mkdir(parents=True, exist_ok=True)

    start = 0
    batch_details: list[tuple[Path, int]] = []

    for index, batch_size in enumerate(batch_sizes, start=1):
        end = start + batch_size
        batch_rows = rows[start:end]
        start = end

        output_file = output_dir / f"{file_stem}_batch_{index:03d}.csv"
        with output_file.open("w", newline="", encoding=output_encoding) as batch_file:
            writer = csv.writer(batch_file, delimiter=delimiter)
            writer.writerow(header)
            writer.writerows(batch_rows)

        batch_details.append((output_file, len(batch_rows)))

    return batch_details


def build_csv_batches_from_rows(
    csv_file: Path,
    header: list[str],
    rows: list[list[str]],
    max_rows_per_batch: int = DEFAULT_MAX_ROWS_PER_CSV_BATCH,
    output_dir: Path | None = None,
    delimiter: str = ",",
    output_encoding: str = "utf-8",
) -> tuple[Path, int, list[tuple[Path, int]]]:
    batch_sizes = get_batch_sizes(
        len(rows),
        suggest_batches(len(rows), max_rows_per_batch),
    )
    target_dir = output_dir or csv_file.parent / csv_file.stem
    batch_details = write_csv_batches(
        header=header,
        rows=rows,
        batch_sizes=batch_sizes,
        output_dir=target_dir,
        file_stem=csv_file.stem,
        delimiter=delimiter,
        output_encoding=output_encoding,
    )
    return target_dir, len(rows), batch_details


def split_csv(
    csv_file: Path,
    batches: int,
    delimiter: str = ",",
    encoding: str = "utf-8",
    output_dir: Path | None = None,
    output_encoding: str = "utf-8",
) -> tuple[Path, int, list[tuple[Path, int]]]:
    header, rows = load_csv_rows(
        csv_file=csv_file,
        delimiter=delimiter,
        encoding=encoding,
    )
    batch_sizes = get_batch_sizes(len(rows), batches)
    target_dir = output_dir or csv_file.parent / csv_file.stem
    batch_details = write_csv_batches(
        header=header,
        rows=rows,
        batch_sizes=batch_sizes,
        output_dir=target_dir,
        file_stem=csv_file.stem,
        delimiter=delimiter,
        output_encoding=output_encoding,
    )
    return target_dir, len(rows), batch_details


def split_csv_by_max_rows(
    csv_file: Path,
    max_rows_per_batch: int = DEFAULT_MAX_ROWS_PER_CSV_BATCH,
    delimiter: str = ",",
    encoding: str = "utf-8",
    output_dir: Path | None = None,
    output_encoding: str = "utf-8",
) -> tuple[Path, int, list[tuple[Path, int]]]:
    return stream_csv_batches(
        csv_file=csv_file,
        max_rows_per_batch=max_rows_per_batch,
        delimiter=delimiter,
        encoding=encoding,
        output_dir=output_dir,
        output_encoding=output_encoding,
    )
