"""
Converts (some) 249 global properties whose destination is an XPlaneLayer
on a new root object. For instance, LODs, Slope Limits, Layer Groups, etc
"""
import collections
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import bpy

from io_xplane2blender import xplane_constants
from io_xplane2blender.xplane_249_converter import (xplane_249_constants,
                                                    xplane_249_helpers)


def _convert_lod_properties(search_objs: List[bpy.types.Object],
                             workflow_type: xplane_249_constants.WorkflowType,
                             dest_root: bpy.types.Object)->None:
    """
    Searches objs for "LOD_[0123]" properties to apply to dest_root's layer.lod
    member
    """
    if not search_objs:
        return

    is_additive = workflow_type == xplane_249_constants.WorkflowType.BULK
    dest_root.xplane.layer.lods = "3"
    lod_props_249 = collections.OrderedDict({0: 0, 1: 1000, 2: 4000, 3: 10000})
    for obj in search_objs:
        #print("\n---------------------")
        #print("Name: ", obj.name)
        defined_lod_props_249 = {
            i: xplane_249_helpers.find_property_in_parents(obj, "LOD_{}".format(i))[0]
            for i in range(4)
            if xplane_249_helpers.find_property_in_parents(obj, "LOD_{}".format(i))[0]
        }

        #print("Hand definied props: %d" % len(defined_lod_props_249))
        lod_props_249.update(defined_lod_props_249)
        #print("lod_props_249.values", lod_props_249.values())
        value, has_prop_obj = xplane_249_helpers.find_property_in_parents(obj, "additive_lod")
        if value is not None:
            is_additive = bool(value)

        if value:
            dest_root.xplane.layer.export_type = xplane_constants.EXPORT_TYPE_INSTANCED_SCENERY
            """
            # double check there isn't also some instanced going on
            value, has_prop_obj = find_property_in_hierarchy(obj, "instanced")
            if value is not None and not bool(value):
                dest_root.xplane.layer.export_type = xplane_constants.EXPORT_TYPE_SCENERY #I guess? Idk, what is a good default here
            """

    #print("Is additive {}".format(is_additive))
    if is_additive:
        for i, breakpoint in enumerate(list(lod_props_249.values())[1:]):
            l = dest_root.xplane.layer.lod[i]
            l.near, l.far = 0, int(breakpoint)
    else:
        for i, (near, far) in enumerate(zip(list(lod_props_249.values())[:-1], list(lod_props_249.values())[1:])):
            l = dest_root.xplane.layer.lod[i]
            l.near, l.far = int(near), int(far)
    #print("Final:", [(l.near, l.far) for l in dest_root.xplane.layer.lod])


def do_convert_layer_properties(scene: bpy.types.Scene, workflow_type, root_objects: List[bpy.types.Object]):
    assert workflow_type != xplane_249_constants.WorkflowType.SKIP

    for root_object in root_objects:
        if workflow_type == xplane_249_constants.WorkflowType.REGULAR:
            search_objs = scene.objects
        elif workflow_type == xplane_249_constants.WorkflowType.BULK:
            search_objs = xplane_249_helpers.get_all_children_recursive(root_object)
        else:
            assert False, "Unknown workflow type"

        _convert_lod_properties(search_objs, workflow_type, root_object)

