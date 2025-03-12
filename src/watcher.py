"""
Watcher class

Class that basically serves as the bot
It watches channel for prompts and responds as needed
"""

import re
from textwrap import dedent

from functools import partial, wraps
import discord
from discord.ext import commands

from responder import Responder

LENA_BINGO_VIDEO = "lenna_bingo_video"


class Watcher:
    """
    Watcher class definition
    """

    # Doll lookup variable
    _INCLUDE_KEYS_STRING = "with_keys"

    def __init__(self, log, token, cmd_prefix):
        self.log = log
        self.token = token
        self.cmd_prefix = cmd_prefix
        self.responder = Responder(self.log)

        self.intents = discord.Intents.default()
        self.intents.message_content = True
        self.bot = commands.Bot(command_prefix=cmd_prefix, intents=self.intents)

        self.bot.event(self._on_ready)

        self._add_command("bingo", Watcher.bingo)
        self._add_command("echo", Watcher.echo)
        self._add_command("lookup", Watcher.lookup)
        self._add_command("flookup", Watcher.flookup)

    def _add_command(self, name, func):
        """
        Helper function to add the command to the bot
        taken from https://stackoverflow.com/questions/75674926/how-do-i-add-commands-to-a-class-discord-py
        """
        self.bot.command(name=name)(wraps(func)(partial(func, self)))

    async def _on_ready(self):
        self.log.info(f"WATCHER: Lenna logged in as user: {self.bot.user}")

    async def bingo(self, ctx):
        """
        Bingo! uwu
        """
        bingo_video = self.responder.get_media(LENA_BINGO_VIDEO)
        await ctx.send(bingo_video)

    async def echo(self, ctx, arg):
        """
        Cutely echoes the message
        """
        await ctx.send(arg)

    async def lookup(self, ctx, doll_name, with_keys_string=""):
        """
        Looks up doll information
        """
        with_keys = with_keys_string == Watcher._INCLUDE_KEYS_STRING
        embed = self._lookup(doll_name, with_keys=with_keys, force=False)

        await ctx.send(embed=embed)

    async def flookup(self, ctx, doll_name, with_keys_string=""):
        with_keys = with_keys_string == Watcher._INCLUDE_KEYS_STRING
        embed = self._lookup(doll_name, with_keys=with_keys, force=True)

        await ctx.send(embed=embed)

    def _lookup(self, doll_name, with_keys=False, force=False):
        """
        Looks up doll information
        """
        embed = None
        try:
            fixed_doll_name = self._fix_doll_name(doll_name)
            embed = self.responder.get_doll(
                fixed_doll_name,
                with_keys=with_keys,
                force=force,
            )

            self.log.info(f"WATCHER: Embed Fields: {str(embed.fields)}")
        except Exception as e:
            self.log.error(
                f"WATCHER: Received an error when looking up doll information for {doll_name}"
            )
            self.log.error(f"WATCHER: Exception:\n{e}")

            lookup_failure_message = f"""
                Eh!? Lenna doesn't know {doll_name}, are you sure you typed their name correctly, Shikikan?
                If you think this is a mistake, please talk to @aguren ~
            """

            embed = discord.Embed(
                title="Doll Lookup Failure",
                description=dedent(lookup_failure_message),
                color=discord.Color.red(),
            )

        return embed

    def run(self):
        """
        Runs the bot inside Watcher
        """
        self.bot.run(self.token)

    def _fix_doll_name(self, doll_name):
        """
        Fixes the doll name to properly capitalize them
        Returns the fixed doll name

        E.g., "MoSIN-naGANt" -> "Mosin-Nagant"

        thank you @jiggles8675!
        """
        return re.sub(
            r"[A-Za-z]+([A-Za-z]+)?", lambda i: i.group(0).capitalize(), doll_name
        )
