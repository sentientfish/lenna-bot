"""
Lenna's Response Handler

Takes user message and prepares the appropriate response
"""

import os
import json

from typing import TypedDict
from doll import Doll

DATA_DIRECTORY = "../data/"
MEDIA_FILE = "media.json"

# Parsing variables
DATA_STRING = "data"
PARSE_STRING = "parse"
WIKITEXT_STRING = "wikitext"
STAR_STRING = "*"

class InvalidMediaException(Exception):
    pass


class MediaFileNotFoundException(Exception):
    pass


class Media(TypedDict):
    """
    Media class definition
    No need to do anything, TypedDict will handle it all
    """
    pass


class Responder:
    def __init__(self):
        self.media_dict = self._load_media()


    def get_media(self, media_name):
        """
        Function to fetch the media needed
        """

        media_link = self.media_dict.get(media_name, None)
        if media_link == None:
            raise InvalidMediaException(f"Media name \"{media_name}\" is \
                    not part of any known media!")

        return media_link


    def get_doll_data(self, doll_name):
        """
        Function to fetch doll information
        """

        doll_json_path = f"{DATA_DIRECTORY}{doll_name}.json"
        if not os.path.exists(doll_json_path):
            print("Still in development")

        # TODO: Implement the query method
        self._query_wiki(doll_name)

        with open(doll_json_path, "r", encoding="utf8") as doll_json_file:
            doll_wikitext = json.load(doll_json_file)[PARSE_STRING]\
                    [WIKITEXT_STRING][STAR_STRING]

            doll = Doll(doll_wikitext)
        
        return doll


    def _load_media(self):
        """
        Internal function to load the media dictionary
        """

        try:
            with open(f"{DATA_DIRECTORY}{MEDIA_FILE}", "r") as media_file:
                media_dict: Media = json.load(media_file)

                return media_dict
        except FileNotFoundError:
            raise MediaFileNotFoundException("Media file is not found!")


    def _query_wiki(self, doll_name):
        """
        Internal function to query the wiki for doll info
        """
        pass