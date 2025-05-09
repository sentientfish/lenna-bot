"""
Lenna's Response Handler

Takes user message and prepares the appropriate response
"""

from datetime import datetime, timezone
import json
from textwrap import dedent

from discord import (
    Embed,
    Color,
)
import requests
from typing import TypedDict

from doll import Doll
from weapons import Weapons
from special_names import (
    SPECIAL_DOLL_NAMES,
    SPECIAL_WEAPON_NAMES,
)
from status_effects import StatusEffects
from parse_utils import (
    get_wikitext,
)

IOPWIKI_API_URL = "https://iopwiki.com/api.php"
IOPWIKI_DATA_FETCH_PARAM = "?action=parse&prop=wikitext&format=json&redirects=1&page="
IOPWIKI_INFO_FETCH_PARAM = "?action=query&format=json&prop=info&titles="
IOPWIKI_WEAPONS_PAGE = "GFL2_Weapons"
IOPWIKI_STATUS_EFFECTS_PAGE = "GFL2_Status_Effects"


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


class WeaponNotFoundException(Exception):
    """
    Exception for when weapon query returned a failure
    """

    def __init__(self, message):
        self.message = f"WeaponNotFoundException: {message}"
        super().__init__(self.message)


class StatusEffectNotFoundException(Exception):
    """
    Exception for when status effect query returned a failure
    """

    def __init__(self, message):
        self.message = f"StatusEffectNotFoundException: {message}"
        super().__init__(self.message)


class CacheNotFoundException(Exception):
    """
    Exception for when cache lookup returned a failure
    """

    def __init__(self, message):
        self.message = f"CacheNotFoundException: {message}"
        super().__init__(self.message)


class QueryFailedException(Exception):
    """
    Exception for when a query fails
    """

    def __init__(self, message):
        self.message = f"QueryFailedException: {message}"
        super().__init__(self.message)


class ForceQueryFailedException(QueryFailedException):
    """
    Exception for when a force query fails
    """

    def __init__(self, message):
        self.message = f"ForceQueryFailedException: {message}"
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
    _DATA_DIRECTORY = "../data"
    _CACHE_DIRECTORY = f"{_DATA_DIRECTORY}/cache/"
    _HEADERS_FILE = "headers.json"
    _MEDIA_FILE = "media.json"
    _COMMANDS_FILE = "commands.json"
    _WEAPONS_CACHE_FILE = "weapons.json"
    _STATUS_EFFECTS_CACHE_FILE = "status_effects.json"
    _FETCHED_STRING = "fetched"
    _UPDATEABLE_STRING = "updateable"
    _COMMAND_HELPSTRING = "helpstring"
    _COMMAND_ARGS = "args"
    _COMMAND_EXAMPLE = "example"

    # Parsing variables
    _DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
    _TOUCHED_STRING = "touched"
    _QUERY_STRING = "query"
    _PAGES_STRING = "pages"

    # Query variables
    _SKILL_START_RANGE = 1
    _SKILL_END_RANGE = 6
    _GOOD_RESPONSE_CODE = 200
    _HEADERS = {
        "User-agent": "LennaBot/1.0 (sentientfishsentient@gmail.com)",
        "From": "sentientfishsentient@gmail.com",
    }
    _ERR_STRING = "error"

    # Embed process variables
    _BREAK_TAG = "<br>"
    _NEWLINE_STRING = "\n"
    _STAR_EMOJI_STRING = ":star:"
    _ARROW_EMOJI_STRING = ":arrow_up_small:"

    def __init__(self, log, cmd_prefix):
        self.media_dict = self._load_media()
        self.log = log
        self.cmd_prefix = cmd_prefix
        self.weapons = None
        self.status_effects = None
        self.session = requests.Session()

        self.session.headers.update(self._get_headers())

    def close(self):
        self.log.info("RESPONDER: Shutting down")
        self.session.close()

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

    def get_help_embed(self, command_name=""):
        """
        Function to prepare a help embed
        """

        embed = Embed(
            title="Available Commands",
            description=f"Command prefix: {self.cmd_prefix}",
            color=Color.orange(),
        )

        with open(f"{self._DATA_DIRECTORY}/{self._COMMANDS_FILE}", "r") as cmd_file:
            cmd_json = json.load(cmd_file)

            if command_name != "":
                command_fields = cmd_json[command_name]
                self.get_command_help_embed(
                    command_fields, command_name, embed, single_command=True
                )
            else:
                for command in cmd_json:
                    command_fields = cmd_json[command]

                    self.get_command_help_embed(command_fields, command, embed)

        return embed

    def get_command_help_embed(self, cmd_dict, command, embed, single_command=False):
        """
        Function to prepare a specific command's help embed
        """

        embed_field_value = f"{cmd_dict[self._COMMAND_HELPSTRING]}\n"
        args = cmd_dict[self._COMMAND_ARGS]

        if len(args) > 0:
            embed_field_value += "args:\n"
            for arg in args:
                embed_field_value += f"{arg}: {args[arg]}\n"

        embed_field_value += f"\nExample: `{cmd_dict[self._COMMAND_EXAMPLE]}`\n"

        if not single_command:
            embed.add_field(name=command, value=embed_field_value, inline=False)
        else:
            embed.title = command
            embed.description = embed_field_value

    def get_doll(
        self, doll_name, with_doll=True, with_keys=False, use_cache=False, force=False
    ):
        """
        Function to fetch doll information
        Returns a discord embed
        """

        updateable = True
        update_cache = False
        try:
            raw_doll_data, update, doll_file_directory, doll_data_updateable = (
                self._get_doll_data(doll_name, use_cache=use_cache, force=force)
            )
            raw_doll_skills, update_list, skill_directories, skill_data_updateable = (
                self._get_doll_skills(doll_name, use_cache=use_cache, force=force)
            )

            updateable = (
                False if not doll_data_updateable or not skill_data_updateable else True
            )

            doll_data, doll_skills = self._process_raw_doll_info(
                raw_doll_data, raw_doll_skills
            )
            doll = Doll(doll_data, doll_skills)

            # If any response is True, we update
            update_cache = update or any(update_list)

        except Exception as e:
            if isinstance(e, CacheNotFoundException):
                raise
            elif force:
                self.log.error(
                    f"RESPONDER: Forced doll query failed! Stopping lookup..."
                )
                raise

            # Doll was not parseable, use cache
            self.log.error(
                f"RESPONDER: Ran into an error when looking up doll information for {doll_name}"
            )
            self.log.error(f"RESPONDER: Exception:\n{e}")
            self.log.info("RESPONDER: Attempting to use cache...")

            # If we reach here, that definitely means something went wrong
            # we want to update our cache if we can so we do not query it in the future
            update_cache = True
            use_cache = True
            updateable = False
            raw_doll_data, update, doll_file_directory, _ = self._get_doll_data(
                doll_name, use_cache=use_cache, force=force
            )
            raw_doll_skills, update_list, skill_directories, _ = self._get_doll_skills(
                doll_name, use_cache=use_cache, force=force
            )

            doll_data, doll_skills = self._process_raw_doll_info(
                raw_doll_data, raw_doll_skills
            )

            doll = Doll(doll_data, doll_skills)

        if update_cache:
            self._update(raw_doll_data, doll_file_directory, updateable)
            for raw_doll_skill, skill_directory in zip(
                raw_doll_skills, skill_directories
            ):
                self._update(raw_doll_skill, skill_directory, updateable)

        embed = Embed(
            title=doll.full_name,
            description=f"{doll.gfl_name if doll.gfl_name is not None else ""}",
            color=Color.orange(),
        )

        if not updateable:
            embed.set_footer(
                text=dedent(
                    """
                    !!!\nShikikan, Lenna failed to fetch data for this doll, but Lenna remembers them! Make sure to check the data out and see what Lenna missed!\n!!!
                    """
                )
            )

        if with_doll:
            embed.add_field(
                name="",
                value=f"{doll.rarity[:-1]}{self._STAR_EMOJI_STRING} {doll.role}",
                inline=True,
            )

            embed.add_field(
                name="Affiliation",
                value=doll.affiliation,
                inline=False,
            )

            if doll.signature_weapon != None:
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
                skill_desc = skill.desc.replace(self._BREAK_TAG, self._NEWLINE_STRING)
                skill_extras = skill.extra_effects

                embed.add_field(
                    name=skill_name,
                    value=skill_desc,
                    inline=False,
                )

                embed.add_field(
                    name="",
                    value="Upgrade effect(s):",
                    inline=False,
                )

                if skill_extras:
                    for extra in skill_extras:
                        extra_desc = extra.replace(
                            self._BREAK_TAG, self._NEWLINE_STRING
                        )
                        embed.add_field(
                            name="",
                            value=f"{self._ARROW_EMOJI_STRING}{extra_desc}{self._NEWLINE_STRING}",
                            inline=False,
                        )

        if with_keys:
            embed.add_field(
                name="Nodes",
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

    def get_weapon(self, weapon_name, use_cache=False, force=False):
        """
        Function to fetch weapon information
        Returns a discord embed
        """

        updateable = True
        weapon_name = SPECIAL_WEAPON_NAMES.get(weapon_name, weapon_name)
        weapons_cache_directory = f"{self._CACHE_DIRECTORY}{self._WEAPONS_CACHE_FILE}"
        weapons_query_url = (
            f"{IOPWIKI_API_URL}{IOPWIKI_DATA_FETCH_PARAM}{IOPWIKI_WEAPONS_PAGE}"
        )
        try:
            raw_weapons_data, update, updateable = self._query_wiki(
                weapons_query_url,
                IOPWIKI_WEAPONS_PAGE,
                weapons_cache_directory,
                use_cache=use_cache,
                force=force,
            )

            weapons_data = get_wikitext(raw_weapons_data)
            if update or self.weapons == None:
                self.weapons = Weapons(weapons_data)

        except Exception as e:
            if isinstance(e, CacheNotFoundException):
                raise
            elif force:
                self.log.error(
                    f"RESPONDER: Forced weapon query failed! Stopping lookup..."
                )
                raise

            # Weapons page was not parseable, use cache
            self.log.error(
                f"RESPONDER: Ran into an error when looking up weapon information for {weapon_name}"
            )
            self.log.error(f"RESPONDER: Exception:\n{e}")
            self.log.info("RESPONDER: Attempting to use cache...")

            # If we reach here, that definitely means something went wrong
            # we want to update our cache if we can so we do not query it in the future
            update = True
            use_cache = True
            updateable = False

            raw_weapons_data, _, _ = self._query_wiki(
                weapons_query_url,
                IOPWIKI_WEAPONS_PAGE,
                weapons_cache_directory,
                use_cache=use_cache,
                force=force,
            )

        if update:
            self._update(raw_weapons_data, weapons_cache_directory, updateable)

        weapon = self.weapons.get_weapon(weapon_name)
        if weapon == None:
            raise WeaponNotFoundException(f"Weapon {weapon_name} was not found!")

        embed = Embed(
            title=weapon.name,
            description=f"{weapon.grade} {weapon.type}",
            color=Color.orange(),
        )

        if not updateable:
            embed.set_footer(
                text=dedent(
                    """
                !!!\nShikikan, Lenna failed to fetch data for this weapon, but Lenna remembers it! Make sure to check the data out and see what Lenna missed!\n!!!
                """
                )
            )

        embed.add_field(name="Imprint", value=weapon.imprint_boost, inline=False)

        embed.add_field(
            name="Skill",
            value=weapon.skill,
            inline=False,
        )

        embed.add_field(name="Trait", value=weapon.trait, inline=False)

        embed.add_field(name="Description", value=weapon.description, inline=False)

        return embed

    def get_status_effect(self, status_effect_name, use_cache=False, force=False):
        """
        Function to fetch status effect
        Returns a discord embed
        """

        updateable = True
        status_effects_cache_directory = (
            f"{self._CACHE_DIRECTORY}{self._STATUS_EFFECTS_CACHE_FILE}"
        )
        status_effects_query_url = (
            f"{IOPWIKI_API_URL}{IOPWIKI_DATA_FETCH_PARAM}{IOPWIKI_STATUS_EFFECTS_PAGE}"
        )

        try:
            raw_status_effects_data, update, updateable = self._query_wiki(
                status_effects_query_url,
                IOPWIKI_WEAPONS_PAGE,
                status_effects_cache_directory,
                use_cache=use_cache,
                force=force,
            )

            status_effects_data = get_wikitext(raw_status_effects_data)
            if update or self.status_effects == None:
                self.status_effects = StatusEffects(status_effects_data)

        except Exception as e:
            if isinstance(e, CacheNotFoundException):
                raise
            elif force:
                self.log.error(
                    f"RESPONDER: Forced status effect query failed! Stopping lookup..."
                )
                raise
                # Weapons page was not parseable, use cache

            self.log.error(
                f"RESPONDER: Ran into an error when looking up status effect information for {status_effect_name}"
            )
            self.log.error(f"RESPONDER: Exception:\n{e}")
            self.log.info("RESPONDER: Attempting to use cache...")

            # If we reach here, that definitely means something went wrong
            # we want to update our cache if we can so we do not query it in the future
            update = True
            use_cache = True
            updateable = False

            raw_status_effects_data, update, updateable = self._query_wiki(
                status_effects_query_url,
                IOPWIKI_WEAPONS_PAGE,
                status_effects_cache_directory,
                use_cache=use_cache,
                force=force,
            )

        if update:
            self._update(
                raw_status_effects_data, status_effects_cache_directory, updateable
            )

        effect = self.status_effects.get_status_effect(status_effect_name)
        if effect == None:
            raise StatusEffectNotFoundException(
                f"Status effect {status_effect_name} was not found!"
            )

        embed = Embed(
            title=status_effect_name,
            description=effect,
            color=Color.orange(),
        )

        if not updateable:
            embed.set_footer(
                text=dedent(
                    """
                !!!\nShikikan, Lenna failed to fetch data for this status effect, but Lenna remembers it! Make sure to check the data out and see what Lenna missed!\n!!!
                """
                )
            )

        return embed

    def _load_media(self):
        """
        Internal function to load the media dictionary
        """

        try:
            with open(f"{self._DATA_DIRECTORY}/{self._MEDIA_FILE}", "r") as media_file:

                media_dict: Media = json.load(media_file)

                return media_dict
        except FileNotFoundError:
            raise MediaFileNotFoundException("Media file is not found!")

    def _process_raw_doll_info(self, raw_doll_data, raw_doll_skills):
        doll_data = get_wikitext(raw_doll_data)

        doll_skills = []
        for raw_doll_skill in raw_doll_skills:
            doll_skill = get_wikitext(raw_doll_skill)
            doll_skills.append(doll_skill)

        return doll_data, doll_skills

    def _get_doll_data(self, doll_name, use_cache=False, force=False):
        """
        Internal function to get doll info

        Returns:
        raw_doll_data: data of raw doll data in JSON format
        update: whether or not the doll data cache should be updated
        doll_file_directory: location of where the doll cache should be located
        updateable: whether or not the skill data should be updated
        """

        doll_file_directory = f"{self._CACHE_DIRECTORY}{doll_name.lower()}.json"

        doll_name = SPECIAL_DOLL_NAMES.get(doll_name, doll_name)
        query_url = f"{IOPWIKI_API_URL}{IOPWIKI_DATA_FETCH_PARAM}{doll_name}"

        raw_doll_data, update, updateable = self._query_wiki(
            query_url, doll_name, doll_file_directory, use_cache=use_cache, force=force
        )
        if raw_doll_data == None:
            raise DollNotFoundException(f"Doll {doll_name} was not found!")

        return raw_doll_data, update, doll_file_directory, updateable

    def _get_doll_skills(self, doll_name, use_cache=False, force=False):
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
        query_doll_name = SPECIAL_DOLL_NAMES.get(doll_name, doll_name)
        updateable = True
        for i in range(self._SKILL_START_RANGE, self._SKILL_END_RANGE):
            skill_index = "" if i == 1 else i

            skill_page = f"{query_doll_name}/skill{skill_index}data"
            skill_query_url = f"{IOPWIKI_API_URL}{IOPWIKI_DATA_FETCH_PARAM}{skill_page}"
            skill_file_directory = (
                f"{self._CACHE_DIRECTORY}{doll_name.lower()}_skill{skill_index}.json"
            )

            raw_skill_data, update, json_updateable = self._query_wiki(
                skill_query_url,
                skill_page,
                skill_file_directory,
                use_cache=use_cache,
                force=force,
            )
            updateable = updateable if not updateable else json_updateable

            if raw_skill_data == None:
                raise SkillNotFoundException(f"Skill {skill_page} was not found!")

            raw_skill_list.append(raw_skill_data)
            update_list.append(update)
            skill_directories.append(skill_file_directory)

        return raw_skill_list, update_list, skill_directories, updateable

    def _get_headers(self):
        """
        Prepares the query headers
        """

        headers_file_dir = f"{self._DATA_DIRECTORY}/{self._HEADERS_FILE}"

        with open(headers_file_dir, "r") as headers_file:
            return dict(json.load(headers_file))

    def _query_page_last_edit(self, page_title):
        """
        Internal function to query the wiki for page information
        Will not work as intended if page_title contains multiple titles

        Returns the last edit ("touched" field) of the page
        """

        query_url = f"{IOPWIKI_API_URL}{IOPWIKI_INFO_FETCH_PARAM}{page_title}"
        query_json = self._query(query_url)

        pages = query_json[self._QUERY_STRING][self._PAGES_STRING]
        page_id = None

        # We use for each here, but we only expect 1 page to be returned
        for page in pages:
            page_id = page

        return datetime.strptime(
            pages[page_id][self._TOUCHED_STRING], self._DATE_FORMAT
        )

    def _query_wiki(
        self, query_url, page_title, cache_directory, use_cache=False, force=False
    ):
        """
        Internal function to query the wiki and return the wikitext
        """

        if not force:
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
                        self.log.warning(
                            f"RESPONDER: Force use of cache for {page_title}!"
                        )
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
                    self.log.error(
                        f"RESPONDER: use_cache is True, but there is no cache!"
                    )
                    raise CacheNotFoundException(
                        f"Cache lookup of {cache_directory} not found!"
                    )

                self.log.info("RESPONDER: Allowed to query!")

        response_json = self._query(query_url)

        return response_json, True, True

    def _query(self, query_url):
        """
        Internal function to send a query
        """

        self.log.info(f"RESPONDER: Querying {query_url}")

        req = requests.Request("GET", query_url)
        prepared_req = self.session.prepare_request(req)

        response = self.session.send(prepared_req)
        content = json.loads(response.content)

        reason = None
        if response.status_code != self._GOOD_RESPONSE_CODE:
            reason = response.reason
        elif self._ERR_STRING in content:
            reason = content[self._ERR_STRING]["info"]

        if reason != None:
            self.log.error(f"RESPONDER: Failed to query {query_url}")
            self.log.error(f"Reason: {reason}")

            raise QueryFailedException(reason)

        return content

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
