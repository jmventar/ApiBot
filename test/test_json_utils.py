import os
import json

from src.utils.json_utils import load_config, store_config, arrays_to_set


def test_load_config():
    # Arrange
    filename = "test.json"
    data = {"key": "value"}
    with open(filename, "w") as f:
        json.dump(data, f)

    # Act
    result = load_config(filename)

    # Assert
    assert result == data

    # Cleanup
    os.remove(filename)


def test_store_config():
    # Arrange
    filename = "test.json"
    data = {"key": "value"}

    # Act
    store_config(filename, data)

    # Assert
    with open(filename, "r") as f:
        result = json.load(f)
    assert result == data

    # Cleanup
    os.remove(filename)


def test_arrays_to_set():
    # Arrange
    filename = "test.json"
    data = [
        {"test": 1, "test1": 1, "test2": 2, "test3": 5, "test4": 6},
        {"test": 3, "test1": 4, "test2": 5, "test3": 6, "test5": 7, "test7": 8},
        {"test": 9, "test1": 4, "test2": 1, "test3": 1, "test6": 2},
    ]

    with open(filename, "w") as f:
        json.dump(data, f)

    # Act
    result = arrays_to_set(filename)

    # Assert
    assert len(result) == 9
    expected = {1, 2, 3, 4, 5, 6, 7, 8, 9}
    assert result == expected

    # Cleanup
    os.remove(filename)
