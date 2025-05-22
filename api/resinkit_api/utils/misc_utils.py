from datetime import UTC, datetime
from random import randint
from typing import Any, Dict
from string import Template

from shortuuid import ShortUUID


def render_with_string_template(configs_template: dict, variables: dict) -> Dict[str, Any]:
    """
        Recursively traverse configs_template and replace string values containing variable
        templates with values from the variables dictionary using string.Template substitution.

    ,    Variables can be referenced as $variable or ${variable} in string values.
    """

    def render_recursive(obj):
        if isinstance(obj, dict):
            return {key: render_recursive(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [render_recursive(item) for item in obj]
        elif isinstance(obj, str):
            try:
                template = Template(obj)
                return template.substitute(variables)
            except (KeyError, ValueError):
                return obj
        else:
            return obj

    return render_recursive(configs_template)


def get_system_variables() -> Dict[str, str]:
    """
    Get system variables.
    """
    return {
        "__NOW_TS10__": str(int(datetime.now(UTC).timestamp() * 1000)),
        "__RANDOM_16BIT__": str(randint(0, 32767)),
        "__SUUID_9__": ShortUUID().random(length=9),
    }
