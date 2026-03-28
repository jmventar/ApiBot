import argparse
import codecs
from datetime import datetime
import logging
import os
import pathlib
import re
from colorama import Fore, init
from constants import (
    CSV_SOURCE,
    DATETIME_FORMAT,
    DEFAULT_MAX_ROWS_PER_CSV_BATCH,
    DEFAULT_UPLOAD_FIELD,
    JSON_ARRAY_SOURCE,
    JSON_SOURCE,
    UPLOAD_CSV_MODE,
)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        epilog="To avoid make request, use --dry for dry run or don't specify -u URL"
    )

    parser.add_argument("--file", "-f", type=str, required=True)
    parser.add_argument("--clean", action="store_true", required=False)
    parser.add_argument("--upload-csv", action="store_true", required=False)
    parser.add_argument(
        "--source",
        "-s",
        type=str,
        required=False,
        default=JSON_SOURCE,
        choices=[JSON_SOURCE, CSV_SOURCE, JSON_ARRAY_SOURCE],
    )
    parser.add_argument("--dry", action="store_true", required=False)

    url_group = parser.add_argument_group()
    url_group.add_argument("--method", "-m", type=str, required=False, default=None)
    url_group.add_argument("--payload", "-p", type=str, required=False, default=None)
    url_group.add_argument("--url", "-u", type=str, required=False)
    url_group.add_argument("--token", "-t", type=str, required=False)
    url_group.add_argument("--delay", "-d", type=float, required=False, default=0)
    url_group.add_argument("--avoid-storage", action="store_true", required=False)
    url_group.add_argument(
        "--max-rows-per-upload",
        type=int,
        required=False,
        default=DEFAULT_MAX_ROWS_PER_CSV_BATCH,
    )
    url_group.add_argument(
        "--upload-field",
        type=str,
        required=False,
        default=DEFAULT_UPLOAD_FIELD,
    )
    url_group.add_argument("--delimiter", type=str, required=False, default=",")
    url_group.add_argument("--encoding", type=str, required=False, default="utf-8")

    args = parser.parse_args(argv)
    if args.method is None:
        args.method = "POST" if args.upload_csv else "GET"
    if args.token is None:
        args.token = os.getenv("APIBOT_TOKEN") or None
    return args


def validate_args(args, placeholders):
    if args.upload_csv:
        if pathlib.Path(args.file).suffix.lower() != ".csv":
            logging.error(
                f"Invalid arguments provided, {Fore.RED}--upload-csv{Fore.RESET} requires a CSV file."
            )
            exit(1)

        if args.url is None:
            logging.error(
                f"Invalid arguments provided, {Fore.RED}--upload-csv{Fore.RESET} requires --url."
            )
            exit(1)

        if placeholders:
            logging.error(
                f"Invalid arguments provided, {Fore.RED}--upload-csv{Fore.RESET} requires a static --url without placeholders."
            )
            exit(1)

        if args.max_rows_per_upload <= 0:
            logging.error(
                f"Invalid arguments provided, {Fore.RED}--max-rows-per-upload{Fore.RESET} must be greater than 0."
            )
            exit(1)

        if not args.upload_field:
            logging.error(
                f"Invalid arguments provided, {Fore.RED}--upload-field{Fore.RESET} cannot be empty."
            )
            exit(1)

        if len(args.delimiter) != 1:
            logging.error(
                f"Invalid arguments provided, {Fore.RED}--delimiter{Fore.RESET} must be a single character."
            )
            exit(1)

        try:
            codecs.lookup(args.encoding)
        except LookupError:
            logging.error(
                f"Invalid arguments provided, {Fore.RED}--encoding{Fore.RESET} is not a valid codec."
            )
            exit(1)

        if args.clean is True:
            logging.error(
                f"Invalid arguments provided, {Fore.RED}--upload-csv{Fore.RESET} cannot be combined with --clean."
            )
            exit(1)
        return

    # Execute args validations
    if args.clean is True and args.source == CSV_SOURCE:
        logging.error(
            f"Invalid arguments provided, {Fore.RED}-c --clean{Fore.RESET} and {Fore.RED}-s --source {CSV_SOURCE}{Fore.RESET}."
        )
        logging.warning(f"Cannot clean {args.source} duplicates")
        exit(1)

    if args.clean is True and len(placeholders) > 1:
        logging.error(
            f"Invalid arguments provided, {Fore.RED}-c --clean{Fore.RESET} and multiple placeholders found."
        )
        logging.warning(f"Cannot clean {args.source} duplicates")
        exit(1)

    if args.clean is True and args.payload:
        payload_placeholders = re.findall(r"{{(.*?)}}", args.payload)
        if len(payload_placeholders) > 1:
            logging.error(
                f"Invalid arguments provided, {Fore.RED}-c --clean{Fore.RESET} and multiple payload placeholders found."
            )
            logging.warning("Cannot map multiple payload placeholders with cleaned scalar values")
            exit(1)

    if args.url is None:
        logging.warning(
            f"{Fore.YELLOW}No URL provided, skipping requests. Use --url to specify the target URL.{Fore.RESET}"
        )


def prepare_storage_paths(source_type: str):
    data_folder = pathlib.Path().resolve() / "data"
    if not data_folder.exists():
        data_folder.mkdir(parents=True, exist_ok=True)
        print(f"Created data directory: {Fore.LIGHTBLACK_EX}{data_folder}{Fore.RESET}")

    timestamp = datetime.now().strftime(DATETIME_FORMAT)
    log_path = data_folder / f"log_{timestamp}_source-{source_type}.jsonl"
    result_path = data_folder / f"result_{timestamp}_source-{source_type}.jsonl"
    return str(log_path), str(result_path)


def main_api_bot():
    from api_bot.api_bot import ApiBot, find_placeholders

    args = parse_args()

    # Initialize colorama and logging
    init()
    logging.basicConfig(level=logging.INFO)

    placeholders = find_placeholders(
        args.url,
        args.source == JSON_ARRAY_SOURCE,
        args.upload_csv,
    )

    validate_args(args, placeholders)

    source_type = UPLOAD_CSV_MODE if args.upload_csv else args.source
    log_filename, result_filename = prepare_storage_paths(source_type)

    if args.upload_csv:
        elements = [args.file]
    elif args.source == CSV_SOURCE:
        from utils.csv_utils import parse

        elements = parse(args.file)
    else:
        from utils.json_utils import cleanup, parse

        # Only cleans simple arrays / json objects with single element
        if args.clean is True and len(placeholders) == 1:
            elements = cleanup(args.file)
        else:
            elements = parse(args.file)

    runner = ApiBot(args, elements, placeholders, log_filename, result_filename)
    logging.info(f"Given {Fore.YELLOW}{len(runner.elements)}{Fore.RESET} elements:")
    logging.info(f"{runner.elements}")
    runner.run()

    exit(0)


if __name__ == "__main__":
    main_api_bot()
