import logging

from colorama import init, Fore


def main_api_bot():
    from api_bot.api_bot import APIRunner, parse_args, find_placeholders

    args = parse_args()

    # Initialize colorama and logging
    init()
    logging.basicConfig(level=logging.INFO)

    placeholders = find_placeholders(args.url)

    if args.source == "csv":
        from utils.csv_utils import parse

        elements = parse(args.file)
    else:
        from utils.json_utils import parse, cleanup

        # Only cleans simple lists / dicts
        if args.clean is True and len(placeholders) == 1:
            elements = cleanup(args.file)
        else:
            elements = parse(args.file)

    runner = APIRunner(args, elements, placeholders)
    logging.info(f"Given {Fore.YELLOW}{len(runner.elements)}{Fore.RESET} elements:")
    logging.info(f"{runner.elements}")
    runner.run()
    exit(0)


if __name__ == "__main__":
    main_api_bot()
