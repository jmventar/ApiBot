import json

import pytest

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
