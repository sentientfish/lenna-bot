"""
Lenna's Response Handler

Takes user message and prepares the appropriate response
"""

from datetime import datetime, timezone
import json
import os

from discord import (
    Embed,
    Color,
)
import requests
from typing import TypedDict

from doll import Doll

IOPWIKI_API_URL = "https://iopwiki.com/api.php"
IOPWIKI_DATA_FETCH_PARAM = "?action=parse&prop=wikitext&format=json&redirects=1&page="
IOPWIKI_INFO_FETCH_PARAM = "?action=query&format=json&prop=info&titles="


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
    _FETCHED_STRING = "fetched"

    # Parsing variables
    _DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
    _DATA_STRING = "data"
    _PARSE_STRING = "parse"
    _WIKITEXT_STRING = "wikitext"
    _STAR_STRING = "*"
    _QUERY_STRING = "query"
    _PAGES_STRING = "pages"
    _TOUCHED_STRING = "touched"
    
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
            value=f"{doll.rarity[:-1]}{self._STAR_EMOJI_STRING} {doll.role}",
            inline=True,
        )

        embed.add_field(
            name=self._AFFILIATION_STRING,
            value=doll.affiliation,
            inline=False,
        )

        embed.add_field(
            name=self._SIGNATURE_WEAPON_STRING,
            value=doll.signature_weapon,
            inline=False,
        )

        embed.add_field(
            name=self._WEAKNESSES_STRING,
            value=f"{doll.weapon_weakness}{doll.phase_weakness}",
            inline=False,
        )

        embed.add_field(
            name=self._SKILLS_STRING,
            value="",
            inline=False,
        )

        for skill in doll.skills:
            skill_name = skill.name
            skill_desc = skill.desc.replace(
                self._BREAK_TAG, self._NEWLINE_STRING
            )
            skill_extras = skill.extra_effects

            value = f"{skill_desc}"
            if skill_extras:
                value += (
                    f"{self._UPGRADE_EFFECTS_STRING}{self._NEWLINE_STRING}"
                )
                for extra in skill_extras:
                    value += f"{self._ARROW_EMOJI_STRING}{extra}{self._NEWLINE_STRING}"

            embed.add_field(
                name=skill_name,
                value=value,
                inline=False,
            )

        if include_keys:
            embed.add_field(
                name=self._NODES_STRING,
                value="",
                inline=False,
            )

            for node in doll.nodes:
                node_name = node.name
                node_desc = node.desc.replace(
                    self._BREAK_TAG, self._NEWLINE_STRING
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
                f"{self._DATA_DIRECTORY}{self._MEDIA_FILE}", "r"
            ) as media_file:

                media_dict: Media = json.load(media_file)

                return media_dict
        except FileNotFoundError:
            raise MediaFileNotFoundException("Media file is not found!")

    def _get_doll_data(self, doll_name):
        """
        Internal function to get doll info and query if needed
        """

        doll_file_directory = f"{self._DATA_DIRECTORY}{doll_name}.json"
        query_url = f"{IOPWIKI_API_URL}{IOPWIKI_DATA_FETCH_PARAM}{doll_name}"

        doll_data = self._query_wiki(query_url, doll_name, doll_file_directory)
        if doll_data == None:
            raise DollNotFoundException()
        
        return doll_data

    def _get_doll_skills(self, doll_name):
        """
        Internal function to query the wiki and get doll skills
        """

        skill_data_array = []
        for i in range(self._SKILL_START_RANGE, self._SKILL_END_RANGE):
            skill_index = "" if i == 1 else i
            skill_page = f"{doll_name}/skill{skill_index}data"

            skill_query_url = (
                f"{IOPWIKI_API_URL}{IOPWIKI_DATA_FETCH_PARAM}{skill_page}"
            )
            skill_file_directory = f"{self._DATA_DIRECTORY}{doll_name}_skill{skill_index}.json"

            skill_data = self._query_wiki(skill_query_url, skill_page, skill_file_directory)

            if skill_data == None:
                raise SkillNotFoundException()

            skill_data_array.append(skill_data)

        return skill_data_array

    def _write(self, payload, filename):
        """
        Internal function to write payload into a page

        Expects a JSON payload
        """

        with open(filename, "w", encoding="utf8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=4)

    def _query_page_last_edit(self, page_title):
        """
        Internal function to query the wiki for page information
        Will not work as intended if page_title contains multiple titles

        Returns the last edit ("touched" field) of the page
        """

        query_url = f"{IOPWIKI_API_URL}{IOPWIKI_INFO_FETCH_PARAM}{page_title}"
        query_json = self._send_query(query_url)
        
        pages = query_json["query"]["pages"]
        page_id = None

        # We use for each here, but we only expect 1 page to be returned
        for page in pages:
            page_id = page
        
        return datetime.strptime(pages[page_id][self._TOUCHED_STRING], format=self._DATE_FORMAT)

    def _query_wiki(self, query_url, page_title, cache_directory):
        """
        Internal function to query the wiki and return the wikitext
        TODO: Check if this actually works for every page of interest
        TESTED TO WORK: Doll data, Doll skills
        """

        wikitext_json = None
        try:
            cache = None
            with open(cache_directory, "r", encoding="utf8") as cache_file:
                cache = json.loads(cache_file)
                fetch_time = datetime.strptime(cache[self._FETCHED_STRING], self._DATE_FORMAT)
                days_since = datetime.now(timezone.utc) - fetch_time

                if days_since >= 1:
                    last_edit = self._query_page_last_edit(page_title)

                    if fetch_time > last_edit:
                        cache[self._FETCHED_STRING] = datetime.now(timezone.utc).strftime(self._DATE_FORMAT)
                        wikitext_json = self._get_wikitext(cache)
                    else:
                        wikitext_json = None

        except FileNotFoundError:
            # No file, let wikitext_json stay None and we will query it after this
            pass

        if wikitext_json != None:
            self._write(cache, cache_directory)
        else:
            response_json = self._send_query_and_save(query_url, cache_directory)
            wikitext_json = self._get_wikitext(response_json)

        return wikitext_json

    def _send_query(self, query_url):
        """
        Internal function to send a query
        """
        headers = {
            "User-agent": "LennaBot/1.0 (sentientfishsentient@gmail.com)",
            "From": "sentientfishsentient@gmail.com",
        }

        response = requests.get(query_url, headers=headers)
        return json.loads(response.content)

    def _send_query_and_save(self, query_url, save_directory):
        """
        Internal function to send a query and save it
        """

        response = self._send_query(query_url)
        response_json = json.loads(response.content)

        response_json[self._FETCHED_STRING] = datetime.now(timezone.utc).strftime(self._DATE_FORMAT)

        self._write(response_json, save_directory)

        return response_json

    def _get_wikitext(self, json_obj):
        """
        Internal function to get wikitext from wikimedia api response
        because its annoying as hell
        """

        return json_obj[self._PARSE_STRING][self._WIKITEXT_STRING][self._STAR_STRING]