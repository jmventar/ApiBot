import logging
import re
import time
from datetime import datetime

import requests
from colorama import Fore, Style
from requests.exceptions import RequestException

from api_bot.response_log import ResponseLog
from constants import CONTENT_TYPE_JSON, JSON_ARRAY_SOURCE


class ApiBot:
    def __init__(self, args, elements, placeholders):
        self.args = args
        self.elements = elements
        self.placeholders = placeholders
        self.response_data = []
        self.response_log = []

    def replace_elements(self, value):
        current_url = self.args.url.replace(r"{{", "#").replace(r"}}", "#")

        if self.args.source == JSON_ARRAY_SOURCE:
            current_url = current_url.replace("#0#", str(value))
        elif self.args.clean is True:
            current_url = current_url.replace(f"#{self.placeholders[0]}#", str(value))
        else:
            for p in self.placeholders:
                current_url = current_url.replace(f"#{p}#", str(value[p]))

        return current_url

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

        if result_length is None:
            result_length = len(response.content) if response.content is not None else 0
        else:
            result_length = int(result_length)

        status_color = self.get_status_color(response.status_code)
        method_color = self.get_method_color(method)
        logging.info(
            f"{Fore.LIGHTBLACK_EX} {count} {current_date_and_time} {Fore.RESET} "
            f"{method_color}{method}{Style.RESET_ALL} {url} : "
            f"{status_color}{response.status_code}{Style.RESET_ALL} "
            f"content {result_content} {result_length} "
        )

        is_json_response: bool = False
        if result_content is not None and CONTENT_TYPE_JSON in result_content:
            logging.info(f"{response.json()}")
            self.response_data.extend(response.json())
            is_json_response = True

        log_data = ResponseLog(response, result_length, is_json_response)
        self.response_log.append(log_data.to_json())

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
    def get_status_color(status_code):
        if 200 <= status_code < 300:
            return Fore.GREEN
        elif 300 <= status_code < 400:
            return Fore.YELLOW
        else:
            return Fore.RED

    @staticmethod
    def get_method_color(method):
        match method:
            case "GET":
                return Fore.LIGHTGREEN_EX
            case "PATCH":
                return Fore.LIGHTMAGENTA_EX
            case "POST":
                return Fore.LIGHTYELLOW_EX
            case "PUT":
                return Fore.LIGHTBLUE_EX
            case "DELETE":
                return Fore.LIGHTRED_EX


def find_placeholders(url: str, jsonArray: bool = False):
    if jsonArray or url is None:
        return ["0"]

    placeholders = re.findall(r"{{(.*?)}}", url)
    placeholder_length = len(placeholders)

    if placeholder_length < 1:
        logging.error(f"No elements to replace on URL ({url})")
        exit(1)

    return placeholders
