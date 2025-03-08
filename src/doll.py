"""
Doll class

Takes a wikitext and parses it into information of interest
Fields and their wikitext correspondent:
-----------------------------------------------------
| No.   | Wikitext          | Field                 |
-----------------------------------------------------
| 01    | fullName          | full_name             |
| 02    | role              | role                  |
| 03    | rarity            | rarity                |
| 04    | affiliation       | affiliation           |
| 05    | favweapon         | weapon_name           |
| 06    | imprint           | signature_weapon      |
| 07    | wepweakness       | weapon_weakness       |
| 08    | phaseweakness     | phase_weakness        |
| 09    | GFL               | gfl_name              |
| 10    | Node*             | nodes                 |
| 11    | N/A               | skills                |
-----------------------------------------------------
"""

import wikitextparser as wtp

# Important nodes that the class will try to parse for
IMPORTANT_NODES = [
    4,
    7,
    10,
    11,
]


class Node:
    """
    Class representation of a doll's neural node
    """

    def __init__(self, name, desc, position):
        self.name = name
        self.desc = desc
        self.position = position

    def __str__(self):
        return f"name: {self.name}\ndesc: {self.desc}\nposition: {self.position}\n"


class Skill:
    """
    Internal representation of a doll's skill
    """

    def __init__(self, name, desc, extra_effects):
        self.name = name
        self.desc = desc
        self.extra_effects = extra_effects

    def __str__(self):
        return f"name: {self.name}\ndesc: {self.desc}\nextra_effects: {self.extra_effects}\n"


class Doll:
    """
    Doll class definition
    """

    # Internal variables to parse wikitext
    _BASE_TEMPLATE_INDEX = 0
    _VALUE_INDEX = 1
    _WEAK_ICON_STRING = "GFL2WeakIcon"
    _IGNORED_KEYS = [
        "icon",
        "skilllevelcount",
    ]
    _KEY_INDEX = 0
    _FIRST_VALUE_INDEX = 1
    _SIMPLE_DATA_ARRAY_LENGTH = 2
    _KEY_POSITION_START_RANGE = 1
    _KEY_POSITION_END_RANGE = 3
    _INVALID_KEY_POSITION = 0

    class SKILL_PARAMETER_STRING:
        """
        Internal class to denote skill table fields
        """

        NAME_STRING = "name"
        TEXT_STRING = "text"
        EXTRA_EFFECT_STRING = "extraeffect"

    def __init__(self, doll_data, skill_data_array):
        template = self._get_base_template(doll_data)

        self.full_name = self._get_template_param_value(template, "fullname")
        self.role = self._get_template_param_value(template, "role")
        self.rarity = self._get_template_param_value(template, "rarity")
        self.affiliation = self._get_template_param_value(template, "affiliation")
        self.weapon_name = self._get_template_param_value(template, "favweapon")
        self.signature_weapon = self._get_template_param_value(template, "imprint")
        self.weapon_weakness = self._get_template_param_value(template, "wepweakness")
        self.phase_weakness = self._get_template_param_value(template, "phaseweakness")
        self.gfl_name = self._get_template_param_value(template, "GFL")

        self.nodes = self._get_nodes(template)
        self.skills = self._get_skills(skill_data_array)

    def _get_node(self, template, node_position, is_key=False, key_position=0):
        """
        Internal function to get node from wikitext template
        """

        name = None
        if is_key:
            name_string = f"Node{node_position}name"
            if key_position != Doll._INVALID_KEY_POSITION:
                name_string += f"{key_position}"
            name_wikitext = self._get_template_param_value(template, name_string)

            name_template = self._get_base_template(name_wikitext)
            name = name_template.arguments[1].value

        desc_string = f"Node{node_position}desc"
        if key_position != Doll._INVALID_KEY_POSITION:
            desc_string += f"{key_position}"

        desc = self._get_template_param_value(template, desc_string)
        desc = self._simplify(desc)
        node = Node(name, desc, node_position)

        return node

    def _get_nodes(self, template):
        """
        Internal function to get all doll nodes
        """

        nodes = []
        for important_node in IMPORTANT_NODES:
            for i in range(
                Doll._KEY_POSITION_START_RANGE, Doll._KEY_POSITION_END_RANGE
            ):
                key_position = i
                if important_node == 11:
                    key_position = Doll._INVALID_KEY_POSITION

                node = self._get_node(
                    template, important_node, is_key=True, key_position=key_position
                )

                nodes.append(node)

        return nodes

    def _get_skills(self, skill_data_array):
        """
        Internal function to parse doll skill tables
        """

        skills = []
        for skill_data in skill_data_array:

            skill = self._parse_skill_table(skill_data)
            skills.append(skill)

        return skills

    def _table_data_to_dict(self, table_data):
        """
        Internal function to convert wikitable data into a dictionary
        """

        table_dictionary = {}
        for data in table_data:
            key = data[Doll._KEY_INDEX]
            data_array_length = len(data)

            value = ""
            if data_array_length > Doll._SIMPLE_DATA_ARRAY_LENGTH:
                value = []

                for i in range(Doll._FIRST_VALUE_INDEX, data_array_length):
                    data_val = data[i]
                    value.append(data_val)
            else:
                value = data[Doll._FIRST_VALUE_INDEX]

            table_dictionary[key] = value

        return table_dictionary

    def _simplify(self, wikitext):
        """
        Internal function to simply the wikitext and remove all templates
        and wikilinks
        """

        wikitext = self._remove_wikilinks(wikitext)
        wikitext = self._remove_templates(wikitext)

        return wikitext

    def _remove_wikilinks(self, wikitext):
        """
        Internal function to simplify wikilinks in wikitext
        Shortens the wikilink into its template value
        """

        wikilinks = wtp.parse(wikitext).wikilinks

        for wikilink in wikilinks:
            wikilink_str = str(wikilink)
            wikitext = wikitext.replace(wikilink_str, wikilink.text)

        return wikitext

    def _remove_templates(self, wikitext):
        """
        Internal function to simplify templates in wikitext
        Shortens the template into its value
        """

        templates = wtp.parse(wikitext).templates

        for template in templates:
            template_str = str(template)

            template_value = ""
            if Doll._WEAK_ICON_STRING not in template:
                template_value = template.arguments[Doll._VALUE_INDEX].value

            wikitext = wikitext.replace(template_str, template_value)

        return wikitext

    def _parse_skill_table(self, skill_data):
        """
        Internal function to parse the skill table
        """

        table_data = wtp.Table(skill_data).data(span=False)
        skill_table_dictionary = self._table_data_to_dict(table_data)

        parsed_skill_dictionary = {}
        variable_skill_parameters = []
        for key in skill_table_dictionary:
            if key in Doll._IGNORED_KEYS:
                continue

            value = skill_table_dictionary[key]

            match key:
                case self.SKILL_PARAMETER_STRING.NAME_STRING:
                    parsed_skill_dictionary[key] = value
                case self.SKILL_PARAMETER_STRING.TEXT_STRING:
                    skill_text = self._simplify(value)

                    parsed_skill_dictionary[key] = skill_text
                case self.SKILL_PARAMETER_STRING.EXTRA_EFFECT_STRING:
                    extra_effects = skill_table_dictionary[key]

                    extra_effects_array = []
                    for extra_effect in extra_effects:
                        if extra_effect == "":
                            continue

                        cleaned_extra_effect = self._simplify(extra_effect)
                        extra_effects_array.append(cleaned_extra_effect)

                    parsed_skill_dictionary[key] = extra_effects_array
                case _:
                    # We found some variables, save them so we can replace it later
                    variable_skill_parameters.append(key)

        # Remove the extraeffects variable from skill text
        skill_text = parsed_skill_dictionary[self.SKILL_PARAMETER_STRING.TEXT_STRING]

        extraeffects_string = f"(${self.SKILL_PARAMETER_STRING.EXTRA_EFFECT_STRING})"
        skill_text = skill_text.replace(extraeffects_string, "")

        # Replace the variable skill parameter
        for parameter in variable_skill_parameters:
            parameter_string = f"(${parameter})"

            parameter_array = skill_table_dictionary[parameter]
            parameter_value = ""

            for value in parameter_array:
                value = self._simplify(value)
                parameter_value += f"{value}/"

            parameter_value = parameter_value[:-1]

            skill_text = skill_text.replace(parameter_string, parameter_value)

        parsed_skill_dictionary[self.SKILL_PARAMETER_STRING.TEXT_STRING] = skill_text

        skill = Skill(
            name=parsed_skill_dictionary[self.SKILL_PARAMETER_STRING.NAME_STRING],
            desc=parsed_skill_dictionary[self.SKILL_PARAMETER_STRING.TEXT_STRING],
            extra_effects=parsed_skill_dictionary.get(
                self.SKILL_PARAMETER_STRING.EXTRA_EFFECT_STRING, None
            ),
        )

        return skill

    def _get_base_template(self, wikitext):
        """
        Internal function to get the base template of a wikitext
        """

        return wtp.parse(wikitext).templates[Doll._BASE_TEMPLATE_INDEX]

    def _get_template_param_value(self, template, param_name):
        """
        Internal function to get the value of a parameter
        """

        return template.get_arg(param_name).value
