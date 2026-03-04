# AGENTS.md

Guidelines for AI coding agents working on this repository.

## Project overview

**ApiBot** is a Python CLI tool for running batches of HTTP requests, similar to Postman's "Run Collection" feature. It reads input data from JSON, JSON-array, or CSV files, replaces URL placeholders with values from the data, and executes the requests sequentially with optional delay, logging, and result storage.

## Project structure

```
src/
  main.py                  # Entry point: argument parsing, orchestration, result storage
  constants.py             # Shared constants (source types, datetime format, content types)
  api_bot/
    api_bot.py             # Core ApiBot class (request execution, URL placeholder replacement)
    response_log.py        # ResponseLog data class for structured logging
  utils/
    csv_utils.py           # CSV file parser (DictReader-based)
    json_utils.py          # JSON file parser, array cleanup/dedup, JSONL append storage
test/
  test_utils.py            # Unit tests for JSON and CSV parsers/utilities
  test_api_bot.py          # Unit tests for ApiBot (replacement, storage, validation, tracking)
  data/                    # Sample input files for tests (JSON and CSV)
.github/workflows/
  python-app.yml           # CI: lint (flake8) + test (pytest) on PRs to main
  gitleaks_pr.yml          # Secret scanning on PRs
README.md                  # Project documentation and usage guide
AGENTS.md                  # Guidelines for AI coding agents
```

## Key concepts

### URL placeholder replacement

URLs use `{{key}}` placeholders that get replaced with values from the input file:

- **JSON/CSV**: each placeholder name maps to a property/column header (e.g. `{{sourceId}}` maps to the `sourceId` field).
- **JSON arrays**: use `{{0}}` as the single placeholder; the array values are deduplicated into a Python set when `--clean` is used.

### Input sources (`--source`)

| Flag value    | Constant          | Parser              |
|---------------|-------------------|----------------------|
| `json`        | `JSON_SOURCE`     | `json_utils.parse`   |
| `json_array`  | `JSON_ARRAY_SOURCE` | `json_utils.parse` + `cleanup` |
| `csv`         | `CSV_SOURCE`      | `csv_utils.parse`    |

### Output

Results and logs are written to `data/` (auto-created) as timestamped JSONL files (one JSON object per line) unless `--avoid-storage` is passed. Filenames follow the pattern `log_<timestamp>_source-<source>.jsonl` and `result_<timestamp>_source-<source>.jsonl`. To prevent data loss in long executions, progress is persisted incrementally every 50 requests and at the completion of all requests — each save appends only the new records since the last save, keeping I/O cost bounded regardless of total run size. The `data/` directory is git-ignored.

## Coding conventions

- **Python 3.13** (CI matrix), using `match`/`case` syntax.
- **`argparse`** for CLI argument parsing.
- **`colorama`** for colored terminal output via `Fore` and `Style`.
- **`logging`** module at INFO level for all operational messages.
- **`requests`** library with session-based Bearer token auth.
- No type-checking tooling configured; type hints are used sparingly.
- Use `flake8` for linting: max complexity 10, max line length 127.

## Dependencies

All pinned in `requirements.txt`. Core runtime dependencies:

- `requests` -- HTTP client
- `colorama` -- colored terminal output

Test dependencies: `pytest`

## Testing

Run tests with:

```bash
PYTHONPATH=src python -m pytest test/
```

Tests live in `test/` alongside sample data in `test/data/`. Storage tests use pytest's `tmp_path` fixture for file isolation and automatic cleanup.

## CI/CD

GitHub Actions run on pull requests to `main`:

1. **python-app.yml** -- installs deps, lints with flake8, runs pytest.
2. **gitleaks_pr.yml** -- scans for leaked secrets.

## Common tasks

### Adding a new input source

1. Add a constant in `src/constants.py`.
2. Create a parser function in `src/utils/` returning a list of elements.
3. Add the choice to the `--source` argument in `src/main.py`.
4. Handle the new source type in `ApiBot.replace_elements()` if placeholder logic differs.

### Adding new CLI arguments

Arguments are defined in `src/main.py:parse_args()`. Validation logic lives in `validate_args()`.
