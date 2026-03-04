import json

from src.utils.json_utils import parse, store_jsonl_append, cleanup


def test_load_config(tmp_path):
    # Arrange
    filename = str(tmp_path / "test.json")
    data = {"key": "value"}
    with open(filename, "w") as f:
        json.dump(data, f)

    # Act
    result = parse(filename)

    # Assert
    assert result == data


def test_store_jsonl_append(tmp_path):
    # Arrange
    filename = str(tmp_path / "test_store.jsonl")
    first_batch = [{"a": 1}, {"b": 2}]
    second_batch = [{"c": 3}]

    # Act
    store_jsonl_append(filename, first_batch)
    store_jsonl_append(filename, second_batch)

    # Assert
    with open(filename, "r") as f:
        lines = [json.loads(line) for line in f if line.strip()]
    assert lines == [{"a": 1}, {"b": 2}, {"c": 3}]


def test_arrays_to_set(tmp_path):
    # Arrange
    filename = str(tmp_path / "test.json")
    data = [
        {"test": 1, "test1": 1, "test2": 2, "test3": 5, "test4": 6},
        {"test": 3, "test1": 4, "test2": 5, "test3": 6, "test5": 7, "test7": 8},
        {"test": 9, "test1": 4, "test2": 1, "test3": 1, "test6": 2},
    ]

    with open(filename, "w") as f:
        json.dump(data, f)

    # Act
    result = cleanup(filename)

    # Assert
    assert len(result) == 9
    expected = {1, 2, 3, 4, 5, 6, 7, 8, 9}
    assert result == expected
