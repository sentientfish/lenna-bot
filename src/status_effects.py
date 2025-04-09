"""
StatusEffects class

a dictionary representation of a status effect's name and its effects
"""

import wikitextparser as wtp

from parse_utils import (
    simplify,
)


class StatusEffects:
    """
    StatusEffects class definition
    """

    _STATUS_HEADER_STRING = "=="
    _SEPARATOR_STRING = "\n\n"
    _STATUS_EFFECT_NAME_START = 3
    _STATUS_EFFECT_NAME_END = -3

    def __init__(self, status_effects_json):
        self.status_effects = self._parse_status_effects_wikitext(status_effects_json)

    def get_status_effect(self, status_effect_name):
        """
        Gets the effect given the status effect name
        """
        return self.status_effects.get(status_effect_name, None)

    def _parse_status_effects_wikitext(self, status_effects_json):
        """
        Maps status effect name to its effect
        """

        # The wikitext follows the format:
        # "{{<some header>}}\n\n<-- <more header> -->\n\n== Status Effect1 ==\n\nEffect\n\n..."
        # So, we skip the two "headers" and then it will alternate between
        # status effect name and its effect
        status_effects = {}
        status_effect_array = status_effects_json.split(self._SEPARATOR_STRING)
        index = 0

        # Skip the "headers"
        while status_effect_array[index][0:2] != self._STATUS_HEADER_STRING:
            index += 1

        while index < len(status_effect_array):
            # At this point, name is of the format:
            # "== Status Effect Name III =="
            # So, we remove the prefix and suffix off the name
            status_effect_name = status_effect_array[index][
                self._STATUS_EFFECT_NAME_START : self._STATUS_EFFECT_NAME_END
            ]
            effect = simplify(status_effect_array[index + 1])

            status_effects[status_effect_name] = effect

            index += 2

        return status_effects
