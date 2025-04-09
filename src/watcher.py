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
ADMIN_ROLES_FILE = "../data/admin.txt"


class Watcher:
    """
    Watcher class definition
    """

    # Doll lookup variable
    _INCLUDE_KEYS_STRING = "with_keys"

    def __init__(self, log, token, cmd_prefix):
        self.admin_roles = []
        with open(ADMIN_ROLES_FILE, "r") as admin_file:
            admin_text = admin_file.read().split("\n")

            for line in admin_text:
                if "#" in line or line == "":
                    continue

                self.admin_roles.append(line)

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
        self._add_command("doll", Watcher.doll)
        self._add_command("mdoll", Watcher.mdoll)
        self._add_command("fdoll", Watcher.fdoll)
        self._add_command("keys", Watcher.keys)
        self._add_command("fkeys", Watcher.fkeys)
        self._add_command("fulldoll", Watcher.fulldoll)
        self._add_command("ffulldoll", Watcher.ffulldoll)
        self._add_command("weapon", Watcher.weapon)
        self._add_command("mweapon", Watcher.mweapon)
        self._add_command("fweapon", Watcher.fweapon)
        self._add_command("define", Watcher.define)

    def close(self):
        self.log.info("WATCHER: Shutting down")
        self.responder.close()

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

    async def echo(self, ctx, *args):
        """
        Cutely echoes the message
        """
        text = " ".join(args)

        await ctx.send(text)

    async def doll(self, ctx, doll_name):
        """
        Looks up doll information
        """
        embed = self._doll_lookup(doll_name, force=False)

        await ctx.send(embed=embed)

    async def mdoll(self, ctx, doll_name):
        """
        For debugging, forces cache lookup
        """
        embed = self._doll_lookup(doll_name, force=False, use_cache=True)

        await ctx.send(embed=embed)

    async def fdoll(self, ctx, doll_name):
        """
        Looks up doll information, forces query to wiki
        """
        if self.allowed(ctx):
            embed = self._doll_lookup(doll_name, force=True)
        else:
            embed = self.create_unallowed_embed()

        await ctx.send(embed=embed)

    async def keys(self, ctx, doll_name):
        """
        Looks up doll information and returns only the keys
        """
        embed = self._doll_lookup(
            doll_name, with_doll=False, with_keys=True, force=False
        )

        await ctx.send(embed=embed)

    async def fkeys(self, ctx, doll_name):
        """
        Looks up doll information and returns only the keys
        """
        if self.allowed(ctx):
            embed = self._doll_lookup(
                doll_name, with_doll=False, with_keys=True, force=False
            )
        else:
            embed = self.create_unallowed_embed()

        await ctx.send(embed=embed)

    async def fulldoll(self, ctx, doll_name):
        """
        Looks up doll information and returns full information
        """
        embed = self._doll_lookup(doll_name, with_keys=True, force=False)

        await ctx.send(embed=embed)

    async def ffulldoll(self, ctx, doll_name):
        """
        Looks up doll information and returns full information
        """
        if self.allowed(ctx):
            embed = self._doll_lookup(doll_name, with_keys=True, force=False)
        else:
            embed = self.create_unallowed_embed()

        await ctx.send(embed=embed)

    async def weapon(self, ctx, *args):
        """
        Looks up weapon information
        """
        weapon_name = " ".join(args)
        embed = self._weapon_lookup(weapon_name)

        await ctx.send(embed=embed)

    async def mweapon(self, ctx, *args):
        """
        For debugging, forces cache lookup
        """
        weapon_name = " ".join(args)
        embed = self._weapon_lookup(weapon_name, use_cache=True)

        await ctx.send(embed=embed)

    async def fweapon(self, ctx, *args):
        """
        Looks up doll information, forces query to wiki
        """
        if self.allowed(ctx):
            weapon_name = " ".join(args)
            embed = self._weapon_lookup(weapon_name, force=True, use_cache=True)
        else:
            embed = self.create_unallowed_embed()

        await ctx.send(embed=embed)

    async def define(self, ctx, *args):
        """
        Defines a status effect
        """

        status_effect_name = " ".join(args)
        embed = self._status_effect_lookup(status_effect_name)

        await ctx.send(embed=embed)

    def allowed(self, ctx):
        """
        Checks whether the author of the message has privilege to run command
        """

        allowed = False
        for role in ctx.author.roles:
            if role.name in self.admin_roles:
                allowed = True
                break

        return allowed

    def create_unallowed_embed(self):
        """
        Creates an embed to show that command is not allowed by user privilege
        """
        unallowed_msg = f"""
            Sorry, Shikikan, but looks like you do not have enough clearance!
            If you think this is an error, please ping @aguren!!!
        """

        embed = discord.Embed(
            title="Unallowed Command",
            description=dedent(unallowed_msg),
            color=discord.Color.red(),
        )

        return embed

    def run(self):
        """
        Runs the bot inside Watcher
        """
        self.bot.run(self.token)

    def _doll_lookup(
        self, doll_name, with_doll=True, with_keys=False, force=False, use_cache=False
    ):
        """
        Looks up doll information
        """
        embed = None
        try:
            fixed_doll_name = self._fix_name(doll_name)
            embed = self.responder.get_doll(
                fixed_doll_name,
                with_doll=with_doll,
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

    def _status_effect_lookup(self, status_effect_name, force=False, use_cache=False):
        embed = None
        try:
            fixed_status_effect_name = self._fix_name(status_effect_name)
            fixed_status_effect_name = self._capitalize_roman_numerals(
                fixed_status_effect_name
            )

            embed = self.responder.get_status_effect(
                fixed_status_effect_name,
                force=force,
                use_cache=use_cache,
            )

            self.log.info(f"WATCHER: Status Effect Embed Fields: {str(embed.fields)}")
        except Exception as e:
            self.log.error(
                f"WATCHER: Received an error when looking up status effect information for {status_effect_name}"
            )
            self.log.error(f"WATCHER: Exception:\n{e}")

            lookup_failure_message = f"""
                Eh!? Lenna doesn't know {status_effect_name}, are you sure you typed the status effect name correctly, Shikikan?
                If you think this is a mistake, please talk to @aguren ~
            """

            embed = discord.Embed(
                title="Status Effect Lookup Failure",
                description=dedent(lookup_failure_message),
                color=discord.Color.red(),
            )

        return embed

    def _fix_name(self, name):
        """
        Fixes the name to properly capitalize them
        Returns the fixed name

        E.g., "MoSIN-naGANt" -> "Mosin-Nagant"

        thank you @jiggles8675!
        """
        return re.sub(r"[A-Za-z]+([A-Za-z]+)?", lambda i: i.group(0).capitalize(), name)

    def _capitalize_roman_numerals(self, string):
        """
        Fixes the string to capitalize roman numerals

        Adapted from chatgpt because @aguren really hates regex (sorry)
        """

        roman_numeral_regex = r"\b[MCDXLIVmcdxliv]+\b"

        return re.sub(roman_numeral_regex, lambda i: i.group(0).upper(), string)
