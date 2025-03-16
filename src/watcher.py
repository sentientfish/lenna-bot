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
        self._add_command("clookup", Watcher.clookup)
        self._add_command("flookup", Watcher.flookup)
        self._add_command("wlookup", Watcher.wlookup)
        self._add_command("cwlookup", Watcher.cwlookup)

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

    async def echo(self, ctx, *arg):
        """
        Cutely echoes the message
        """
        text = " ".join(arg)

        await ctx.send(text)

    async def clookup(self, ctx, doll_name, with_keys_string=""):
        """
        For debugging, forces cache lookup
        """
        with_keys = with_keys_string == Watcher._INCLUDE_KEYS_STRING
        embed = self._lookup(
            doll_name, with_keys=with_keys, force=False, use_cache=True
        )

        await ctx.send(embed=embed)

    async def lookup(self, ctx, doll_name, with_keys_string=""):
        """
        Looks up doll information
        """
        with_keys = with_keys_string == Watcher._INCLUDE_KEYS_STRING
        embed = self._lookup(doll_name, with_keys=with_keys, force=False)

        await ctx.send(embed=embed)

    async def flookup(self, ctx, doll_name, with_keys_string=""):
        """
        Looks up doll information, forces query to wiki
        """
        with_keys = with_keys_string == Watcher._INCLUDE_KEYS_STRING
        embed = self._lookup(doll_name, with_keys=with_keys, force=True)

        await ctx.send(embed=embed)

    async def cwlookup(self, ctx, *args):
        """
        For debugging, forces cache lookup
        """
        weapon_name = " ".join(args)
        fixed_weapon_name = self._fix_name(weapon_name)

        embed = self._weapon_lookup(fixed_weapon_name, use_cache=True)

        await ctx.send(embed=embed)

    async def wlookup(self, ctx, *args):
        """
        Looks up weapon information
        """
        weapon_name = " ".join(args)
        fixed_weapon_name = self._fix_name(weapon_name)

        embed = self._weapon_lookup(fixed_weapon_name)

        await ctx.send(embed=embed)

    def _lookup(self, doll_name, with_keys=False, force=False, use_cache=False):
        """
        Looks up doll information
        """
        embed = None
        try:
            fixed_doll_name = self._fix_name(doll_name)
            embed = self.responder.get_doll(
                fixed_doll_name,
                with_keys=with_keys,
                force=force,
                use_cache=use_cache,
            )

            self.log.info(f"WATCHER: Doll Embed Fields: {str(embed.fields)}")
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

    def _weapon_lookup(self, weapon_name, force=False, use_cache=False):
        embed = None
        try:
            fixed_weapon_name = self._fix_name(weapon_name)
            embed = self.responder.get_weapon(
                fixed_weapon_name,
                force=force,
                use_cache=use_cache,
            )

            self.log.info(f"WATCHER: Weapon Embed Fields: {str(embed.fields)}")
        except Exception as e:
            self.log.error(
                f"WATCHER: Received an error when looking up weapon information for {weapon_name}"
            )
            self.log.error(f"WATCHER: Exception:\n{e}")

            lookup_failure_message = f"""
                Eh!? Lenna doesn't know {weapon_name}, are you sure you typed the weapon name correctly, Shikikan?
                If you think this is a mistake, please talk to @aguren ~
            """

            embed = discord.Embed(
                title="Weapon Lookup Failure",
                description=dedent(lookup_failure_message),
                color=discord.Color.red(),
            )

        return embed

    def run(self):
        """
        Runs the bot inside Watcher
        """
        self.bot.run(self.token)

    def _fix_name(self, doll_name):
        """
        Fixes the name to properly capitalize them
        Returns the fixed name

        E.g., "MoSIN-naGANt" -> "Mosin-Nagant"

        thank you @jiggles8675!
        """
        return re.sub(
            r"[A-Za-z]+([A-Za-z]+)?", lambda i: i.group(0).capitalize(), doll_name
        )
