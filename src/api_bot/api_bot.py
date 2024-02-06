import argparse
import json
import logging
import re
import requests
import time
from colorama import Fore, Style
from utils.json_utils import load_config
from datetime import datetime
from requests.exceptions import RequestException


class APIRunner:
    def __init__(self, args):
        self.args = args
        if self.args.clean is True:
            self.elements = self.arrays_to_set()
        else:
            self.elements = load_config(self.args.file)

    def arrays_to_set(self):
        all_arrays = []
        with open(self.args.file, "r") as file:
            json_data = json.load(file)
            for array in json_data:
                all_arrays.extend(array)

        all_arrays = set(all_arrays)
        logging.info(all_arrays)
        return all_arrays

    def find_elements_to_replace(self):
        # Find elements between {{}}
        return re.findall(r"{{(.*?)}}", self.args.url)

    def replace_elements(self, placeholders, value):
        current_url = self.args.url

        if len(placeholders) < 1:
            logging.info(f"No elements to replace on URL ({self.args.url}), exit")
            return

        if len(placeholders) == 1:
            current_url = current_url.replace("0", str(value))
        else:
            for p in placeholders:
                current_url = current_url.replace(f"{p}", value[p])

        return current_url.replace(r"{{", "").replace(r"}}", "")

    def run(self):
        # Validate arguments
        if self.args.url is None:
            return

        method = "GET" if self.args.method is None else self.args.method.upper()
        delay = self.args.delay or 0

        placeholders = self.find_elements_to_replace()

        with requests.Session() as session:
            session.headers.update({"Authorization": f"Bearer {self.args.token}"})

            for count, elem in enumerate(self.elements, start=1):
                current_url = self.replace_elements(placeholders, elem)
                response = self.execute(method, current_url, session.headers, None)

                if response is not None:
                    self.log_response(method, current_url, count, response)

                if delay > 0:
                    time.sleep(delay)

    def log_response(self, method, url, count, response):
        current_date_and_time = datetime.now()
        result_content = response.headers.get("content-type")
        result_length = response.headers.get("content-length")

        color = self.get_color(response.status_code)
        logging.info(
            f"{Fore.LIGHTBLACK_EX} {count} {current_date_and_time} "
            + f"{Fore.RESET} Executed {method} {url} "
            + color
            + f": {response.status_code}"
            + Style.RESET_ALL
            + f" content {result_content} {result_length}"
        )

    @staticmethod
    def execute(method: str, url: str, headers, json_data):
        try:
            return requests.request(method, url, headers=headers, json=json_data)
        except RequestException as e:
            logging.error(f"Request failed: {e}")
            return None

    @staticmethod
    def get_color(status_code):
        if 200 <= status_code < 300:
            return Fore.GREEN
        elif 300 <= status_code < 400:
            return Fore.YELLOW
        else:
            return Fore.RED


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", "-f", type=str, required=True)
    parser.add_argument("--clean", "-c", action="store_true", required=False)
    parser.add_argument("--method", "-m", type=str, required=False, default="GET")
    parser.add_argument("--url", "-u", type=str, required=False)
    parser.add_argument("--token", "-t", type=str, required=False)
    parser.add_argument("--delay", "-d", type=float, required=False, default=0)
    return parser.parse_args()
