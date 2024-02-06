import logging

from colorama import init, Fore


def main_api_bot():
    from api_bot.api_bot import APIRunner, parse_args

    args = parse_args()

    # Initialize colorama and logging
    init()
    logging.basicConfig(level=logging.INFO)

    runner = APIRunner(args)
    logging.info(
        f"Executing {Fore.YELLOW} {len(runner.elements)} {Fore.RESET} requests, for elements:"
    )
    logging.info(f"{runner.elements}")
    runner.run()
    exit(0)


if __name__ == "__main__":
    main_api_bot()
