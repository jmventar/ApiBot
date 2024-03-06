import logging
import re
import time
from datetime import datetime

import requests
from api_bot.response_log import ResponseLog
from colorama import Fore, Style
from requests.exceptions import RequestException


class ApiBot:
    def __init__(self, args, elements, placeholders):
        self.args = args
        self.elements = elements
        self.placeholders = placeholders
        self.response_data = []
        self.response_log = []

    def replace_elements(self, value):
        current_url = self.args.url

        if (self.args.source != "csv") and (len(self.placeholders) == 1):
            current_url = current_url.replace("0", str(value))
        else:
            for p in self.placeholders:
                current_url = current_url.replace(f"{p}", value[p])

        return current_url.replace(r"{{", "").replace(r"}}", "")

    def run(self):
        if self.args.dry or self.args.url is None:
            logging.info(f"{Fore.YELLOW} dry-run, skip requests")
            exit(0)
        else:
            method = self.args.method.upper()
            delay = self.args.delay

            with requests.Session() as session:
                session.headers.update({"Authorization": f"Bearer {self.args.token}"})

                for count, elem in enumerate(self.elements, start=1):
                    current_url = self.replace_elements(elem)
                    response = self.execute(method, current_url, session.headers, None)

                    if response is not None:
                        self.log_response(method, current_url, count, response)

                    if count % 50 == 0:
                        self.show_progress(count, len(self.elements))

                    if delay > 0:
                        time.sleep(delay)

            # Return log
            return (self.response_data, self.response_log)

    def log_response(self, method, url, count, response):
        current_date_and_time = datetime.now()
        result_content = response.headers.get("content-type")
        result_length = response.headers.get("content-length")

        color = self.get_color(response.status_code)
        logging.info(
            f"{Fore.LIGHTBLACK_EX} {count} {current_date_and_time} {Fore.RESET} Executed {method} {url} : {color}"
            + f"{response.status_code}{Style.RESET_ALL} content {result_content} {result_length}"
        )

        if self.args.response_stored and "json" in response.headers["content-type"]:
            logging.info(f"{response.json()}")
            log_data = ResponseLog(response)
            self.response_log.append(log_data.to_json())

    #            self.response_data.extend(response_log)

    @staticmethod
    def show_progress(count: int, total: int):
        percent = (count / total) * 100
        percent = round(percent, 2)
        logging.info(
            f"{Fore.YELLOW} Progress {count} / {total} : {percent}% {Fore.RESET}"
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


def find_placeholders(url: str):
    if url is None:
        return

    placeholders = re.findall(r"{{(.*?)}}", url)

    placeholder_length = len(placeholders)

    if placeholder_length < 1:
        logging.error(f"No elements to replace on URL ({url})")
        exit(1)

    return placeholders
