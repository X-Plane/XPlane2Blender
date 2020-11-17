import collections
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import bpy
import idprop

# This is basically a copy of EnumPropertyItem, with only the parts we care about
_EnumItem = collections.namedtuple("EnumItem", ["identifier", "name", "description"])


def _get_enum_item(
    prop_group: bpy.types.PropertyGroup, prop: bpy.types.Property
) -> _EnumItem:
    """
    Inspects a property group's enum property and return's
    throws KeyNotFound and typeError

    prop.type must be and ENUM found in prop_group
    """
    assert (
        prop.identifier in prop_group.bl_rna.properties
    ), f"{prop.identifier} is not a member of {prop_group.rna_type.name}'s properties"
    assert (
        prop.type == "ENUM"
    ), f"{prop.identifier} is not an ENUM and cannot be used in this function"
    # We need get instead of getattr because only get
    # gives us the real unfiltered value including
    # "never changed" aka None
    prop_value: Optional[int] = prop_group.get(prop.identifier)
    if prop_value is None:
        enum_key: str = prop.default
    else:
        enum_key: str = prop.enum_items.keys()[prop_value]
    item: bpy.types.EnumPropertyItem = prop.enum_items[enum_key]
    return _EnumItem(item.identifier, item.name, item.description)


def check_property_group_has_non_default(
    prop_group: bpy.types.PropertyGroup, props_to_ignore={"index", "expanded"}
) -> Dict[str, Union[bool, float, int, str]]:
    """
    Recursively searches a property group for any members of it that have different values than the default.
    Returns a dictionary of property names to values. Currently does not inspect PointerPropertys
    """

    def check_recursive(real_prop_group: bpy.types.PropertyGroup):
        nondefault_props = {}
        for prop in filter(
            lambda p: p.identifier not in (props_to_ignore | {"rna_type"}),
            real_prop_group.bl_rna.properties,
        ):
            if prop.type == "POINTER":
                # TODO: This can be followed, but for now we need to press on to other bugs
                # and we don't have a test case that uses this
                # check_recursive(prop_group)
                continue
            elif prop.type == "COLLECTION":
                nondefaults = list(
                    filter(
                        None,
                        [
                            check_recursive(m)
                            for m in getattr(real_prop_group, prop.identifier)
                        ],
                    )
                )
                if nondefaults:
                    nondefault_props[prop.identifier] = nondefaults
            else:
                if prop.type == "ENUM":
                    # This is the enum's identifier, what getattr and get when unchanged
                    # or missing
                    real_value = _get_enum_item(real_prop_group, prop).identifier
                else:
                    real_value = real_prop_group.get(prop.identifier, prop.default)
                if real_value != prop.default:
                    nondefault_props[prop.identifier] = real_value
        return nondefault_props

    return check_recursive(prop_group)


def copy_property_group(
    source_prop_group: bpy.types.PropertyGroup,
    dest_prop_group: bpy.types.PropertyGroup,
    props_to_ignore: Set[str] = None,
) -> None:
    """
    Recursively copies values from one PropertyGroup to another, using setattr.

    Note:
    If your PropertyGroup has a "name" property with a non-empty str default, you must copy those
    yourself.

    To iterate, we use bl_rna.properties, whose "name" member actually refers to the partent type
    (bpy.types.PropertyGroup)'s "name" property which is

        (identifier="name",
         name="Name",
         description="Unique name used in the code and scripting",
         default="")

    If your "name" property's default matches the parent's "name", then everything lines up by co-incidence.
    There does not appear to be a way to get around this.

    bl_rna.properties["rna_type"] is always ignored since that is Blender defined.
    """

    props_to_ignore = props_to_ignore if props_to_ignore else set()

    def copy_recursive(
        source_prop_group: bpy.types.PropertyGroup,
        dest_prop_group: bpy.types.PropertyGroup,
    ):
        assert source_prop_group.rna_type == dest_prop_group.rna_type
        for prop in filter(
            lambda p: p.identifier not in (props_to_ignore | {"rna_type"}),
            source_prop_group.bl_rna.properties,
        ):
            if prop.type == "POINTER":
                # TODO: When we have a case with an POINTER to worry about
                # we'll fill this in
                continue
            elif prop.type == "COLLECTION":
                source_members = getattr(source_prop_group, prop.identifier)
                dest_members = getattr(dest_prop_group, prop.identifier)
                while len(dest_members) < len(source_members):
                    dest_members.add()

                for source_member, dest_member in zip(source_members, dest_members):
                    copy_recursive(source_member, dest_member)
            else:
                source_value = source_prop_group.get(prop.identifier, prop.default)
                if prop.type == "ENUM":
                    setattr(
                        dest_prop_group,
                        prop.identifier,
                        _get_enum_item(source_prop_group, prop).identifier,
                    )
                else:
                    setattr(dest_prop_group, prop.identifier, source_value)

    copy_recursive(source_prop_group, dest_prop_group)


def copy_former_property_group_to_property_group(
    from_idprop_todict: Dict[str, Any], dest_prop_group
):
    """
    For recursively copying a deleted PropertyGroup, now an idprop_group, use this.
    Data comes in from a call to idprop_group.to_dict()
    """
    # TODO: Implement this and delete scene.xplane.layers
    ...


def delete_property_from_datablock(
    idprop_group: idprop.types.IDPropertyGroup, prop: str
) -> Optional[Union[bool, int, float, str]]:
    """
    Attempts to delete an idprop from a datablock.
    If round, return the value as reported by __getitem__,
    else return None
    """
    try:
        # TODO: Or would getattr() or get be better?
        value = idprop_group[prop]
        del idprop_group[prop]
    except KeyError:
        return None
    else:
        return value


def delete_property_from_blend_file(idprop_groups: List[Any], prop: str) -> None:
    """
    Completely cleans away a property from the .blend file, leaving no trace
    Assumes each member of bpy_types has an xplane pointer property

    thing is the thing that has the property group hanging off it
    """
    # TODO: Not sure what I want out of this API. Something where
    # Scene and "xplane.exportMode" are passed in, and all of
    # "exportMode" is deleted?
    # Better communication than lots of for loops?
    # for idprop_group in idprop_groups:
    # delete_property_from_datablock(idprop_group, prop)
    ...


def reorder_enum_prop(
    datablock,
    prop: str,
    conversion_table: List[Tuple[int, int]],
    previous_default_value: int,
) -> None:
    """
    Re-orders an enum based on a conversion table, where each row of the table is the before->after index.
    Uses get, and, if no value was set, uses the previous_default_value now that getattr would return the incorrect result
    """
    ...


def rename_prop(
    datablock, prop_old: str, prop_new_name: str, delete_old_prop: bool = True
) -> None:
    """
    Copies the value from prop_old to prop_new, with the option to delete the old property right away.
    Works with properties that are read ID properties or old ID properties
    """
    ...
