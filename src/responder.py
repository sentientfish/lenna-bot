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

SPECIAL_NAMES = {
    "Centaureissi": "Centauerissi_(GFL2)",
    "Daiyan": "Daiyan_(GFL2)",
    "Dushevnaya": "Dushevnaya_(GFL2)",
    "Jiangyu": "Jiangyu_(GFL2)",
    "Mosin-Nagant": "Mosin-Nagant_(GFL2)",
    "Springfield": "Springfield_(GFL2)",
    "Suomi": "Suomi_(GFL2)",
    "Vector": "Vector_(GFL2)",
    "Ksenia": "Ksenia_(GFL2)",
}


class InvalidMediaException(Exception):
    """
    Exception for when media requested is not found in media json
    """

    def __init__(self, message):
        self.message = f"InvalidMediaException: {message}"
        super().__init__(self.message)


class MediaFileNotFoundException(Exception):
    """
    Exception for when the media json file is not found
    """

    def __init__(self, message):
        self.message = f"MediaFileNotFoundException: {message}"
        super().__init__(self.message)


class DollNotFoundException(Exception):
    """
    Exception for when doll query returned a failure
    """

    def __init__(self, message):
        self.message = f"DollNotFoundException: {message}"
        super().__init__(self.message)


class SkillNotFoundException(Exception):
    """
    Exception for when doll skill query returned a failure
    """

    def __init__(self, message):
        self.message = f"SkillNotFoundException: {message}"
        super().__init__(self.message)


class CacheNotFoundException(Exception):
    """
    Exception for when cache lookup returned a failure
    """

    def __init__(self, message):
        self.message = f"CacheNotFoundException: {message}"
        super().__init__(self.message)


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
    _CACHE_DIRECTORY = f"{_DATA_DIRECTORY}/cache/"
    _MEDIA_FILE = "media.json"
    _FETCHED_STRING = "fetched"
    _UPDATEABLE_STRING = "updateable"

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
    _SKILL_END_RANGE = 6

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
    _WARNING_FOOTER = f"!!!\nShikikan, Lenna failed to fetch data for this doll, but Lenna remembers them! Make sure to check the data out and see what Lenna missed!\n!!!"

    def __init__(self, log):
        self.media_dict = self._load_media()
        self.log = log

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

    def get_doll(self, doll_name, include_keys=False, use_cache=False):
        """
        Function to fetch doll information
        Returns a discord embed
        """
        updateable = True
        update_cache = False
        try:
            raw_doll_data, update, doll_file_directory, doll_data_updateable = (
                self._get_doll_data(doll_name, use_cache=use_cache)
            )
            raw_doll_skills, update_list, skill_directories, skill_data_updateable = (
                self._get_doll_skills(doll_name, use_cache=use_cache)
            )

            updateable = (
                False if not doll_data_updateable or not skill_data_updateable else True
            )

            doll_data, doll_skills = self._process_raw_doll_info(
                raw_doll_data, raw_doll_skills
            )
            doll = Doll(doll_data, doll_skills)

            # If any response is True, we update
            update_cache = update
            for update_skill in update_list:
                update_cache = update_cache or update_skill

        except Exception as e:
            if isinstance(e, CacheNotFoundException):
                raise

            # Doll was not parseable, use cache
            self.log.error(
                f"RESPONDER: Ran into an error when looking up doll information for {doll_name}"
            )
            self.log.error(f"RESPONDER: Exception:\n{e}")
            self.log.info("RESPONDER: Attempting to use cache...")

            # If we reach here, that definitely means something went wrong
            # we want to update our cache if we can
            update_cache = True
            use_cache = True
            updateable = False
            raw_doll_data, update, doll_file_directory, _ = self._get_doll_data(
                doll_name, use_cache=use_cache
            )
            raw_doll_skills, update_list, skill_directories, _ = self._get_doll_skills(
                doll_name, use_cache=use_cache
            )

            doll_data, doll_skills = self._process_raw_doll_info(
                raw_doll_data, raw_doll_skills
            )

            doll = Doll(doll_data, doll_skills)

        if update_cache:
            self._update(raw_doll_data, doll_file_directory, updateable)
            for raw_doll_skill, skill_directory, update_skill in zip(
                raw_doll_skills, skill_directories, update_list
            ):
                self._update(raw_doll_skill, skill_directory, updateable)

        embed = Embed(
            title=doll.full_name,
            description=f"{doll.gfl_name}",
            color=Color.orange(),
        )

        if not updateable:
            embed.set_footer(
                text=self._WARNING_FOOTER,
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
            skill_desc = skill.desc.replace(self._BREAK_TAG, self._NEWLINE_STRING)
            skill_extras = skill.extra_effects

            embed.add_field(
                name=skill_name,
                value=skill_desc,
                inline=False,
            )

            embed.add_field(
                name="",
                value=self._UPGRADE_EFFECTS_STRING,
                inline=False,
            )

            if skill_extras:
                for extra in skill_extras:
                    embed.add_field(
                        name="",
                        value=f"{self._ARROW_EMOJI_STRING}{extra}{self._NEWLINE_STRING}",
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
                node_desc = node.desc.replace(self._BREAK_TAG, self._NEWLINE_STRING)

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
            with open(f"{self._DATA_DIRECTORY}{self._MEDIA_FILE}", "r") as media_file:

                media_dict: Media = json.load(media_file)

                return media_dict
        except FileNotFoundError:
            raise MediaFileNotFoundException("Media file is not found!")

    def _process_raw_doll_info(self, raw_doll_data, raw_doll_skills):
        doll_data = self._get_wikitext(raw_doll_data)

        doll_skills = []
        for raw_doll_skill in raw_doll_skills:
            doll_skill = self._get_wikitext(raw_doll_skill)
            doll_skills.append(doll_skill)

        return doll_data, doll_skills

    def _get_doll_data(self, doll_name, use_cache=False):
        """
        Internal function to get doll info

        Returns:
        raw_doll_data: data of raw doll data in JSON format
        update: whether or not the doll data cache should be updated
        doll_file_directory: location of where the doll cache should be located
        updateable: whether or not the skill data should be updated
        """

        doll_file_directory = f"{self._CACHE_DIRECTORY}{doll_name.lower()}.json"

        doll_name = SPECIAL_NAMES.get(doll_name, doll_name)
        query_url = f"{IOPWIKI_API_URL}{IOPWIKI_DATA_FETCH_PARAM}{doll_name}"

        raw_doll_data, update, updateable = self._query_wiki(
            query_url, doll_name, doll_file_directory, use_cache
        )
        if raw_doll_data == None:
            raise DollNotFoundException(f"Doll {doll_name} was not found!")

        return raw_doll_data, update, doll_file_directory, updateable

    def _get_doll_skills(self, doll_name, use_cache=False):
        """
        Internal function to get doll skills

        Returns:
        skill_list: list of doll raw doll skills in JSON format
        update_list: list of whether or not the respective skills should be updated
        skill_directories: location of where the skill_data cache should be located
        updateable: whether or not the skill data should be updated
        """

        raw_skill_list = []
        update_list = []
        skill_directories = []
        query_doll_name = SPECIAL_NAMES.get(doll_name, doll_name)
        updateable = True
        for i in range(self._SKILL_START_RANGE, self._SKILL_END_RANGE):
            skill_index = "" if i == 1 else i

            skill_page = f"{query_doll_name}/skill{skill_index}data"
            skill_query_url = f"{IOPWIKI_API_URL}{IOPWIKI_DATA_FETCH_PARAM}{skill_page}"
            skill_file_directory = (
                f"{self._CACHE_DIRECTORY}{doll_name.lower()}_skill{skill_index}.json"
            )

            raw_skill_data, update, json_updateable = self._query_wiki(
                skill_query_url, skill_page, skill_file_directory, use_cache
            )
            updateable = updateable if not updateable else json_updateable

            if raw_skill_data == None:
                raise SkillNotFoundException(f"Skill {skill_page} was not found!")

            raw_skill_list.append(raw_skill_data)
            update_list.append(update)
            skill_directories.append(skill_file_directory)

        return raw_skill_list, update_list, skill_directories, updateable

    def _query_page_last_edit(self, page_title):
        """
        Internal function to query the wiki for page information
        Will not work as intended if page_title contains multiple titles

        Returns the last edit ("touched" field) of the page
        """

        query_url = f"{IOPWIKI_API_URL}{IOPWIKI_INFO_FETCH_PARAM}{page_title}"
        query_json = self._query(query_url)

        pages = query_json["query"]["pages"]
        page_id = None

        # We use for each here, but we only expect 1 page to be returned
        for page in pages:
            page_id = page

        return datetime.strptime(
            pages[page_id][self._TOUCHED_STRING], format=self._DATE_FORMAT
        )

    def _query_wiki(self, query_url, page_title, cache_directory, use_cache=False):
        """
        Internal function to query the wiki and return the wikitext
        TODO: Check if this actually works for every page of interest
        TESTED TO WORK: Doll data, Doll skills
        """

        try:
            cache = None
            with open(cache_directory, "r", encoding="utf8") as cache_file:
                cache = json.load(cache_file)
                updateable = cache[self._UPDATEABLE_STRING]
                fetch_time = datetime.strptime(
                    cache[self._FETCHED_STRING], self._DATE_FORMAT
                )
                days_since = datetime.now(timezone.utc) - fetch_time.replace(
                    tzinfo=timezone.utc
                )

                if not updateable or use_cache:
                    self.log.warning(f"RESPONDER: Force use of cache for {page_title}!")
                    return cache, False if not updateable else True, updateable
                elif days_since.days >= 1:
                    last_edit = self._query_page_last_edit(page_title)

                    if fetch_time > last_edit:
                        return cache, False, updateable
                else:
                    self.log.info(
                        f"RESPONDER: Data fetched less than a day ago, using cache."
                    )
                    return cache, False, updateable

        except FileNotFoundError:
            self.log.info(f"RESPONDER: Unable to find cache for {page_title}!")

            if use_cache:
                self.log.error(f"RESPONDER: use_cache is True, but there is no cache!")
                raise CacheNotFoundException()

            self.log.info("RESPONDER: Allowed to query!")

        response_json = self._query(query_url)

        return response_json, True, True

    def _query(self, query_url):
        """
        Internal function to send a query
        """
        self.log.info(f"RESPONDER: Querying {query_url}")

        headers = {
            "User-agent": "LennaBot/1.0 (sentientfishsentient@gmail.com)",
            "From": "sentientfishsentient@gmail.com",
        }

        response = requests.get(query_url, headers=headers)
        return json.loads(response.content)

    def _get_wikitext(self, json_obj):
        """
        Internal function to get wikitext from wikimedia api response
        because it's annoying as hell
        """

        return json_obj[self._PARSE_STRING][self._WIKITEXT_STRING][self._STAR_STRING]

    def _write(self, payload, filename):
        """
        Internal function to write payload into a page

        Expects a JSON payload
        """
        with open(filename, "w", encoding="utf8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=4)

    def _update(self, file_content, file_directory, updateable):
        """
        Internal function to update the local cache
        """
        self.log.info(f"RESPONDER: Updating {file_directory}.")

        file_content[self._FETCHED_STRING] = datetime.now(timezone.utc).strftime(
            self._DATE_FORMAT
        )
        file_content[self._UPDATEABLE_STRING] = updateable

        self._write(file_content, file_directory)
