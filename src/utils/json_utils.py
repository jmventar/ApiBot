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
