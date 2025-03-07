"""
Watcher class

Class that basically serves as the bot
It watches channel for prompts and responds as needed
"""

from functools import partial, wraps
import discord
from discord.ext import commands

from responder import Responder

LENA_BINGO_VIDEO = "lenna_bingo_video"


class Watcher:
    """
    Watcher class definition
    """
    def __init__(self, token, cmd_prefix):
        self.token = token
        self.cmd_prefix = cmd_prefix
        self.responder = Responder()

        self.intents = discord.Intents.default()
        self.intents.message_content = True
        self.bot = commands.Bot(command_prefix=cmd_prefix, intents=self.intents)

        self._add_command("bingo", Watcher.bingo)
        self._add_command("echo", Watcher.echo)
        self._add_command("lookup", Watcher.lookup)


    def _add_command(self, name, func):
        """
        Helper function to add the command to the bot
        taken from https://stackoverflow.com/questions/75674926/how-do-i-\
                add-commands-to-a-class-discord-py
        """
        self.bot.command(name=name)(wraps(func)(partial(func, self)))


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
    

    async def lookup(self, ctx, doll_name):
        """
        Looks up doll information
        """
        pass



    def run(self):
        """
        Runs the bot inside Watcher
        """
        self.bot.run(self.token)
    
