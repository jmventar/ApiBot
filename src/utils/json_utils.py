import datetime
import json


def parse(filename: str):
    with open(filename) as jsonfile:
        data = json.load(jsonfile)
        print(f"Read successful {filename}")
        jsonfile.close()
        return data


def store(filename: str, data, writeMethod: str = "a"):
    if writeMethod != "w":
        writeMethod = "a"

    with open(filename, writeMethod) as jsonfile:
        json.dump(data, jsonfile, cls=DateTimeEncoder)
        print(f"Write successful {filename}")
        jsonfile.close()


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
