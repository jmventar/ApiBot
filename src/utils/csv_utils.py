import csv
from pathlib import Path


def parse(filename: str):
    if not Path(filename).suffix == ".csv":
        raise Exception("Only csv files allowed")

    with open(filename, mode="r") as csv_file:
        csv_reader = csv.DictReader(csv_file, skipinitialspace=True)
        data = [row for row in csv_reader]
        return data
