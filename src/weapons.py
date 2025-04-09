"""
Weapons class

a collection of the singular, Weapon class
"""

from enum import Enum

import wikitextparser as wtp

from parse_utils import (
    simplify,
    table_data_to_dict,
)


class Weapon:
    """
    Internal representation of a weapon
    """

    def __init__(self, type, name, grade, description, skill, trait, imprint_boost):
        self.type = type
        self.name = name
        self.grade = grade
        self.description = description
        self.skill = skill
        self.trait = trait
        self.imprint_boost = imprint_boost

    def __str__(self):
        return f"Weapon(Name: {self.name}, Type: {self.type}, Grade: {self.grade}, Desc: {self.description}, Skill: {self.skill}, Trait: {self.trait}, Imprint: {self.imprint_boost})"


class Weapons:
    """
    Weapons class definition
    """

    _WEAPON_GRADE_INDEX = 0
    _WEAPON_DESCRIPTION_INDEX = 2
    _WEAPON_SKILL_INDEX = 3
    _WEAPON_TRAIT_INDEX = 4
    _WEAPON_IMPRINT_INDEX = 5

    class WeaponType(Enum):
        HG = 0
        SMG = 1
        AR = 2
        RF = 3
        MG = 4
        SG = 5
        BLADE = 6

    _WEAPON_DATA_START_INDEX = 2

    def __init__(self, weapons_json):
        self.weapons = self._parse_weapons_wikitable(weapons_json)

    def get_weapon(self, weapon_name):
        """
        Function to get a Weapon by weapon_name
        """
        return self.weapons.get(weapon_name, None)

    def _parse_weapons_wikitable(self, weapons_tables_json):
        """
        Parses weapons table into a dictionary of weapon name to Weapon object
        returns said dictionary
        """
        weapons_tables = wtp.parse(weapons_tables_json).tables

        # First, map WeaponType enums to a dictionary of weapons of that type.
        # The wikitext nested dictionary follows the format:
        # key = name
        # value[0] = grade
        # value[1] = icon
        # value[2] = description
        # value[3] = skill
        # value[4] = trait
        # value[5] = imprint
        # value[6] = source/unlock method
        # value[7] = release CN
        # value[8] = release GL
        weapons_dictionaries = {}
        weapons_type_enum_iterator = 0
        for weapons_table in weapons_tables:
            weapons_table_data = weapons_table.data(span=False)
            weapons_table_data = weapons_table_data[self._WEAPON_DATA_START_INDEX :]
            weapons_dict = table_data_to_dict(weapons_table_data)

            weapons_dictionaries[self.WeaponType(weapons_type_enum_iterator)] = (
                weapons_dict
            )
            weapons_type_enum_iterator += 1

        # Maps weapon name to Weapon class
        weapons_dictionary = {}
        for weapon_type in weapons_dictionaries.keys():
            weapons_dict = weapons_dictionaries[weapon_type]

            for weapon_name in weapons_dict:
                weapon_info = weapons_dict[weapon_name]
                weapon = Weapon(
                    weapon_type.name,
                    weapon_name,
                    simplify(weapon_info[self._WEAPON_GRADE_INDEX]),
                    simplify(weapon_info[self._WEAPON_DESCRIPTION_INDEX]),
                    simplify(weapon_info[self._WEAPON_SKILL_INDEX]),
                    simplify(weapon_info[self._WEAPON_TRAIT_INDEX]),
                    simplify(weapon_info[self._WEAPON_IMPRINT_INDEX]),
                )

                weapons_dictionary[weapon_name] = weapon

        return weapons_dictionary
