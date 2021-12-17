from __future__ import annotations

import inflection


def _key_as_underscore(target: dict) -> dict:
    """
    `key_as_underscore` impl.

    @param target:
    @return:
    """
    return {inflection.underscore(k): v for k, v in target.items()}


def key_as_underscore(target) -> dict | list:
    """
    Converts the key of dictionary that written as camel case to snake case.

    @param target:
    @return: Converted value.
    """
    if type(target) == dict:
        return _key_as_underscore(target)
    elif type(target) == list:
        return [_key_as_underscore(item) for item in target]


def extend_dict_by_match_key(target: dict, *dicts) -> None:
    """
    Append value from `dicts` to `target` that match key.

    @param target:
    @param dicts:
    """
    for k in target.keys():
        for d in dicts:
            target[k].update(d.get(k))
