import argparse
import datetime
import logging
import pathlib
from colorama import Fore, init
from constants import CSV_SOURCE, JSON_ARRAY_SOURCE, JSON_SOURCE
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
        default=JSON_SOURCE,
        choices=[JSON_SOURCE, CSV_SOURCE, JSON_ARRAY_SOURCE],
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
    if args.clean is True and args.source == CSV_SOURCE:
        logging.error(
            f"Invalid arguments provided, {Fore.RED}-c --clean{Fore.RESET} and {Fore.RED}-s --source {CSV_SOURCE}{Fore.RESET}."
        )
        logging.warning(f"Can not clean {CSV_SOURCE} duplicates")
        exit(1)

    return args


def main_api_bot():
    from api_bot.api_bot import ApiBot, find_placeholders

    args = parse_args()

    # Initialize colorama and logging
    init()
    logging.basicConfig(level=logging.INFO)

    placeholders = find_placeholders(args.url, args.source == JSON_ARRAY_SOURCE)

    if args.source == CSV_SOURCE:
        from utils.csv_utils import parse

        elements = parse(args.file)
    else:
        from utils.json_utils import cleanup, parse

        # Only cleans simple arrays / json objects with single element
        if args.clean is True and len(placeholders) == 1:
            elements = cleanup(args.file)
        else:
            elements = parse(args.file)

    runner = ApiBot(args, elements, placeholders)
    logging.info(f"Given {Fore.YELLOW}{len(runner.elements)}{Fore.RESET} elements:")
    logging.info(f"{runner.elements}")
    (result, log_data) = runner.run()

    # check pathfolder exists
    data_folder_path = f"{pathlib.Path().resolve()}/data"
    data_folder = pathlib.Path(data_folder_path)

    if not data_folder.exists():
        data_folder.mkdir(parents=True, exist_ok=True)
        print(
            f"Created data directory: {Fore.LIGHTBLACK_EX}{data_folder_path}{Fore.RESET}"
        )

    # check if results not empty and avoid storage flag
    if log_data and not args.avoid_storage:
        store(f"{data_folder_path}/log_{datetime.date.today()}.json", log_data)

    # check if log_data not empty and avoid storage flag
    if result and not args.avoid_storage:
        store(
            f"{data_folder_path}/result_{datetime.date.today()}.json",
            result,
        )

    exit(0)


if __name__ == "__main__":
    main_api_bot()
