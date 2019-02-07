"""
This is the entry point for the 249 converter. Before you start poking around
make sure you read the available documentation! Don't assume anything!
"""
import collections
import copy
import enum
import os
import re
import sys
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import bpy

from io_xplane2blender import xplane_constants, xplane_helpers
from io_xplane2blender.tests import test_creation_helpers
from io_xplane2blender.xplane_249_converter import (xplane_249_constants,
                                                    xplane_249_dataref_decoder,
                                                    xplane_249_manip_decoder,
                                                    xplane_249_workflow_converter)

PropDataType = Union[bool, float, int, str]
def find_property_in_hierarchy(obj: bpy.types.Object,
                               prop_name: str,
                               *,
                               ignore_case: bool=True,
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
            filter_fn = lambda prop: prop_name.casefold() == prop.name.casefold() and prop.type in prop_types
        else:
            filter_fn = lambda prop: prop_name == prop.name and prop.type in prop_types

        val = next(filter(filter_fn, obj.game.properties)).value
        #print("Found {}".format(val))
        return val, obj
    except StopIteration:
        if obj.parent and (max_parents is None or max_parents > 0):
            return find_property_in_hierarchy(obj.parent,
                                              prop_name,
                                              prop_types=prop_types,
                                              max_parents=max_parents - 1 if max_parents else None,
                                              default=default)
        else:
            #print("Not found, using {}".format(default))
            return default, None

_runs = 0
def do_249_conversion(context: bpy.types.Context, workflow_type: xplane_249_constants.WorkflowType):
    # TODO: Create log, similar to updater log

    #TODO: When we integrate with the updater, (adding 2.49 as a legacy version)
    # We can use that. Until then, we have this hack to keep unit testing going
    # Also, we should put it in the operator call instead so we can force it
    # rather than in the API itself
    global _runs
    if _runs > 0:
        return
    _runs += 1

    for scene in bpy.data.scenes:
        # Global settings
        scene.xplane.debug = True

        new_roots = xplane_249_workflow_converter.convert_workflow(scene, workflow_type)

        # Make the default material for new objects to be assaigned
        for armature in filter(lambda obj: obj.type == "ARMATURE", bpy.data.objects):
            xplane_249_dataref_decoder.convert_armature_animations(scene, armature)

        for obj in filter(lambda obj: obj.type == "MESH", bpy.data.objects):
            xplane_249_manip_decoder.convert_manipulators(scene, obj)

        is_additive = workflow_type == xplane_249_constants.WorkflowType.BULK

        #Keep checking from here
        #TODO: What about checking for LODs in regular mode?
        for obj in filter(lambda obj: "" in obj.name, new_roots):
            obj.xplane.layer.lods = "3"
            #print("\n---------------------")
            #print("Name: ", obj.name)
            lod_props_249 = collections.OrderedDict({0: 0, 1: 1000, 2: 4000, 3: 10000})
            defined_lod_props_249 = {
                i: find_property_in_hierarchy(obj, "LOD_{}".format(i))[0]
                for i in range(4)
                if find_property_in_hierarchy(obj, "LOD_{}".format(i))[0]
            }

            #print("Hand definied props: %d" % len(defined_lod_props_249))
            lod_props_249.update(defined_lod_props_249)
            #print("lod_props_249.values", lod_props_249.values())
            value, has_prop_obj = find_property_in_hierarchy(obj, "additive_lod")
            if value is not None:
                is_additive = bool(value)

            if value:
                has_prop_obj.xplane.layer.export_type = xplane_constants.EXPORT_TYPE_INSTANCED_SCENERY
                """
                # double check there isn't also some instanced going on
                value, has_prop_obj = find_property_in_hierarchy(obj, "instanced")
                if value is not None and not bool(value):
                    has_prop_obj.xplane.layer.export_type = xplane_constants.EXPORT_TYPE_SCENERY #I guess? Idk, what is a good default here
                """

            #print("Is additive {}".format(is_additive))
            if is_additive:
                for i, breakpoint in enumerate(list(lod_props_249.values())[1:]):
                    l = obj.xplane.layer.lod[i]
                    l.near, l.far = 0, int(breakpoint)
            else:
                for i, (near, far) in enumerate(zip(list(lod_props_249.values())[:-1], list(lod_props_249.values())[1:])):
                    l = obj.xplane.layer.lod[i]
                    l.near, l.far = int(near), int(far)
            #print("Final:", [(l.near, l.far) for l in obj.xplane.layer.lod])

