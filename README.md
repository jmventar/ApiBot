# api-bot

Simple project to run a collection of requests, similar to POSTMAN run collection.

### Usage

Check `.vscode/launch.json` for test runs using **Visual Studio Code**

`-f` parameter is mandatory, with an input file (json object as default, also accepts json arrays and csv).

`usage: main.py [-h] --file FILE [--clean] [--source {json,csv}] [--dry] [--method METHOD] [--response-stored] [--url URL] [--token TOKEN] [--delay DELAY]`

##### Options

- `-h, --help` show this help message and exit
- `--file FILE, -f FILE` source data file, **mandatory**
- `--url URL, -u URL` url to make the requests
- `--clean` check json array cleaner section
- `--source {json, json_array, csv}, -s {json, json_array, csv}` json is default format for input, default **json**
- `--dry` dry run, run without executing requests
- `--method METHOD, -m METHOD` request method, default **GET**
- `--avoid-storage` don't create `data/result_<timestamp>_source-<source>.jsonl` results file and `data/log_<timestamp>_source-<source>.jsonl` log file. **false by default.** Logs and results use JSONL format (one JSON object per line) and are persisted incrementally every 50 requests and at the end of the run, appending only new records each time.
- `--token TOKEN, -t TOKEN` bearer token if needed
- `--delay DELAY, -d DELAY` delay between requests in seconds, accepts deciaml values

To avoid make request, use --dry for dry run or don't specify -u URL

#### Array cleaner

Cleanup multiple response arrays in a single set without duplicates

`py ./data/main.py -clean -f ./data/single_replace.json`

#### Replacer

Url replacer replaces specific parts of the url with provided file values.
It will try to find json property and replace in the url.
Same for CSV with headers.

Special case is for json arrays, where a `{{0}}` needs to be specified in url. This specific case is used to clean duplicated values and converts the array into python set. Check `ApiBot JSON single replace arrays` and `ApiBot JSON single call` examples on `.vscode/launch.json`

#### Sample requests

Sample launch GET requests

`py ./src/main.py -clean -f ./data/single_replace.json -m GET -u https://jsonplaceholder.typicode.com/posts/{{post_num}} -t 123456 -d 2.5`

`py ./src/main.py -f ./data/multiple_replace.csv -m GET -u https://jsonplaceholder.typicode.com/posts/{{id}}}/{{name}}/{{map_id}}/{{map}} -t 123456`

#### Sample scripts

Ready-to-use shell scripts for common operations are available in the `scripts/` directory. See `scripts/insurances_availability.sh` for an example of running batch POST requests.

#### AI coding agents

This repository includes an `AGENTS.md` file with project structure, conventions, and guidelines for AI coding assistants (Cursor, Copilot, etc.).
