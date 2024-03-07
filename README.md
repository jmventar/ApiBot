# api-bot

Simple project to run a collection of requests, similar to POSTMAN run collection.

### Usage

Check `launch.json` for automated runs using **Visual Studio Code**

**-f** parameter is mandatory, with an input file (json as default or csv).

`usage: main.py [-h] --file FILE [--clean] [--source {json,csv}] [--dry] [--method METHOD] [--response-stored] [--url URL] [--token TOKEN] [--delay DELAY]`

##### Options

- `-h, --help` show this help message and exit
- `--file FILE, -f FILE` source data file, **mandatory**
- `--clean` check Array cleaner section
- `--source {json,csv}, -s {json,csv}` json is default format for input
- `--dry` dry run, run without executing requests

- `--method METHOD, -m METHOD` request method, default **GET**
- `--response-stored, -r` it will store a resonse in data folder with result\_{current_date}.json
- `--url URL, -u URL` url to make the requests
- `--token TOKEN, -t TOKEN` bearer token if needed
- `--delay DELAY, -d DELAY` delay between requests in seconds, accepts deciaml values

To avoid make request, use --dry for dry run or don't specify -u URL

#### Array cleaner

Cleanup multiple response arrays in a single set without duplicates

`py ./data/main.py -clean -f ./data/single_replace.json`

#### Sample requests

Launch GET requests to github profiles with 2.5 seconds delay

`py ./src/main.py -clean -f ./data/single_replace.json -m GET -u https://jsonplaceholder.typicode.com/posts/{{post_num}} -t 123456 -d 2.5`
`py ./src/main.py -f ./data/multiple_replace.csv -m GET -u https://jsonplaceholder.typicode.com/posts/{{id}}}/{{name}}/{{map_id}}/{{map}} -t 123456`
