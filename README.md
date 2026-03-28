# api-bot

Simple project to run a collection of requests, similar to POSTMAN run collection.

### Usage

`-f` parameter is mandatory, with an input file (json object as default, also accepts json arrays and csv).

`usage: main.py [-h] --file FILE [--clean] [--upload-csv] [--source {json,json_array,csv}] [--dry] [--method METHOD] [--payload JSON_PAYLOAD] [--avoid-storage] [--url URL] [--token TOKEN] [--delay DELAY] [--max-rows-per-upload MAX_ROWS_PER_UPLOAD] [--upload-field UPLOAD_FIELD] [--delimiter DELIMITER] [--encoding ENCODING]`

##### Options

- `-h, --help` show this help message and exit
- `--file FILE, -f FILE` source data file, **mandatory**
- `--url URL, -u URL` url to make the requests
- `--clean` check cleaner section
- `--source {json, json_array, csv}, -s {json, json_array, csv}` json is default format for input, default **json**
- `--dry` dry run, run without executing requests
- `--upload-csv` split the CSV file into batch files and upload them sequentially as multipart form-data
- `--method METHOD, -m METHOD` request method, default **GET** for normal runs and **POST** for `--upload-csv`
- `--payload JSON_PAYLOAD, -p JSON_PAYLOAD` JSON payload template string. Supports placeholder substitution with `{{key}}`.
- `--avoid-storage` don't create `data/result_<timestamp>_source-<source>.jsonl` results file and `data/log_<timestamp>_source-<source>.jsonl` log file. **false by default.** Logs and results use JSONL format (one JSON object per line) and are persisted incrementally every 50 requests and at the end of the run, appending only new records each time.
- `--token TOKEN, -t TOKEN` bearer token if needed
- `--delay DELAY, -d DELAY` delay between requests in seconds, accepts decimal values
- `--max-rows-per-upload` maximum data rows per uploaded batch file, default **5000**
- `--upload-field` multipart form-data field used for the uploaded file, default **csvFile**
- `--delimiter` CSV delimiter used when reading and splitting upload CSVs, default **,**
- `--encoding` file encoding used when reading and splitting upload CSVs, default **utf-8**

To avoid make request, use --dry for dry run or don't specify -u URL.

#### Placeholder replacement

URL placeholders use the `{{key}}` pattern and are resolved from the current input row.

- **JSON**: each placeholder maps to a property in the current object
- **CSV**: each placeholder maps to a column header in the current row
- **JSON arrays**: use `{{0}}` as the placeholder value

#### Cleaner

`--clean` deduplicates values before execution.

- With JSON object input, it collects values from every field across all objects and returns the unique values. This mode is most predictable when each object contains a single scalar field.
- With `json_array` input, it flattens nested arrays and returns unique values
- This is typically paired with a single URL or payload placeholder

#### Payload replacement

`--payload` supports the same placeholder syntax used by URLs.

- **JSON/CSV** payload placeholders map to object properties or CSV headers
- **JSON arrays** use `{{0}}`
- The rendered payload is parsed as JSON before the request is sent

#### CSV upload mode

`--upload-csv` switches the tool from row-based placeholder replacement to batch file upload mode.

- `--file` is treated as the CSV file to upload
- `--url` must be static and cannot contain placeholders
- The file is split into batch CSV files before upload
- `--max-rows-per-upload` defaults to `5000`
- `--upload-field` defaults to `csvFile`

#### Examples

One example for each supported action:

- Clean duplicate scalar values from a JSON object list:
  `python ./src/main.py --clean -f ./test/data/single_replace.json`
- Clean duplicate scalar values from a JSON array source:
  `python ./src/main.py -s json_array --clean -f ./test/data/json_arrays.json`
- Replace a `{{0}}` placeholder from a cleaned JSON array source:
  `python ./src/main.py -s json_array --clean -f ./test/data/json_arrays.json -u "https://jsonplaceholder.typicode.com/posts/{{0}}"`
- Replace placeholders from a JSON object source and send a JSON payload:
  `python ./src/main.py -f ./test/data/multiple_replace.json -m POST -u "https://jsonplaceholder.typicode.com/posts/{{id}}" -p "{\"title\":\"{{name}}\",\"body\":\"{{map}}\",\"userId\":\"{{map_id}}\"}" -t 123456 -d 2.5`
- Replace a single placeholder from CSV:
  `python ./src/main.py -f ./test/data/single_replace.csv -s csv -m GET -u "https://jsonplaceholder.typicode.com/posts/{{post_num}}" -t 123456`
- Replace multiple placeholders from CSV:
  `python ./src/main.py -f ./test/data/multiple_replace.csv -s csv -m GET -u "https://jsonplaceholder.typicode.com/posts/1?param1={{replace_1}}&param2={{replace_2}}&param3={{replace_3}}" -t 123456`
- Replace CSV placeholders inside a JSON payload:
  `python ./src/main.py -f ./test/data/multiple_replace.csv -s csv -m POST -u "https://jsonplaceholder.typicode.com/posts/{{replace_1}}" -p "{\"title\":\"{{replace_1}}\",\"body\":\"{{replace_2}}\",\"userId\":\"{{replace_3}}\"}" -t 123456`
- Upload a CSV file in batches:
  `python ./src/main.py --upload-csv -f ./test/data/multiple_replace.csv -u "https://www.example.es/api/v3/upload-csv" -t 123456 --max-rows-per-upload 5000`

#### AI coding agents

This repository includes an `AGENTS.md` file with project structure, conventions, and guidelines for AI coding assistants (Cursor, Copilot, etc.).
