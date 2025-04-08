import os
import logging

from dotenv import load_dotenv

from watcher import Watcher

LOGFILE = "lenna.log"
CMD_PREFIX = "!"


def main():
    try:
        # Environment Setup
        load_dotenv()
        token = os.getenv("DISCORD_TOKEN")

        log = logging.getLogger(__name__)
        logging.basicConfig(filename=LOGFILE, encoding="utf-8")
        log.setLevel(logging.INFO)

        lenna_bot = Watcher(log, token, CMD_PREFIX)
        lenna_bot.run()
    except KeyboardInterrupt:
        # Gracefully handle a keyboard interrupt
        lenna_bot.close()


if __name__ == "__main__":
    main()
