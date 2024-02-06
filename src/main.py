from colorama import init
import logging


def main_api_bot():
    from api_bot.api_bot import parse_args, APIRunner

    args = parse_args()

    # Initialize colorama and logging
    init()
    logging.basicConfig(level=logging.INFO)

    runner = APIRunner(args)
    runner.run()
    exit(0)


if __name__ == "__main__":
    main_api_bot()
    main_logi()
