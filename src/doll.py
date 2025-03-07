"""
Doll class definition
"""

import mwparserfromhell

class Doll:
    class Node:
        def __init__(self, name, desc, position):
            self.name = name
            self.desc = desc
            self.position = position
        

    def __init__(self, doll_wikitext):
        template = self._get_base_template(doll_wikitext)

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


    def _get_node(self, template, node_position, is_key=False, key_position=0):
        name = None
        if is_key:
            name_string = f"Node{node_position}name"
            if key_position != 0:
                name_string += f"{key_position}"
            name_wikitext = self._get_template_param_value(template, name_string)

            name_template = self._get_base_template(name_wikitext)
            name = self._get_base_template(name_template).params[1]
        
        desc_string = f"Node{node_position}desc"
        if key_position != 0:
            desc_string += f"{key_position}"
        
        desc = self._get_template_param_value(template, desc_string)
        node = self.Node(name, desc, node_position)

        return node


    def _get_nodes(self, template):
        nodes = [
            self._get_node(template, 1),
            self._get_node(template, 2),
            self._get_node(template, 3),
            self._get_node(template, 4, is_key=True, key_position=1),
            self._get_node(template, 4, is_key=True, key_position=2),
            self._get_node(template, 5),
            self._get_node(template, 6),
            self._get_node(template, 7, is_key=True, key_position=1),
            self._get_node(template, 7, is_key=True, key_position=2),
            self._get_node(template, 8),
            self._get_node(template, 9),
            self._get_node(template, 10, is_key=True, key_position=1),
            self._get_node(template, 10, is_key=True, key_position=2),
            self._get_node(template, 11, is_key=True),
        ]

        return nodes


    def _get_base_template(self, wikitext):
        return mwparserfromhell.parse(wikitext).filter_templates()[0]


    def _get_template_param_value(self, template, param_name):
        return template.get(param_name).value