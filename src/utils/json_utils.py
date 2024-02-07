import json


def load_config(filename: str):
    with open(filename) as jsonfile:
        data = json.load(jsonfile)
        print(f"Read successful {filename}")
        jsonfile.close()
        return data


def store_config(filename: str, data):
    with open(filename, "w") as jsonfile:
        json.dump(data, jsonfile)
        print(f"Write successful {filename}")
        jsonfile.close()


def arrays_to_set(filename):
    json_data = load_config(filename)

    all_arrays = (
        [v for item in json_data for k, v in item.items()]
        if isinstance(json_data[0], dict)
        else [val for array in json_data for val in array]
    )
    return set(all_arrays)
