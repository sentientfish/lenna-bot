"""
Internal library to help with common parsing functions
"""

import json
import wikitextparser as wtp

# Template parsing variables
BASE_TEMPLATE_INDEX = 0

# API Payload parsing variables
PARSE_STRING = "parse"
WIKITEXT_STRING = "wikitext"
STAR_STRING = "*"
DATA_STRING = "data"
WEAK_ICON_STRING = "GFL2WeakIcon"
VALUE_INDEX = 1

# Table parsing variables
KEY_INDEX = 0
FIRST_VALUE_INDEX = 1
SIMPLE_DATA_LIST_LENGTH = 2


def get_wikitext(json_obj):
    """
    Internal function to get wikitext from wikimedia api response
    because it's annoying as hell
    """

    return json_obj[PARSE_STRING][WIKITEXT_STRING][STAR_STRING]


def get_base_template(wikitext):
    """
    Internal function to get the base template of a wikitext
    """

    return wtp.parse(wikitext).templates[BASE_TEMPLATE_INDEX]


def get_template_param_value(template, param_name):
    """
    Internal function to get the value of a parameter
    """

    return template.get_arg(param_name).value


def remove_wikilinks(wikitext):
    """
    Internal function to simplify wikilinks in wikitext
    Shortens the wikilink into its template value
    """

    wikilinks = wtp.parse(wikitext).wikilinks

    for wikilink in wikilinks:
        if wikilink.text == None:
            continue

        wikilink_str = str(wikilink)
        wikitext = wikitext.replace(wikilink_str, wikilink.text)

    return wikitext


def remove_templates(wikitext):
    """
    Internal function to simplify templates in wikitext
    Shortens the template into its value
    """

    templates = wtp.parse(wikitext).templates

    for template in templates:
        template_str = str(template)

        template_value = ""
        if WEAK_ICON_STRING not in template:
            template_value = template.arguments[VALUE_INDEX].value

        wikitext = wikitext.replace(template_str, template_value)

    return wikitext


def simplify(wikitext):
    """
    Internal function to simply the wikitext and remove all templates
    and wikilinks
    """

    wikitext = remove_wikilinks(wikitext)
    wikitext = remove_templates(wikitext)

    return wikitext


def table_data_to_dict(table_data):
    """
    Internal function to convert wikitable data into a dictionary
    """

    table_dictionary = {}
    for data in table_data:
        key = data[KEY_INDEX]
        data_list_length = len(data)

        value = ""
        if data_list_length > SIMPLE_DATA_LIST_LENGTH:
            value = []

            for i in range(FIRST_VALUE_INDEX, data_list_length):
                data_val = data[i]
                value.append(data_val)
        else:
            value = data[FIRST_VALUE_INDEX]

        table_dictionary[key] = value

    return table_dictionary
