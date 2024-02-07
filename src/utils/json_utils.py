import json


def parse(filename: str):
    with open(filename) as jsonfile:
        data = json.load(jsonfile)
        print(f"Read successful {filename}")
        jsonfile.close()
        return data


def store(filename: str, data):
    with open(filename, "w") as jsonfile:
        json.dump(data, jsonfile)
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
