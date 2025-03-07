"""
Lenna's Response Handler

Takes user message and prepares the appropriate response
"""

import json

from typing import TypedDict


MEDIA_FILE = "../data/media.json"


class InvalidMediaException(Exception):
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


    def _load_media(self):
        """
        Internal function to load the media dictionary
        """

        with open(MEDIA_FILE, "r") as media_file:
            media_dict: Media = json.load(media_file)

            return media_dict


    def get_media(self, media_name):
        """
        Function to fetch the media needed
        """

        media_link = self.media_dict.get(media_name, None)
        if media_link == None:
            raise InvalidMediaException(f"Media name \"{media_name}\" is not part of any known media!")

        return media_link