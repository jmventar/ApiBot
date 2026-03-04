import datetime
import json

from colorama import Fore


def parse(filename: str):
    with open(filename) as jsonfile:
        data = json.load(jsonfile)
        print(f"Read successful {filename}")
        jsonfile.close()
        return data


def store(filename: str, data):
    with open(filename, "w") as jsonfile:
        json.dump(data, jsonfile, cls=DateTimeEncoder)
        print(f"Write successful {Fore.LIGHTCYAN_EX}{filename}{Fore.RESET}")
        jsonfile.close()


def store_jsonl_append(filename: str, items: list):
    """Append items to a JSONL file (one JSON object per line)."""
    with open(filename, "a") as f:
        for item in items:
            f.write(json.dumps(item, cls=DateTimeEncoder) + "\n")
    print(f"Appended {Fore.YELLOW}{len(items)}{Fore.RESET} records to {Fore.LIGHTCYAN_EX}{filename}{Fore.RESET}")


# TODO this is a crap, specific method also on replace for single elements != all CSV + multiple JSON
def cleanup(filename):
    json_data = parse(filename)

    all_arrays = (
        [v for item in json_data for k, v in item.items()]
        if isinstance(json_data[0], dict)
        else [val for array in json_data for val in array]
    )

    return set(all_arrays)


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return super().default(obj)
