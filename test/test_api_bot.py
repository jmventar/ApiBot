import json
import os

import pytest
from unittest.mock import MagicMock, patch

from src.api_bot.api_bot import ApiBot, find_placeholders
from src.main import parse_args, validate_args


class MockArgs:
    def __init__(
        self,
        url="http://example.com/{{0}}",
        source="json_array",
        payload=None,
        dry=False,
        method="GET",
        delay=0,
        token="test-token",
        avoid_storage=False,
        clean=False,
        file="input.json",
        upload_csv=False,
        upload_field="csvFile",
        max_rows_per_upload=5000,
        encoding="utf-8",
        delimiter=",",
    ):
        self.url = url
        self.source = source
        self.payload = payload
        self.dry = dry
        self.method = method
        self.delay = delay
        self.token = token
        self.avoid_storage = avoid_storage
        self.clean = clean
        self.file = file
        self.upload_csv = upload_csv
        self.upload_field = upload_field
        self.max_rows_per_upload = max_rows_per_upload
        self.encoding = encoding
        self.delimiter = delimiter


def _read_jsonl(filename):
    """Read a JSONL file and return a list of parsed objects."""
    with open(filename, "r") as f:
        return [json.loads(line) for line in f if line.strip()]


# ============================================================
# parse_args
# ============================================================

def test_parse_args_upload_csv_defaults_to_post():
    args = parse_args(
        [
            "--file",
            "contacts.csv",
            "--upload-csv",
            "--url",
            "https://example.com/api/v3/upload-csv",
        ]
    )

    assert args.upload_csv is True
    assert args.method == "POST"
    assert args.max_rows_per_upload == 5000
    assert args.upload_field == "csvFile"
    assert args.encoding == "utf-8"
    assert args.delimiter == ","


# ============================================================
# replace_elements
# ============================================================

# --- JSON_ARRAY_SOURCE branch ---

def test_replace_elements_json_array():
    args = MockArgs(url="http://example.com/items/{{0}}", source="json_array")
    bot = ApiBot(args, [], ["0"])
    assert bot.replace_elements(42) == "http://example.com/items/42"


def test_replace_elements_json_array_string_value():
    args = MockArgs(url="http://example.com/items/{{0}}/details", source="json_array")
    bot = ApiBot(args, [], ["0"])
    assert bot.replace_elements("abc") == "http://example.com/items/abc/details"


# --- --clean branch (single placeholder, scalar value) ---

def test_replace_elements_clean_single_placeholder():
    args = MockArgs(url="http://example.com/posts/{{post_num}}", source="json", clean=True)
    bot = ApiBot(args, [], ["post_num"])
    assert bot.replace_elements(99) == "http://example.com/posts/99"


def test_replace_elements_clean_string_value():
    args = MockArgs(url="http://example.com/users/{{id}}/profile", source="json", clean=True)
    bot = ApiBot(args, [], ["id"])
    assert bot.replace_elements("u-123") == "http://example.com/users/u-123/profile"


# --- default branch (multi-placeholder, dict value) ---

def test_replace_elements_single_placeholder_dict():
    args = MockArgs(url="http://example.com/posts/{{id}}", source="json")
    bot = ApiBot(args, [], ["id"])
    assert bot.replace_elements({"id": 7}) == "http://example.com/posts/7"


def test_replace_elements_multiple_placeholders():
    args = MockArgs(url="http://example.com/posts/{{id}}/{{name}}/{{map}}", source="json")
    bot = ApiBot(args, [], ["id", "name", "map"])
    value = {"id": 1, "name": "Downtown", "map": "CritCity"}
    assert bot.replace_elements(value) == "http://example.com/posts/1/Downtown/CritCity"


def test_replace_elements_csv_multiple_placeholders():
    args = MockArgs(url="http://example.com/q?a={{r1}}&b={{r2}}&c={{r3}}", source="csv")
    bot = ApiBot(args, [], ["r1", "r2", "r3"])
    value = {"r1": "x", "r2": "y", "r3": "z"}
    assert bot.replace_elements(value) == "http://example.com/q?a=x&b=y&c=z"


# ============================================================
# replace_payload_elements
# ============================================================

def test_replace_payload_none():
    args = MockArgs(payload=None, source="json")
    bot = ApiBot(args, [], ["id"])
    assert bot.replace_payload_elements({"id": 7}) is None


def test_replace_payload_json_source():
    args = MockArgs(
        source="json",
        payload='{"id": "{{id}}"}',
    )
    bot = ApiBot(args, [], ["id"])
    payload = bot.replace_payload_elements({"id": 7})
    assert payload == {"id": "7"}


def test_replace_payload_csv_source():
    args = MockArgs(
        source="csv",
        payload='{"replace_1": "{{replace_1}}", "replace_2": "{{replace_2}}"}',
    )
    bot = ApiBot(args, [], ["replace_1", "replace_2"])
    payload = bot.replace_payload_elements({"replace_1": "foo", "replace_2": "bar"})
    assert payload == {"replace_1": "foo", "replace_2": "bar"}


def test_replace_payload_json_array():
    args = MockArgs(
        source="json_array",
        payload='{"scheduleId": "{{0}}"}',
    )
    bot = ApiBot(args, [], ["0"])
    payload = bot.replace_payload_elements(123)
    assert payload == {"scheduleId": "123"}


def test_replace_payload_multiple_placeholders():
    args = MockArgs(
        source="json",
        payload='{"id": "{{id}}", "name": "{{name}}", "map": "{{map}}"}',
    )
    bot = ApiBot(args, [], ["id", "name", "map"])
    payload = bot.replace_payload_elements({"id": 1, "name": "Downtown", "map": "CritCity"})
    assert payload == {"id": "1", "name": "Downtown", "map": "CritCity"}


def test_replace_payload_special_chars_remain_valid_json():
    args = MockArgs(
        source="csv",
        payload='{"name": "{{name}}"}',
    )
    bot = ApiBot(args, [], ["name"])
    payload = bot.replace_payload_elements({"name": 'A "quoted" value\nnext line'})
    assert payload == {"name": 'A "quoted" value\nnext line'}


def test_replace_payload_invalid_json_template_returns_none():
    args = MockArgs(source="json", payload='{"id": {{id}}}')
    bot = ApiBot(args, [], ["id"])
    assert bot.replace_payload_elements({"id": 7}) is None


# ============================================================
# find_placeholders
# ============================================================

def test_find_placeholders_single():
    assert find_placeholders("http://example.com/posts/{{id}}") == ["id"]


def test_find_placeholders_multiple():
    assert find_placeholders("http://example.com/{{a}}/{{b}}/{{c}}") == ["a", "b", "c"]


def test_find_placeholders_json_array():
    assert find_placeholders("http://example.com/{{0}}", jsonArray=True) == ["0"]


def test_find_placeholders_url_none():
    assert find_placeholders(None) == ["0"]


def test_find_placeholders_url_none_json_array():
    assert find_placeholders(None, jsonArray=True) == ["0"]


def test_find_placeholders_no_placeholders_exits():
    with pytest.raises(SystemExit):
        find_placeholders("http://example.com/no-placeholders")


def test_find_placeholders_allows_static_url_for_upload_mode():
    assert find_placeholders("http://example.com/upload-csv", allow_static=True) == []


def test_find_placeholders_upload_mode_ignores_json_array_source():
    assert (
        find_placeholders(
            "http://example.com/upload-csv",
            jsonArray=True,
            allow_static=True,
        )
        == []
    )


# ============================================================
# validate_args
# ============================================================

def test_validate_args_clean_csv_exits():
    args = MockArgs(source="csv", clean=True)
    with pytest.raises(SystemExit):
        validate_args(args, ["col1"])


def test_validate_args_clean_multiple_placeholders_exits():
    args = MockArgs(source="json", clean=True)
    with pytest.raises(SystemExit):
        validate_args(args, ["id", "name"])


def test_validate_args_no_url_does_not_exit():
    args = MockArgs(url=None)
    validate_args(args, ["id"])


def test_validate_args_valid_clean_single_placeholder():
    args = MockArgs(source="json", clean=True)
    validate_args(args, ["id"])


def test_validate_args_valid_no_clean():
    args = MockArgs(source="json", clean=False)
    validate_args(args, ["id", "name"])


def test_validate_args_clean_multiple_payload_placeholders_exits():
    args = MockArgs(source="json", clean=True, payload='{"a":"{{a}}","b":"{{b}}"}')
    with pytest.raises(SystemExit):
        validate_args(args, ["id"])


def test_validate_args_upload_csv_requires_csv_file():
    args = MockArgs(
        file="input.json",
        source="json",
        upload_csv=True,
        url="http://example.com/upload-csv",
    )

    with pytest.raises(SystemExit):
        validate_args(args, [])


def test_validate_args_upload_csv_requires_url():
    args = MockArgs(file="contacts.csv", upload_csv=True, url=None)

    with pytest.raises(SystemExit):
        validate_args(args, [])


def test_validate_args_upload_csv_allows_static_url():
    args = MockArgs(
        file="contacts.csv",
        source="json",
        upload_csv=True,
        url="http://example.com/upload-csv",
    )

    validate_args(args, [])


def test_validate_args_upload_csv_rejects_placeholder_url():
    args = MockArgs(
        file="contacts.csv",
        source="json",
        upload_csv=True,
        url="http://example.com/upload-csv/{{id}}",
    )

    with pytest.raises(SystemExit):
        validate_args(args, ["id"])


def test_validate_args_upload_csv_requires_non_empty_upload_field():
    args = MockArgs(
        file="contacts.csv",
        upload_csv=True,
        url="http://example.com/upload-csv",
        upload_field="",
    )

    with pytest.raises(SystemExit):
        validate_args(args, [])


def test_validate_args_upload_csv_requires_single_character_delimiter():
    args = MockArgs(
        file="contacts.csv",
        upload_csv=True,
        url="http://example.com/upload-csv",
        delimiter="::",
    )

    with pytest.raises(SystemExit):
        validate_args(args, [])


def test_validate_args_upload_csv_requires_known_encoding():
    args = MockArgs(
        file="contacts.csv",
        upload_csv=True,
        url="http://example.com/upload-csv",
        encoding="definitely-not-a-real-encoding",
    )

    with pytest.raises(SystemExit):
        validate_args(args, [])


# ============================================================
# register_success / register_failure / _format_failures_summary
# ============================================================

def test_register_success():
    bot = ApiBot(MockArgs(), [], ["0"])
    assert bot._successful_requests == 0
    bot.register_success()
    bot.register_success()
    assert bot._successful_requests == 2


def test_register_failure_counts_by_status():
    bot = ApiBot(MockArgs(), [], ["0"])
    bot.register_failure(404)
    bot.register_failure(404)
    bot.register_failure(500)
    assert bot._failed_by_status == {404: 2, 500: 1}


def test_format_failures_summary_empty():
    bot = ApiBot(MockArgs(), [], ["0"])
    assert bot._format_failures_summary() == ""


def test_format_failures_summary_single_code():
    bot = ApiBot(MockArgs(), [], ["0"])
    bot.register_failure(404)
    summary = bot._format_failures_summary()
    assert "404:1" in summary
    assert "Failures:" in summary


def test_format_failures_summary_multiple_codes_sorted():
    bot = ApiBot(MockArgs(), [], ["0"])
    bot.register_failure(500)
    bot.register_failure(500)
    bot.register_failure(400)
    summary = bot._format_failures_summary()
    pos_400 = summary.index("400:1")
    pos_500 = summary.index("500:2")
    assert pos_400 < pos_500


# ============================================================
# _persist_to_storage
# ============================================================

def test_persist_to_storage(tmp_path):
    args = MockArgs(avoid_storage=False)
    log_file = str(tmp_path / "test_log.jsonl")
    result_file = str(tmp_path / "test_result.jsonl")

    bot = ApiBot(args, ["elem1"], ["0"], log_filename=log_file, result_filename=result_file)
    bot.response_log = [{"log": "data"}]
    bot.response_data = [{"result": "data"}]

    bot._persist_to_storage()

    assert _read_jsonl(log_file) == [{"log": "data"}]
    assert _read_jsonl(result_file) == [{"result": "data"}]


def test_persist_incremental_append(tmp_path):
    """Successive persists only append the delta, preserving earlier records."""
    args = MockArgs(avoid_storage=False)
    log_file = str(tmp_path / "test_incremental_log.jsonl")
    result_file = str(tmp_path / "test_incremental_result.jsonl")

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


def test_persist_to_storage_avoid(tmp_path):
    args = MockArgs(avoid_storage=True)
    log_file = str(tmp_path / "test_log_avoid.jsonl")
    result_file = str(tmp_path / "test_result_avoid.jsonl")

    bot = ApiBot(args, ["elem1"], ["0"], log_filename=log_file, result_filename=result_file)
    bot.response_log = [{"log": "data"}]
    bot.response_data = [{"result": "data"}]

    bot._persist_to_storage()

    assert not os.path.exists(log_file)
    assert not os.path.exists(result_file)


# ============================================================
# log_response
# ============================================================

def test_log_response_appends_json_object_as_single_result():
    bot = ApiBot(MockArgs(), [], ["0"])

    response = MagicMock()
    response.status_code = 200
    response.headers = {"content-type": "application/json"}
    response.json.return_value = {"key": "value"}
    response.content = b'{"key":"value"}'

    bot.log_response("GET", "http://example.com/items/1", 1, response)

    assert bot.response_data == [{"key": "value"}]


# ============================================================
# run (integration-level)
# ============================================================


def test_run_passes_payload_to_execute():
    args = MockArgs(
        source="json",
        method="POST",
        url="http://example.com/posts/{{id}}",
        payload='{"id":"{{id}}","name":"{{name}}"}',
    )
    elements = [{"id": 1, "name": "one"}, {"id": 2, "name": "two"}]
    bot = ApiBot(args, elements, ["id"])

    with patch.object(ApiBot, "execute", return_value=MagicMock(status_code=200)) as mock_execute:
        with patch.object(ApiBot, "log_response"):
            with patch.object(bot, "_persist_to_storage"):
                bot.run()

    assert mock_execute.call_args_list[0].args[3] == {"id": "1", "name": "one"}
    assert mock_execute.call_args_list[1].args[3] == {"id": "2", "name": "two"}


def test_run_passes_none_when_no_payload():
    args = MockArgs(
        source="json",
        method="POST",
        url="http://example.com/posts/{{id}}",
        payload=None,
    )
    elements = [{"id": 1}]
    bot = ApiBot(args, elements, ["id"])

    with patch.object(ApiBot, "execute", return_value=MagicMock(status_code=200)) as mock_execute:
        with patch.object(ApiBot, "log_response"):
            with patch.object(bot, "_persist_to_storage"):
                bot.run()

    assert mock_execute.call_args_list[0].args[3] is None


@patch("src.api_bot.api_bot.requests.request")
def test_run_upload_csv_splits_batches_and_posts_multipart_files(
    mock_request, tmp_path
):
    csv_file = tmp_path / "contacts.csv"
    csv_file.write_text("id,name\n1,Alice\n2,Bob\n3,Carla\n", encoding="utf-8")

    args = MockArgs(
        source="json",
        method="POST",
        url="http://example.com/upload-csv",
        file=str(csv_file),
        upload_csv=True,
        max_rows_per_upload=2,
    )
    bot = ApiBot(args, [str(csv_file)], [])

    mock_response = MagicMock()
    mock_response.status_code = 202
    mock_response.headers = {"content-type": "text/plain"}
    mock_response.content = b"accepted"
    mock_request.return_value = mock_response

    batch_dir = tmp_path / "upload_run"
    with patch("src.api_bot.api_bot.tempfile.mkdtemp", return_value=str(batch_dir)):
        with patch.object(ApiBot, "log_response"):
            with patch.object(bot, "_persist_to_storage"):
                bot.run()

    assert mock_request.call_count == 2

    first_call = mock_request.call_args_list[0]
    assert first_call.args == ("POST", "http://example.com/upload-csv")
    assert first_call.kwargs["headers"] == {"Authorization": "Bearer test-token"}
    assert first_call.kwargs["data"] == {}
    assert first_call.kwargs["files"][0][0] == "csvFile"
    assert first_call.kwargs["files"][0][1][0] == "contacts_batch_001.csv"
    assert first_call.kwargs["files"][0][1][2] == "application/octet-stream"

    second_call = mock_request.call_args_list[1]
    assert second_call.kwargs["files"][0][1][0] == "contacts_batch_002.csv"

    assert batch_dir.joinpath("contacts_batch_001.csv").read_text(encoding="utf-8") == (
        "id,name\n1,Alice\n2,Bob\n"
    )
    assert batch_dir.joinpath("contacts_batch_002.csv").read_text(encoding="utf-8") == (
        "id,name\n3,Carla\n"
    )

@patch("src.api_bot.api_bot.requests.request")
def test_run_calls_persist_periodically(mock_request, tmp_path):
    elements = [f"elem{i}" for i in range(55)]
    args = MockArgs(url="http://example.com/{{0}}")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "application/json"}
    mock_response.json.return_value = {"key": "value"}
    mock_response.content = b'{"key": "value"}'
    mock_request.return_value = mock_response

    log_file = str(tmp_path / "periodic_log.jsonl")
    result_file = str(tmp_path / "periodic_result.jsonl")
    bot = ApiBot(args, elements, ["0"], log_filename=log_file, result_filename=result_file)

    with patch.object(bot, "_persist_to_storage") as mock_persist:
        bot.run()

        # Should be called once at count 50 and once at the end
        assert mock_persist.call_count == 2
