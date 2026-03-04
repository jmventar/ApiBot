import os
import json
from unittest.mock import MagicMock, patch
from src.api_bot.api_bot import ApiBot


class MockArgs:
    def __init__(
        self,
        url="http://example.com/{{0}}",
        source="json_array",
        dry=False,
        method="GET",
        delay=0,
        token="test-token",
        avoid_storage=False,
        clean=False
    ):
        self.url = url
        self.source = source
        self.dry = dry
        self.method = method
        self.delay = delay
        self.token = token
        self.avoid_storage = avoid_storage
        self.clean = clean


def _read_jsonl(filename):
    """Read a JSONL file and return a list of parsed objects."""
    with open(filename, "r") as f:
        return [json.loads(line) for line in f if line.strip()]


def test_persist_to_storage():
    # Arrange
    args = MockArgs(avoid_storage=False)
    log_file = "test_log.jsonl"
    result_file = "test_result.jsonl"

    for f in (log_file, result_file):
        if os.path.exists(f):
            os.remove(f)

    bot = ApiBot(args, ["elem1"], ["0"], log_filename=log_file, result_filename=result_file)
    bot.response_log = [{"log": "data"}]
    bot.response_data = [{"result": "data"}]

    # Act
    bot._persist_to_storage()

    # Assert
    assert os.path.exists(log_file)
    assert os.path.exists(result_file)

    assert _read_jsonl(log_file) == [{"log": "data"}]
    assert _read_jsonl(result_file) == [{"result": "data"}]

    # Cleanup
    os.remove(log_file)
    os.remove(result_file)


def test_persist_incremental_append():
    """Successive persists only append the delta, preserving earlier records."""
    args = MockArgs(avoid_storage=False)
    log_file = "test_incremental_log.jsonl"
    result_file = "test_incremental_result.jsonl"

    for f in (log_file, result_file):
        if os.path.exists(f):
            os.remove(f)

    bot = ApiBot(args, ["elem1"], ["0"], log_filename=log_file, result_filename=result_file)

    # First batch
    bot.response_log = [{"batch": 1, "idx": 0}, {"batch": 1, "idx": 1}]
    bot.response_data = [{"d": "a"}]
    bot._persist_to_storage()

    assert _read_jsonl(log_file) == [{"batch": 1, "idx": 0}, {"batch": 1, "idx": 1}]
    assert _read_jsonl(result_file) == [{"d": "a"}]

    # Second batch — append more items to the in-memory lists
    bot.response_log.append({"batch": 2, "idx": 2})
    bot.response_data.append({"d": "b"})
    bot._persist_to_storage()

    # File should contain ALL records (old + new)
    assert _read_jsonl(log_file) == [
        {"batch": 1, "idx": 0},
        {"batch": 1, "idx": 1},
        {"batch": 2, "idx": 2},
    ]
    assert _read_jsonl(result_file) == [{"d": "a"}, {"d": "b"}]

    # Third persist with no new data — file should remain unchanged
    bot._persist_to_storage()
    assert _read_jsonl(log_file) == [
        {"batch": 1, "idx": 0},
        {"batch": 1, "idx": 1},
        {"batch": 2, "idx": 2},
    ]

    # Cleanup
    os.remove(log_file)
    os.remove(result_file)


def test_persist_to_storage_avoid():
    # Arrange
    args = MockArgs(avoid_storage=True)
    log_file = "test_log_avoid.jsonl"
    result_file = "test_result_avoid.jsonl"

    for f in (log_file, result_file):
        if os.path.exists(f):
            os.remove(f)

    bot = ApiBot(args, ["elem1"], ["0"], log_filename=log_file, result_filename=result_file)
    bot.response_log = [{"log": "data"}]
    bot.response_data = [{"result": "data"}]

    # Act
    bot._persist_to_storage()

    # Assert
    assert not os.path.exists(log_file)
    assert not os.path.exists(result_file)


@patch("src.api_bot.api_bot.requests.request")
def test_run_calls_persist_periodically(mock_request):
    # Arrange
    elements = [f"elem{i}" for i in range(55)]
    args = MockArgs(url="http://example.com/{{0}}")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "application/json"}
    mock_response.json.return_value = {"key": "value"}
    mock_response.content = b'{"key": "value"}'
    mock_request.return_value = mock_response

    bot = ApiBot(args, elements, ["0"], log_filename="periodic_log.jsonl", result_filename="periodic_result.jsonl")

    with patch.object(bot, "_persist_to_storage") as mock_persist:
        bot.run()

        # Should be called once at count 50 and once at the end
        assert mock_persist.call_count == 2

    for f in ("periodic_log.jsonl", "periodic_result.jsonl"):
        if os.path.exists(f):
            os.remove(f)
