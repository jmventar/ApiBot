import json

import pytest

from src.utils.csv_batch_utils import (
    get_batch_sizes_for_max_rows,
    load_csv_rows,
    split_csv,
    split_csv_by_max_rows,
    suggest_batches,
)
from src.utils.json_utils import parse, store_jsonl_append, cleanup
from src.utils.csv_utils import parse as csv_parse


# --- json_utils.parse ---

def test_json_parse(tmp_path):
    filename = str(tmp_path / "test.json")
    data = {"key": "value"}
    with open(filename, "w") as f:
        json.dump(data, f)

    result = parse(filename)

    assert result == data


# --- json_utils.store_jsonl_append ---

def test_store_jsonl_append(tmp_path):
    filename = str(tmp_path / "test_store.jsonl")
    first_batch = [{"a": 1}, {"b": 2}]
    second_batch = [{"c": 3}]

    store_jsonl_append(filename, first_batch)
    store_jsonl_append(filename, second_batch)

    with open(filename, "r") as f:
        lines = [json.loads(line) for line in f if line.strip()]
    assert lines == [{"a": 1}, {"b": 2}, {"c": 3}]


# --- json_utils.cleanup ---

def test_cleanup_arrays_to_set(tmp_path):
    filename = str(tmp_path / "test.json")
    data = [
        {"test": 1, "test1": 1, "test2": 2, "test3": 5, "test4": 6},
        {"test": 3, "test1": 4, "test2": 5, "test3": 6, "test5": 7, "test7": 8},
        {"test": 9, "test1": 4, "test2": 1, "test3": 1, "test6": 2},
    ]

    with open(filename, "w") as f:
        json.dump(data, f)

    result = cleanup(filename)

    assert len(result) == 9
    expected = {1, 2, 3, 4, 5, 6, 7, 8, 9}
    assert result == expected


# --- csv_utils.parse ---

def test_csv_parse_single_column(tmp_path):
    csv_file = tmp_path / "single.csv"
    csv_file.write_text("post_num\n25\n46\n74\n")

    result = csv_parse(str(csv_file))

    assert len(result) == 3
    assert result[0] == {"post_num": "25"}
    assert result[1] == {"post_num": "46"}
    assert result[2] == {"post_num": "74"}


def test_csv_parse_multiple_columns(tmp_path):
    csv_file = tmp_path / "multi.csv"
    csv_file.write_text("a, b, c\n1,2,3\nx,y,z\n")

    result = csv_parse(str(csv_file))

    assert len(result) == 2
    assert result[0] == {"a": "1", "b": "2", "c": "3"}
    assert result[1] == {"a": "x", "b": "y", "c": "z"}


def test_csv_parse_rejects_non_csv(tmp_path):
    json_file = tmp_path / "data.json"
    json_file.write_text('{"key": "value"}')

    with pytest.raises(Exception, match="Only csv files allowed"):
        csv_parse(str(json_file))


def test_csv_parse_empty(tmp_path):
    csv_file = tmp_path / "empty.csv"
    csv_file.write_text("col1,col2\n")

    result = csv_parse(str(csv_file))

    assert result == []


# --- csv_batch_utils ---

def test_get_batch_sizes_for_max_rows():
    assert get_batch_sizes_for_max_rows(total_rows=5, max_rows_per_batch=2) == [2, 2, 1]


def test_load_csv_rows_strips_utf8_bom_from_header(tmp_path):
    csv_file = tmp_path / "bom.csv"
    csv_file.write_text("\ufeffid,name\n1,Alice\n", encoding="utf-8")

    header, rows = load_csv_rows(csv_file, delimiter=",", encoding="utf-8")

    assert header == ["id", "name"]
    assert rows == [["1", "Alice"]]


def test_load_csv_rows_rejects_empty_csv(tmp_path):
    csv_file = tmp_path / "empty.csv"
    csv_file.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="empty"):
        load_csv_rows(csv_file, delimiter=",", encoding="utf-8")


def test_load_csv_rows_rejects_header_only_csv(tmp_path):
    csv_file = tmp_path / "header_only.csv"
    csv_file.write_text("id,name\n", encoding="utf-8")

    with pytest.raises(ValueError, match="no data rows"):
        load_csv_rows(csv_file, delimiter=",", encoding="utf-8")


def test_split_csv_by_max_rows_writes_numbered_batches(tmp_path):
    csv_file = tmp_path / "contacts.csv"
    csv_file.write_text("id,name\n1,Alice\n2,Bob\n3,Carla\n", encoding="utf-8")
    output_dir = tmp_path / "upload_run_001"

    created_dir, total_rows, batch_details = split_csv_by_max_rows(
        csv_file=csv_file,
        max_rows_per_batch=2,
        delimiter=",",
        encoding="utf-8",
        output_dir=output_dir,
    )

    assert created_dir == output_dir
    assert total_rows == 3
    assert [(batch_file.name, row_count) for batch_file, row_count in batch_details] == [
        ("contacts_batch_001.csv", 2),
        ("contacts_batch_002.csv", 1),
    ]
    assert output_dir.joinpath("contacts_batch_001.csv").read_text(encoding="utf-8") == (
        "id,name\n1,Alice\n2,Bob\n"
    )
    assert output_dir.joinpath("contacts_batch_002.csv").read_text(encoding="utf-8") == (
        "id,name\n3,Carla\n"
    )


def test_suggest_batches_uses_default_max_rows():
    assert suggest_batches(total_rows=10001) == 3


def test_split_csv_with_explicit_batches_distributes_rows_evenly(tmp_path):
    csv_file = tmp_path / "contacts.csv"
    csv_file.write_text(
        "id,name\n1,Alice\n2,Bob\n3,Carla\n4,David\n5,Emma\n", encoding="utf-8"
    )
    output_dir = tmp_path / "manual_batches"

    created_dir, total_rows, batch_details = split_csv(
        csv_file=csv_file,
        batches=2,
        delimiter=",",
        encoding="utf-8",
        output_dir=output_dir,
    )

    assert created_dir == output_dir
    assert total_rows == 5
    assert [(batch_file.name, row_count) for batch_file, row_count in batch_details] == [
        ("contacts_batch_001.csv", 3),
        ("contacts_batch_002.csv", 2),
    ]
