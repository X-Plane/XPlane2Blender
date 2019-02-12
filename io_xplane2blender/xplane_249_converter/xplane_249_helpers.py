"""
Contains functions relating to traversing the heirarchy to search for
game properties, and others
"""

from typing import Any, Dict, List, Optional, Set, Tuple, Union
import bpy


def get_all_children_recursive(obj: bpy.types.Object)->List[bpy.types.Object]:
    """
    Recurse down the tree of parent-child relations and gather all the
    possible objects under obj in a list, as reported by obj.children.

    An empty list is returned when obj has no list
    """
    if not obj.children:
        return []
    else:
        children = []
        for child in obj.children:
            sub_children = get_all_children_recursive(child)
            if sub_children:
                children.append(sub_children)
        return children + list(obj.children)


PropDataType = Union[bool, float, int, str]
def find_property_in_parents(obj: bpy.types.Object,
                             prop_name: str,
                             *,
                             ignore_case: bool = True,
                             prop_types: Set[str] = {"BOOL", "FLOAT", "INT", "STRING", "TIMER"},
                             max_parents: Optional[int] = None,
                             default: Optional[PropDataType] = None)\
                             ->Tuple[Optional[PropDataType], Optional[bpy.types.Object]]:
    """
    Searches from obj up for a property and the object that has it,
    returns the value and the object it was found on or (default value, None)
    """
    assert prop_types <= {"BOOL", "FLOAT", "INT", "STRING", "TIMER"}, \
            "Target prop_types {} is not a recognized property type"
    """
    print(
        ("Searching for '{}' starting at {}, with {} and " + ["an unlimited amount of", "a maximum of {}"][bool(max_parents)] + " parents").format(
            prop_name,
            obj.name,
            prop_types if len(prop_types) < 5 else "all types",
            max_parents
        )
    )
    print("searching for '{}' starting at {}".format(
            prop_name,
            obj.name
        )
    )
    """

    try:
        if ignore_case:
            filter_fn = lambda prop: (prop_name.casefold() == prop.name.casefold()
                                      and prop.type in prop_types)
        else:
            filter_fn = lambda prop: prop_name == prop.name and prop.type in prop_types

        val = next(filter(filter_fn, obj.game.properties)).value
        #print("Found {}".format(val))
        return val, obj
    except StopIteration:
        if obj.parent and (max_parents is None or max_parents > 0):
            return find_property_in_parents(obj.parent,
                                            prop_name,
                                            prop_types=prop_types,
                                            max_parents=max_parents - 1 if max_parents else None,
                                            default=default)
        else:
            #print("Not found, using {}".format(default))
            return default, None
