import logging
import json
import re
import pathlib
import tempfile
import time
from datetime import datetime
from urllib.parse import quote

import requests
from colorama import Fore, Style
from requests.exceptions import RequestException

from api_bot.response_log import ResponseLog
from constants import CONTENT_TYPE_JSON, JSON_ARRAY_SOURCE
from utils.csv_batch_utils import (
    build_csv_batches_from_rows,
    load_csv_rows,
    suggest_batches,
)
from utils.json_utils import store_jsonl_append


class ApiBot:
    def __init__(self, args, elements, placeholders, log_filename=None, result_filename=None):
        self.args = args
        self.elements = elements
        self.placeholders = placeholders
        self.log_filename = log_filename
        self.result_filename = result_filename
        self.response_data = []
        self.response_log = []
        self._last_persisted_log_idx = 0
        self._last_persisted_data_idx = 0
        self._successful_requests = 0
        self._failed_by_status = {}

    def replace_elements(self, value):
        current_url = self.args.url.replace(r"{{", "#").replace(r"}}", "#")

        if self.args.source == JSON_ARRAY_SOURCE:
            current_url = current_url.replace("#0#", self._encode_url_value(value))
        elif self.args.clean is True:
            current_url = current_url.replace(
                f"#{self.placeholders[0]}#",
                self._encode_url_value(value),
            )
        else:
            for p in self.placeholders:
                current_url = current_url.replace(
                    f"#{p}#",
                    self._encode_url_value(value[p]),
                )

        return current_url

    @staticmethod
    def _encode_url_value(value):
        return quote(str(value), safe="")

    def replace_payload_elements(self, value):
        if not self.args.payload:
            return None

        payload_placeholders = re.findall(r"{{(.*?)}}", self.args.payload)
        try:
            payload_template = json.loads(self.args.payload)
        except json.JSONDecodeError as exc:
            logging.error(
                "Failed to decode payload template JSON: %s. Payload: %s",
                exc,
                self.args.payload,
            )
            return None

        try:
            return self._replace_payload_placeholders(
                payload_template, value, payload_placeholders
            )
        except KeyError as exc:
            logging.error(
                "Missing payload placeholder key %s for value: %s",
                exc,
                value,
            )
            return None

    def _replace_payload_placeholders(self, obj, value, payload_placeholders):
        if isinstance(obj, str):
            updated = obj

            if self.args.source == JSON_ARRAY_SOURCE:
                return updated.replace("{{0}}", str(value))

            if self.args.clean is True:
                if len(payload_placeholders) == 1:
                    placeholder = payload_placeholders[0]
                    return updated.replace(f"{{{{{placeholder}}}}}", str(value))
                return updated

            for p in payload_placeholders:
                updated = updated.replace(f"{{{{{p}}}}}", str(value[p]))

            return updated

        if isinstance(obj, list):
            return [
                self._replace_payload_placeholders(item, value, payload_placeholders)
                for item in obj
            ]

        if isinstance(obj, dict):
            return {
                self._replace_payload_placeholders(
                    key, value, payload_placeholders
                ): self._replace_payload_placeholders(
                    item, value, payload_placeholders
                )
                for key, item in obj.items()
            }

        return obj

    def _persist_to_storage(self):
        if self.args.avoid_storage:
            return

        if self.log_filename:
            new_logs = self.response_log[self._last_persisted_log_idx:]
            if new_logs:
                store_jsonl_append(self.log_filename, new_logs)
                self._last_persisted_log_idx = len(self.response_log)

        if self.result_filename:
            new_data = self.response_data[self._last_persisted_data_idx:]
            if new_data:
                store_jsonl_append(self.result_filename, new_data)
                self._last_persisted_data_idx = len(self.response_data)

    def _build_headers(self):
        if self.args.token is None:
            return {}
        return {"Authorization": f"Bearer {self.args.token}"}

    def _get_response_byte_limit(self):
        return self.args.max_response_bytes

    def _read_response_body(self, response):
        max_bytes = self._get_response_byte_limit()
        iter_content = getattr(response, "iter_content", None)

        if not callable(iter_content):
            raw_content = getattr(response, "content", b"") or b""
            if isinstance(raw_content, str):
                raw_content = raw_content.encode("utf-8", errors="replace")
            truncated = len(raw_content) > max_bytes
            close = getattr(response, "close", None)
            if callable(close):
                close()
            return raw_content[:max_bytes], truncated

        chunks = []
        bytes_read = 0
        truncated = False

        try:
            iterator = iter_content(chunk_size=8192)
            for chunk in iterator:
                if not chunk:
                    continue

                remaining = max_bytes - bytes_read
                if remaining <= 0:
                    truncated = True
                    break

                if len(chunk) <= remaining:
                    chunks.append(chunk)
                    bytes_read += len(chunk)
                    continue

                chunks.append(chunk[:remaining])
                bytes_read += remaining
                truncated = True
                break
        except TypeError:
            raw_content = getattr(response, "content", b"") or b""
            if isinstance(raw_content, str):
                raw_content = raw_content.encode("utf-8", errors="replace")
            truncated = len(raw_content) > max_bytes
            return raw_content[:max_bytes], truncated
        finally:
            close = getattr(response, "close", None)
            if callable(close):
                close()

        return b"".join(chunks), truncated

    def _prepare_upload_output_dir(self, csv_file: pathlib.Path) -> pathlib.Path:
        data_dir = pathlib.Path().resolve() / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        output_dir = tempfile.mkdtemp(prefix=f"{csv_file.stem}_upload_", dir=data_dir)
        return pathlib.Path(output_dir)

    def _run_upload_csv(self, method: str, headers, delay: float):
        csv_file = pathlib.Path(self.args.file)
        output_dir = self._prepare_upload_output_dir(csv_file)
        header, rows = load_csv_rows(
            csv_file=csv_file,
            delimiter=self.args.delimiter,
            encoding=self.args.encoding,
        )
        total_rows = len(rows)
        total_batches = suggest_batches(total_rows, self.args.max_rows_per_upload)
        logging.info(f"CSV rows to split: {total_rows}")
        logging.info(f"CSV upload batches to create: {total_batches}")
        _, _, batch_details = build_csv_batches_from_rows(
            csv_file=csv_file,
            header=header,
            rows=rows,
            max_rows_per_batch=self.args.max_rows_per_upload,
            output_dir=output_dir,
            delimiter=self.args.delimiter,
            output_encoding=self.args.encoding,
        )

        total_batches = len(batch_details)
        with requests.Session() as session:
            session.headers.update(headers)
            for count, (batch_file, _) in enumerate(batch_details, start=1):
                with batch_file.open("rb") as batch_stream:
                    files = [
                        (
                            self.args.upload_field,
                            (
                                batch_file.name,
                                batch_stream,
                                "text/csv",
                            ),
                        )
                    ]
                    response = self.execute(
                        session,
                        method,
                        self.args.url,                    
                        files=files,
                        timeout=self.args.timeout,
                    )

                if response is not None:
                    self.log_response(method, self.args.url, count, response)
                    if 200 <= response.status_code < 300:
                        self.register_success()
                    else:
                        self.register_failure(response.status_code)

                if count % 50 == 0:
                    self.show_progress(count, total_batches)
                    self._persist_to_storage()

                if delay > 0:
                    time.sleep(delay)

        self._persist_to_storage()
        failures_summary = self._format_failures_summary()
        logging.info(
            f"Uploaded all CSV batches {Fore.YELLOW}{total_batches}{Fore.RESET}"
        )
        logging.info(
            f"Success: {self.get_status_color(200)}{self._successful_requests}{Fore.RESET}"
            f"{failures_summary}"
        )

        return (self.response_data, self.response_log)

    def run(self):
        # reset counters per run
        self._successful_requests = 0
        self._failed_by_status = {}

        if self.args.dry or self.args.url is None:
            logging.info(f"{Fore.YELLOW} dry-run, skip requests")
            exit(0)
        else:
            method = self.args.method.upper()
            delay = self.args.delay
            headers = self._build_headers()

            if self.args.upload_csv:
                return self._run_upload_csv(method, headers, delay)

            with requests.Session() as session:
                session.headers.update(headers)

                for count, elem in enumerate(self.elements, start=1):
                    current_url = self.replace_elements(elem)
                    json_data = self.replace_payload_elements(elem)
                    response = self.execute(
                        session,
                        method,
                        current_url,
                        json_data,
                        timeout=self.args.timeout,
                    )

                    if response is not None:
                        self.log_response(method, current_url, count, response)
                        if 200 <= response.status_code < 300:
                            self.register_success()
                        else:
                            self.register_failure(response.status_code)

                    if count % 50 == 0:
                        self.show_progress(count, len(self.elements))
                        self._persist_to_storage()

                    if delay > 0:
                        time.sleep(delay)

            self._persist_to_storage()
            total = len(self.elements)
            failures_summary = self._format_failures_summary()
            logging.info(f"Executed all requests {Fore.YELLOW}{total}{Fore.RESET}")
            logging.info(
                f"Success: {self.get_status_color(200)}{self._successful_requests}{Fore.RESET}"
                f"{failures_summary}"
            )

            # Return log
            return (self.response_data, self.response_log)

    def register_success(self):
        self._successful_requests += 1

    def register_failure(self, status_code: int):
        self._failed_by_status[status_code] = (
            self._failed_by_status.get(status_code, 0) + 1
        )

    def _format_failures_summary(self) -> str:
        if not self._failed_by_status:
            return ""
        # Sort by status code for consistent output
        parts = []
        for code in sorted(self._failed_by_status.keys()):
            count = self._failed_by_status[code]
            color = self.get_status_color(code)
            parts.append(f" {color}{code}:{count}{Fore.RESET}")
        return " | Failures:" + "".join(parts)

    def log_response(self, method, url, count, response):
        current_date_and_time = datetime.now()
        result_content = response.headers.get("content-type")
        response_body, is_truncated = self._read_response_body(response)
        result_length = len(response_body)

        status_color = self.get_status_color(response.status_code)
        method_color = self.get_method_color(method)
        logging.info(
            f"{Fore.LIGHTBLACK_EX} {count} {current_date_and_time} {Fore.RESET} "
            f"{method_color}{method}{Style.RESET_ALL} {url} : "
            f"{status_color}{response.status_code}{Style.RESET_ALL} "
            f"content {result_content} {result_length}"
            f"{' [truncated]' if is_truncated else ''} "
        )

        response_data = None
        content_type = result_content.lower() if result_content is not None else ""
        if result_length > 0:
            response_text = response_body.decode(
                response.encoding or "utf-8",
                errors="replace",
            )
            if CONTENT_TYPE_JSON in content_type and not is_truncated:
                try:
                    response_data = json.loads(response_text)
                    logging.info(f"{response_data}")
                    if isinstance(response_data, list):
                        self.response_data.extend(response_data)
                    else:
                        self.response_data.append(response_data)
                except json.JSONDecodeError:
                    response_data = response_text
                    logging.info(f"{response_data}")
            else:
                response_data = response_text
                logging.info(f"{response_data}")

        log_data = ResponseLog(
            method=method,
            url=url,
            status_code=response.status_code,
            content_type=result_content,
            content_length=result_length,
            data=response_data,
            truncated=is_truncated,
        )
        self.response_log.append(log_data.to_json())

    @staticmethod
    def show_progress(count: int, total: int):
        percent = (count / total) * 100
        percent = round(percent, 2)
        logging.info(
            f"{Fore.YELLOW} Progress {count} / {total} : {percent}% {Fore.RESET}"
        )

    @staticmethod
    def execute(session, method: str, url: str, json_data=None, files=None, timeout=None):
        try:
            return session.request(
                method,
                url,
                headers=session.headers,
                json=json_data,
                data=None, # NOT supported option
                files=files,
                timeout=timeout,
                stream=True,
            )
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


def find_placeholders(
    url: str, jsonArray: bool = False, allow_static: bool = False
):
    if allow_static and url is not None:
        placeholders = re.findall(r"{{(.*?)}}", url)
        if placeholders:
            return placeholders
        return []

    if jsonArray or url is None:
        return ["0"]

    placeholders = re.findall(r"{{(.*?)}}", url)
    placeholder_length = len(placeholders)

    if placeholder_length < 1:
        if allow_static:
            return []
        logging.error(f"No elements to replace on URL ({url})")
        exit(1)

    return placeholders
