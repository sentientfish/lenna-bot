"""
Lenna's Response Handler

Takes user message and prepares the appropriate response
"""

import os
import json

from typing import TypedDict
from discord import (
    Embed,
    Color,
)

from doll import Doll


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

    def __init__(self):
        self.media_dict = self._load_media()

    def get_media(self, media_name):
        """
        Function to fetch the media needed
        """

        media_link = self.media_dict.get(media_name, None)
        if media_link == None:
            raise InvalidMediaException(
                f'Media name "{media_name}" is \
                    not part of any known media!'
            )

        return media_link

    def get_doll_data(self, doll_name, include_keys=False):
        """
        Function to fetch doll information
        Returns a discord embed
        """

        # TODO: Implement the query method
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
            value=f"{doll.rarity[:-1]}:star: {doll.role}",
            inline=True,
        )

        embed.add_field(
            name="Affiliation",
            value=doll.affiliation,
            inline=False,
        )

        embed.add_field(
            name="Signature Weapon",
            value=doll.signature_weapon,
            inline=False,
        )

        embed.add_field(
            name="Weaknesses",
            value=f"{doll.weapon_weakness}{doll.phase_weakness}",
            inline=False,
        )

        embed.add_field(
            name="Skills",
            value="",
            inline=False,
        )

        for skill in doll.skills:
            skill_name = skill.name
            skill_desc = skill.desc.replace("<br>", "\n")
            skill_extras = skill.extra_effects

            value = f"{skill_desc}"
            if skill_extras:
                value += "Upgrade Effect(s):\n"
                for extra in skill_extras:
                    value += f":arrow_up_small:{extra}\n"

            embed.add_field(
                name=skill_name,
                value=value,
                inline=False,
            )

        if include_keys:
            embed.add_field(
                name="Nodes",
                value="",
                inline=False,
            )

            for node in doll.nodes:
                node_name = node.name
                node_desc = node.desc.replace("<br>", "\n")

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

        # TODO: Actually build the query url
        try:
            query_url = f"{Responder._DATA_DIRECTORY}{doll_name}.json"

            return self._query_wiki(query_url)
        except FileNotFoundError:
            raise DollNotFoundException(f"Doll {doll_name} was not found!")

    def _get_doll_skills(self, doll_name):
        """
        Internal function to query the wiki and get doll skills
        """

        # TODO: Actually build the query url
        try:
            skill_data_array = []
            for i in range(Responder._SKILL_START_RANGE, Responder._SKILL_END_RANGE):
                skill_index_url = "" if i == 1 else i
                skill_url = f"{Responder._DATA_DIRECTORY}{doll_name}_skill{skill_index_url}.json"

                skill_data = self._query_wiki(skill_url)
                skill_data_array.append(skill_data)

            return skill_data_array
        except FileNotFoundError:
            raise SkillNotFoundException(f"Doll {doll_name} skill {i} was not found!")

    def _query_wiki(self, query_url):
        """
        Internal function to query the wiki and return the wikitext
        """

        # TODO: Actually query the wiki
        with open(query_url, "r", encoding="utf8") as query_file:
            return json.load(query_file)[Responder._PARSE_STRING][
                Responder._WIKITEXT_STRING
            ][Responder._STAR_STRING]
