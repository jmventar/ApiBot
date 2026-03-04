# api-bot

Simple project to run a collection of requests, similar to POSTMAN run collection.

### Usage

Check `.vscode/launch.json` for test runs using **Visual Studio Code**

`-f` parameter is mandatory, with an input file (json object as default, also accepts json arrays and csv).

`usage: main.py [-h] --file FILE [--clean] [--source {json,json_array,csv}] [--dry] [--method METHOD] [--payload JSON_PAYLOAD] [--avoid-storage] [--url URL] [--token TOKEN] [--delay DELAY]`

##### Options

- `-h, --help` show this help message and exit
- `--file FILE, -f FILE` source data file, **mandatory**
- `--url URL, -u URL` url to make the requests
- `--clean` check json array cleaner section
- `--source {json, json_array, csv}, -s {json, json_array, csv}` json is default format for input, default **json**
- `--dry` dry run, run without executing requests
- `--method METHOD, -m METHOD` request method, default **GET**
- `--payload JSON_PAYLOAD, -p JSON_PAYLOAD` JSON payload template string. Supports placeholder substitution with `{{key}}`.
- `--avoid-storage` don't create `data/result_<timestamp>_source-<source>.jsonl` results file and `data/log_<timestamp>_source-<source>.jsonl` log file. **false by default.** Logs and results use JSONL format (one JSON object per line) and are persisted incrementally every 50 requests and at the end of the run, appending only new records each time.
- `--token TOKEN, -t TOKEN` bearer token if needed
- `--delay DELAY, -d DELAY` delay between requests in seconds, accepts deciaml values

To avoid make request, use --dry for dry run or don't specify -u URL

#### Array cleaner

Cleanup multiple response arrays in a single set without duplicates

`python ./src/main.py --clean -f ./test/data/single_replace.json`

#### Replacer

Url replacer replaces specific parts of the url with provided file values.
It will try to find json property and replace in the url.
Same for CSV with headers.

Special case is for json arrays, where a `{{0}}` needs to be specified in url. This specific case is used to clean duplicated values and converts the array into python set. Check `ApiBot JSON single replace arrays` and `ApiBot JSON single call` examples on `.vscode/launch.json`

#### Payload replacer

Payload placeholders are auto-detected from brackets in `--payload` (same `{{key}}` style used in URLs).

- **JSON/CSV**: each `{{key}}` maps to a property/column in the current row.
- **JSON arrays**: use `{{0}}` as the placeholder.
- The rendered payload is parsed with JSON before the request is sent.
- If no payload is provided, requests are sent with no JSON body.

#### Sample requests

Sample launch GET requests

`python ./src/main.py --clean -f ./test/data/single_replace.json -m GET -u https://jsonplaceholder.typicode.com/posts/{{post_num}} -t 123456 -d 2.5`

`python ./src/main.py -f ./test/data/multiple_replace.csv -s csv -m GET -u "https://jsonplaceholder.typicode.com/posts/{{id}}/{{name}}/{{map_id}}/{{map}}" -t 123456`

`python ./src/main.py -f ./test/data/multiple_replace.csv -s csv -m POST -u "https://example.com/items/{{id}}" -p "{\"id\":\"{{id}}\",\"name\":\"{{name}}\"}" -t 123456`

#### AI coding agents

This repository includes an `AGENTS.md` file with project structure, conventions, and guidelines for AI coding assistants (Cursor, Copilot, etc.).
