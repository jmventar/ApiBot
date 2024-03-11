import argparse
import datetime
import logging
import re

from api_bot.api_bot import ApiBot
from colorama import Fore, init
from utils.json_utils import store


def parse_args():
    parser = argparse.ArgumentParser(
        epilog="To avoid make request, use --dry for dry run or don't specify -u URL"
    )

    parser.add_argument("--file", "-f", type=str, required=True)
    parser.add_argument("--clean", action="store_true", required=False)
    parser.add_argument(
        "--source",
        "-s",
        type=str,
        required=False,
        default="json",
        choices=["json", "csv"],
    )
    parser.add_argument("--dry", action="store_true", required=False)

    url_group = parser.add_argument_group()
    url_group.add_argument("--method", "-m", type=str, required=False, default="GET")
    url_group.add_argument("--url", "-u", type=str, required=False)
    url_group.add_argument("--token", "-t", type=str, required=False)
    url_group.add_argument("--delay", "-d", type=float, required=False, default=0)
    url_group.add_argument("--avoid-storage", action="store_true", required=False)

    args = parser.parse_args()

    # Execute args validations
    if args.clean and args.source == "csv":
        logging.error(
            f"Invalid arguments provided, {Fore.RED}-c --clean{Fore.RESET} and {Fore.RED}-s --source csv{Fore.RESET}."
        )
        logging.warn("Can not clean csv duplicates")
        exit(1)

    return args


def find_placeholders(url: str):
    if url is None:
        return None

    placeholders = re.findall(r"{{(.*?)}}", url)

    placeholder_length = len(placeholders)

    if placeholder_length < 1:
        logging.error(f"No elements to replace on URL ({url})")
        exit(1)

    return placeholders


def main_api_bot():
    args = parse_args()

    # Initialize colorama and logging
    init()
    logging.basicConfig(level=logging.INFO)

    placeholders = find_placeholders(args.url)

    if args.source == "csv":
        from utils.csv_utils import parse

        elements = parse(args.file)
    else:
        from utils.json_utils import parse, clean_duplicates

        elements = parse(args.file)

        if args.clean:
            elements = clean_duplicates(elements)

    runner = ApiBot(args, elements, placeholders)
    logging.info(f"Given {Fore.YELLOW}{len(runner.elements)}{Fore.RESET} elements:")
    logging.info(f"{runner.elements}")
    (result, log_data) = runner.run()
    if not args.avoid_storage:
        store(f"data/log_{datetime.date.today()}.json", log_data)
        store(f"data/result_{datetime.date.today()}.json", result)
    exit(0)


if __name__ == "__main__":
    main_api_bot()
