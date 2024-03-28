import argparse
import datetime
import logging
import pathlib

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
    if args.clean is True and args.source == "csv":
        logging.error(
            f"Invalid arguments provided, {Fore.RED}-c --clean{Fore.RESET} and {Fore.RED}-s --source csv{Fore.RESET}."
        )
        logging.warn("Can not clean csv duplicates")
        exit(1)

    return args


def main_api_bot():
    from api_bot.api_bot import ApiBot, find_placeholders

    args = parse_args()

    # Initialize colorama and logging
    init()
    logging.basicConfig(level=logging.INFO)

    placeholders = find_placeholders(args.url)

    if args.source == "csv":
        from utils.csv_utils import parse

        elements = parse(args.file)
    else:
        from utils.json_utils import cleanup, parse

        # Only cleans simple lists / dicts
        if args.clean is True and len(placeholders) == 1:
            elements = cleanup(args.file)
        else:
            elements = parse(args.file)

    runner = ApiBot(args, elements, placeholders)
    logging.info(f"Given {Fore.YELLOW}{len(runner.elements)}{Fore.RESET} elements:")
    logging.info(f"{runner.elements}")
    (result, log_data) = runner.run()

    data_folder = f"{pathlib.Path().resolve()}/data"

    # check if results not empty and avoid storage flag
    if log_data and not args.avoid_storage:
        store(f"{data_folder}/log_{datetime.date.today()}.json", log_data)

    # check if log_data not empty and avoid storage flag
    if result and not args.avoid_storage:
        store(
            f"{data_folder}/result_{datetime.date.today()}.json",
            result,
        )

    exit(0)


if __name__ == "__main__":
    main_api_bot()
