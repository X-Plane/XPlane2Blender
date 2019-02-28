"""
Converts (some) 249 global properties whose destination is an XPlaneLayer
on a new root object. For instance, LODs, Slope Limits, Layer Groups, etc
"""
import collections
import math
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import bpy

from io_xplane2blender import xplane_constants
from io_xplane2blender.xplane_249_converter import (xplane_249_constants,
                                                    xplane_249_helpers)


def _convert_global_properties(search_objs: List[bpy.types.Object],
                               workflow_type: xplane_249_constants.WorkflowType,
                               dest_root: bpy.types.Object)->None:
    assert search_objs, "Must have objects to search"

    layer = dest_root.xplane.layer
    for obj in search_objs:
        cockpit_reg_value, _ = xplane_249_helpers.find_property_in_parents(obj, "COCKPIT_REGION")
        if cockpit_reg_value is not None:
            layer.export_type = xplane_constants.EXPORT_TYPE_COCKPIT
            layer.cockpit_regions = "1"
            if isinstance(cockpit_reg_value, str):
                if cockpit_reg_value == "":
                    pass
                elif (len(cockpit_reg_value.split()) == 4
                      and [v.isnumeric() for v in cockpit_reg_value.split()]):
                    reg = layer.cockpit_region[0]
                    reg.left, reg.top, reg.width, reg.height = [math.log2(int(v)) if int(v) else 0 for v in cockpit_reg_value.split()]
            else:
                print("NEXT-STEP: Set Cockpit Region value for {}."
                      "'{}' couldn't be parsed to 4 integers."
                      .format(dest_root.name,cockpit_reg_value))

        #---------------------------------------------------------------------
        # Scenery Only Properties, change if hasn't already been set to the
        # more specific INSTANCED instead
        #---------------------------------------------------------------------
        slope_limit_value, _ = xplane_249_helpers.find_property_in_parents(obj, "SLOPE_LIMIT", prop_types={"STRING"})
        if slope_limit_value is not None:
            layer.slope_limit = True
            try:
                if any([not -90 <= float(v) <= 90 for v in slope_limit_value.split()]):
                    print("WARN: SLOPE_LIMIT must have 4 floats between -90 and 90 inclusive seperated by space for a value")
                    print("NEXT-STEP: Change your slope limits")
            except ValueError:
                print("WARN: SLOPE_LIMIT must have 4 floats between -90 and 90 inclusive seperated by space for a value")
            else:
                layer.slope_limit_min_pitch, \
                layer.slope_limit_max_pitch, \
                layer.slope_limit_min_roll, \
                layer.slope_limit_max_roll = [float(v) for v in slope_limit_value.split()]


        tilted_value, _ = xplane_249_helpers.find_property_in_parents(obj, "TILTED")
        if tilted_value is not None:
            layer.tilted = True

        layer_group_value, _ = xplane_249_helpers.find_property_in_parents(obj, "ATTR_layer_group", prop_types={"STRING"})
        if layer_group_value is not None:
            try:
                layer_group_type, layer_group_offset = layer_group_value.split()
                layer.layer_group = layer_group_type
            except ValueError: #split has too many or two few values to unpack (expected 2)
                print("WARN: '{}' isn't in the right format".format(layer_group_value))
            else:
                try:
                    if -5 <= int(layer_group_offset) <= 5:
                        layer_group_offset = int(layer_group_offset)
                        layer.layer_group_offset = layer_group_offset
                    else:
                        print("WARN: ATTR_layer_group offset '{}' must be between -5 and 5 inclusive".format(layer_group_offset))
                        break
                except ValueError:
                    print("WARN: ATTR_layer_group \"{}\"'s offset must be a number".format(layer_group_value))

        dry_value, has_prop_obj = xplane_249_helpers.find_property_in_parents(obj, "REQUIRE_DRY", prop_types={"STRING"})
        if dry_value == "":
            layer.require_surface = xplane_constants.REQUIRE_SURFACE_DRY

        wet_value, has_prop_obj = xplane_249_helpers.find_property_in_parents(obj, "REQUIRE_WET", prop_types={"STRING"})
        if wet_value == "":
            layer.require_surface = xplane_constants.REQUIRE_SURFACE_WET

        #---------------------------------------------------------------------
        # Draped Scenery Only Properties, export type hint: Instanced
        #---------------------------------------------------------------------
        LOD_draped_value, _ = xplane_249_helpers.find_property_in_parents(obj, "ATTR_LOD_draped")
        if LOD_draped_value is not None:
            try:
                if float(LOD_draped_value) >= 0.0:
                    layer.lod_draped = float(LOD_draped_value) #TODO: This seems wrong, shouldn't this be an int?
                else:
                    print("WARN: Value for ATTR_LOD_draped must be >= 0, is '{}'".format(LOD_draped_value))
            except TypeError: #LOD_draped_value is None
                print("WARN: Value for ATTR_LOD_draped must be convertable to an float, is '{}'".format(LOD_draped_value))
            except ValueError: #LOD_draped_value is not convertable to a float
                print("WARN: Value for ATTR_LOD_draped must be convertable to an float, is '{}'".format(LOD_draped_value))

        layer_group_draped_value, _ = xplane_249_helpers.find_property_in_parents(obj, "ATTR_layer_group_draped", prop_types={"STRING"})
        if layer_group_draped_value is not None:
            try:
                layer_group_draped_type, layer_group_draped_offset = layer_group_draped_value.split()
                #print(layer_group_draped_type, layer_group_draped_offset)
            except ValueError: # Too many or too few to unpack
                print("WARN: '{}' is not in the right format, must be <group type> <offset>".format(layer_group_draped_value))
            else:
                if layer_group_draped_type in xplane_constants.LAYER_GROUPS_ALL:
                    layer.layer_group_draped = layer_group_draped_type
                    try:
                        if -5 <= int(layer_group_draped_offset) <= 5:
                            layer.layer_group_draped_offset = int(layer_group_draped_offset)
                        else:
                            print("WARN: Layer Group Draped Offset must be between and including -5 and 5, is '{}'".format(layer_group_draped_offset))
                    except TypeError:
                        print("WARN: Layer Group Draped Offset must be convertable to an int, is '{}'".format(layer_group_draped_offset))
                    except ValueError:
                        print("WARN: Layer Group Draped Offset must be convertable to an int, is '{}'".format(layer_group_draped_offset))
                else:
                    print("WARN: '{}' is not a known Layer Group".format(layer_group_draped_type))


        # Apply export type hints, from least specific to most specific
        if any([p is not None for p in [slope_limit_value, tilted_value, layer_group_value, dry_value, wet_value]]):
            layer.export_type = xplane_constants.EXPORT_TYPE_SCENERY

        if any([p is not None for p in [LOD_draped_value, layer_group_draped_value]]):
            layer.export_type = xplane_constants.EXPORT_TYPE_INSTANCED_SCENERY


def _convert_lod_properties(search_objs: List[bpy.types.Object],
                            workflow_type: xplane_249_constants.WorkflowType,
                            dest_root: bpy.types.Object)->None:
    """
    Searches objs for "LOD_[0123]" properties to apply to dest_root's layer.lod
    member
    """
    assert search_objs, "Must have objects to search"

    dest_root.xplane.layer.lods = "3"
    for obj in search_objs:
        value, has_prop_obj = xplane_249_helpers.find_property_in_parents(obj, "additive_lod")
        if value is not None:
            is_additive = bool(value)
            break
        """
        # TODO: double check there isn't also some instanced going on
        value, has_prop_obj = find_property_in_hierarchy(obj, "instanced")
        if value is not None and not bool(value):
            dest_root.xplane.layer.export_type = xplane_constants.EXPORT_TYPE_SCENERY #I guess? Idk, what is a good default here
        """
    else: #nobreak
        is_additive = workflow_type == xplane_249_constants.WorkflowType.BULK

    if is_additive:
        dest_root.xplane.layer.export_type = xplane_constants.EXPORT_TYPE_INSTANCED_SCENERY

    lod_props_249 = collections.OrderedDict({0: 0, 1: 1000, 2: 4000, 3: 10000})
    for obj in search_objs:
        defined_lod_props_249 = {
            i: xplane_249_helpers.find_property_in_parents(obj, "LOD_{}".format(i))[0]
            for i in range(4)
            if xplane_249_helpers.find_property_in_parents(obj, "LOD_{}".format(i))[0]
        }

        lod_props_249.update(defined_lod_props_249)

    if is_additive:
        for i, breakpoint in enumerate(list(lod_props_249.values())[1:]):
            l = dest_root.xplane.layer.lod[i]
            l.near, l.far = 0, int(breakpoint)
    else:
        for i, (near, far) in enumerate(zip(list(lod_props_249.values())[:-1], list(lod_props_249.values())[1:])):
            l = dest_root.xplane.layer.lod[i]
            l.near, l.far = int(near), int(far)


def do_convert_layer_properties(scene: bpy.types.Scene, workflow_type, root_objects: List[bpy.types.Object]):
    assert workflow_type != xplane_249_constants.WorkflowType.SKIP

    for root_object in root_objects:
        print("Converting XPlaneLayer related properties for '{}'".format(root_object.name))
        if workflow_type == xplane_249_constants.WorkflowType.REGULAR:
            search_objs = scene.objects
        elif workflow_type == xplane_249_constants.WorkflowType.BULK:
            search_objs = [root_object] + xplane_249_helpers.get_all_children_recursive(root_object, scene)
        else:
            assert False, "Unknown workflow type"

        if search_objs:
            # Hints towards Instanced Scenery Export
            _convert_lod_properties(search_objs, workflow_type, root_object)

            # Hints towards Cockpit
            _convert_global_properties(search_objs, workflow_type, root_object)
