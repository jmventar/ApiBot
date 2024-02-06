# api-bot

Simple project to run a collection of requests, similar to POSTMAN run collection.

### Usage

Check `launch.json` for automated runs using **Visual Studio Code**

**-f** parameter is mandatory, with a json file.

#### Array cleaner

Cleanup multiple response arrays in a single set without duplicates

`py api_run.py -c -f .\example_input.json`

#### Url bot

Launch GET requests to github profiles with 2.5 seconds delay

`py main.py -c -f .\single_replace.json -m GET -u https://github.com/{{0}} -t 123456 -d 2.5`
`py main.py -f .\multiple_replace.json -m GET -u https://localhost/{{id}}}/{{name}}/{{map_id}}/{{map}} -t 123456`
