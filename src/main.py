import logging

from colorama import init, Fore
from utils.json_utils import load_config, arrays_to_set


def main_api_bot():
    from api_bot.api_bot import APIRunner, parse_args

    args = parse_args()

    # Initialize colorama and logging
    init()
    logging.basicConfig(level=logging.INFO)

    if args.clean is True:
        elements = arrays_to_set(args.file)
    else:
        elements = load_config(args.file)

    runner = APIRunner(args, elements)
    logging.info(
        f"Executing {Fore.YELLOW} {len(runner.elements)} {Fore.RESET} requests, for elements:"
    )
    logging.info(f"{runner.elements}")
    runner.run()
    exit(0)


if __name__ == "__main__":
    main_api_bot()
