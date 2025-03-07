import os
import json

from dotenv import load_dotenv
from discord import (
    Intents,
)

from watcher import Watcher

LENA_BINGO_VIDEO = "lenna_bingo_video"

CMD_PREFIX = "!"


def main():
    # Environment Setup
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN")

    lenna_bot = Watcher(token, CMD_PREFIX)
    lenna_bot.run()


if __name__ == "__main__":
    main()
