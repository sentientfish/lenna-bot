"""
Doll class

Takes a wikitext and parses it into information of interest
This includes:
- fullName          -> renamed to full_name
- role
- rarity
- affiliation
- favweapon         -> renamed to weapon_name
- imprint           -> renamed to signature_weapon
- wepweakness       -> renamed to weapon_weakness
- phaseweakness     -> renamed to phase_weakness
- GFL               -> renamed to gfl_name
- Node*             -> collected into a list named nodes
- skills            -> TODO: do it
"""

import wikitextparser as wtp

class Doll:
    """
    Doll class definition
    """

    class Node:
        """
        Internal node class representation
        """

        def __init__(self, name, desc, position):
            self.name = name
            self.desc = desc
            self.position = position
        
        def __str__(self):
            return f"name: {self.name}, desc: {self.desc}, position: {self.position}"
        

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
        """
        Internal function to get node from wikitext template
        """

        name = None
        if is_key:
            name_string = f"Node{node_position}name"
            if key_position != 0:
                name_string += f"{key_position}"
            name_wikitext = self._get_template_param_value(template, name_string)

            name_template = self._get_base_template(name_wikitext)
            name = name_template.arguments[1].value
        
        desc_string = f"Node{node_position}desc"
        if key_position != 0:
            desc_string += f"{key_position}"
        
        desc = self._get_template_param_value(template, desc_string)
        node = self.Node(name, desc, node_position)

        return node


    def _get_nodes(self, template):
        """
        Internal function to get all doll nodes
        """

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
        """
        Internal function to get the base template of a wikitext
        """

        return wtp.parse(wikitext).templates[0]


    def _get_template_param_value(self, template, param_name):
        """
        Internal function to get the value of a parameter 
        """
        
        return template.get_arg(param_name).value
