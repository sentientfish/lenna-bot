"""
Lenna's Response Handler

Takes user message and prepares the appropriate response
"""

import json

from discord import (
    Embed,
    Color,
)
from functools import lru_cache
import requests
from typing import TypedDict

from doll import Doll


IOPWIKI_API_URL = "https://iopwiki.com/api.php?action=parse&prop=wikitext&format=json&redirects=1&page="


class InvalidMediaException(Exception):
    """
    Exception for when media requested is not found in media json
    """

    pass


class MediaFileNotFoundException(Exception):
    """
    Exception for when the media json file is not found
    """

    pass


class DollNotFoundException(Exception):
    """
    Exception for when doll query returned a failure
    """

    pass


class SkillNotFoundException(Exception):
    """
    Exception for when doll skill query returned a failure
    """

    pass


class Media(TypedDict):
    """
    Media class definition
    No need to do anything, TypedDict will handle it all
    """

    pass


class Responder:
    """
    Response handler definition
    """

    # Media-related variables
    _DATA_DIRECTORY = "../data/"
    _MEDIA_FILE = "media.json"

    # Parsing variables
    _DATA_STRING = "data"
    _PARSE_STRING = "parse"
    _WIKITEXT_STRING = "wikitext"
    _STAR_STRING = "*"

    # Query variables
    _SKILL_START_RANGE = 1
    _SKILL_END_RANGE = 5

    # Embed process variables
    _AFFILIATION_STRING = "Affiliation"
    _SIGNATURE_WEAPON_STRING = "Signature Weapon"
    _WEAKNESSES_STRING = "Weaknesses"
    _SKILLS_STRING = "Skills"
    _UPGRADE_EFFECTS_STRING = "Upgrade effect(s):"
    _NODES_STRING = "Nodes"
    _BREAK_TAG = "<br>"
    _NEWLINE_STRING = "\n"
    _STAR_EMOJI_STRING = ":star:"
    _ARROW_EMOJI_STRING = ":arrow_up_small:"

    def __init__(self):
        self.media_dict = self._load_media()

    def get_media(self, media_name):
        """
        Function to fetch the media needed
        """

        media_link = self.media_dict.get(media_name, None)
        if media_link == None:
            raise InvalidMediaException(
                f'Media name "{media_name}" is not part of any known media!'
            )

        return media_link

    def get_doll_data(self, doll_name, include_keys=False):
        """
        Function to fetch doll information
        Returns a discord embed
        """

        doll_data = self._get_doll_data(doll_name)
        doll_skill_data_array = self._get_doll_skills(doll_name)

        doll = Doll(doll_data, doll_skill_data_array)

        embed = Embed(
            title=doll.full_name,
            description=f"{doll.gfl_name}",
            color=Color.orange(),
        )

        embed.add_field(
            name="",
            value=f"{doll.rarity[:-1]}{Responder._STAR_EMOJI_STRING} {doll.role}",
            inline=True,
        )

        embed.add_field(
            name=Responder._AFFILIATION_STRING,
            value=doll.affiliation,
            inline=False,
        )

        embed.add_field(
            name=Responder._SIGNATURE_WEAPON_STRING,
            value=doll.signature_weapon,
            inline=False,
        )

        embed.add_field(
            name=Responder._WEAKNESSES_STRING,
            value=f"{doll.weapon_weakness}{doll.phase_weakness}",
            inline=False,
        )

        embed.add_field(
            name=Responder._SKILLS_STRING,
            value="",
            inline=False,
        )

        for skill in doll.skills:
            skill_name = skill.name
            skill_desc = skill.desc.replace(
                Responder._BREAK_TAG, Responder._NEWLINE_STRING
            )
            skill_extras = skill.extra_effects

            value = f"{skill_desc}"
            if skill_extras:
                value += (
                    f"{Responder._UPGRADE_EFFECTS_STRING}{Responder._NEWLINE_STRING}"
                )
                for extra in skill_extras:
                    value += f"{Responder._ARROW_EMOJI_STRING}{extra}{Responder._NEWLINE_STRING}"

            embed.add_field(
                name=skill_name,
                value=value,
                inline=False,
            )

        if include_keys:
            embed.add_field(
                name=Responder._NODES_STRING,
                value="",
                inline=False,
            )

            for node in doll.nodes:
                node_name = node.name
                node_desc = node.desc.replace(
                    Responder._BREAK_TAG, Responder._NEWLINE_STRING
                )

                embed.add_field(
                    name=node_name,
                    value=node_desc,
                    inline=False,
                )

        return embed

    def _load_media(self):
        """
        Internal function to load the media dictionary
        """

        try:
            with open(
                f"{Responder._DATA_DIRECTORY}{Responder._MEDIA_FILE}", "r"
            ) as media_file:

                media_dict: Media = json.load(media_file)

                return media_dict
        except FileNotFoundError:
            raise MediaFileNotFoundException("Media file is not found!")

    def _get_doll_data(self, doll_name):
        """
        Internal function to query the wiki and get doll info
        """

        try:
            query_url = f"{IOPWIKI_API_URL}{doll_name}"

            return self._query_wiki(query_url)
        except FileNotFoundError:
            raise DollNotFoundException(f"Doll {doll_name} was not found!")

    def _get_doll_skills(self, doll_name):
        """
        Internal function to query the wiki and get doll skills
        """

        try:
            skill_data_array = []
            for i in range(Responder._SKILL_START_RANGE, Responder._SKILL_END_RANGE):
                skill_index_url = "" if i == 1 else i
                skill_query_url = (
                    f"{IOPWIKI_API_URL}{doll_name}/skill{skill_index_url}data"
                )

                skill_data = self._query_wiki(skill_query_url)
                skill_data_array.append(skill_data)

            return skill_data_array
        except FileNotFoundError:
            raise SkillNotFoundException(f"Doll {doll_name} skill {i} was not found!")

    @lru_cache(maxsize=128)
    def _query_wiki(self, query_url):
        """
        Internal function to query the wiki and return the wikitext
        """

        headers = {
            "User-agent": "LennaBot/1.0 (sentientfishsentient@gmail.com)",
            "From": "sentientfishsentient@gmail.com",
        }

        response = requests.get(query_url, headers=headers)
        return json.loads(response.content)[Responder._PARSE_STRING][
            Responder._WIKITEXT_STRING
        ][Responder._STAR_STRING]
