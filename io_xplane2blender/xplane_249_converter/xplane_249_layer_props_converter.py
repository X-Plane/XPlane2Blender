"""
Converts (some) 249 global properties whose destination is an XPlaneLayer
on a new root object. For instance, LODs, Slope Limits, Layer Groups, etc
"""
import collections
import math
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import bpy

from io_xplane2blender import xplane_constants, xplane_helpers
from io_xplane2blender.xplane_helpers import logger
from io_xplane2blender.xplane_249_converter import (xplane_249_constants,
                                                    xplane_249_helpers)


def _convert_global_properties(search_objs: List[bpy.types.Object],
                               workflow_type: xplane_249_constants.WorkflowType,
                               dest_root: bpy.types.Object)->None:
    assert search_objs, "Must have objects to search"

    # We do a lot of "is it convertable to" testing...
    def _isint(s:Any)->bool:
        try:
            int(s)
            return True
        except (TypeError, ValueError):
            return False

    def _isfloat(s:Any)->bool:
        try:
            float(s)
            return True
        except (TypeError, ValueError):
            return False

    logger.info("", "raw")
    logger.info("Converting Any Global OBJ Properties for Root Object '{}'\n"
                "--------------------------------------------------".format(dest_root.name))
    info = set()
    warnings = set()
    layer = dest_root.xplane.layer
    for obj in search_objs:
        cockpit_reg_value, prop_source = xplane_249_helpers.find_property_in_parents(obj, "COCKPIT_REGION")
        if cockpit_reg_value is not None:
            layer.export_type = xplane_constants.EXPORT_TYPE_COCKPIT
            layer.cockpit_regions = "1"
            if isinstance(cockpit_reg_value, str):
                if cockpit_reg_value == "":
                    pass
                elif (len(cockpit_reg_value.split()) == 4
                      and [v.isdigit() for v in cockpit_reg_value.split()]):
                    reg = layer.cockpit_region[0]
                    reg.left, reg.top, reg.width, reg.height = [math.log2(int(v)) if int(v) else 0 for v in cockpit_reg_value.split()]
                else:
                    warnings.add("COCKPIT_REGION value '{}' on {} couldn't be parsed into 4 integers\n"
                                 "NEXT STEP: Set Cockpit Region manually"
                                 .format(cockpit_reg_value, prop_source.name))
            else:
                warnings.add("COCKPIT_REGION value '{}' on {} couldn't be parsed into 4 integers\n"
                             "NEXT STEP: Set Cockpit Region manually"
                             .format(cockpit_reg_value, prop_source.name))

        #---------------------------------------------------------------------
        # Scenery Only Properties, change if hasn't already been set to the
        # more specific INSTANCED instead
        #---------------------------------------------------------------------
        slope_limit_value, prop_source = xplane_249_helpers.find_property_in_parents(obj, "SLOPE_LIMIT", prop_types={"STRING"})
        if slope_limit_value is not None:
            layer.slope_limit = True
            if all([_isfloat(v) and -90 <= float(v) <= 90 for v in slope_limit_value.split()]):
                layer.slope_limit_min_pitch, \
                layer.slope_limit_max_pitch, \
                layer.slope_limit_min_roll, \
                layer.slope_limit_max_roll = [float(v) for v in slope_limit_value.split()]
            else:
                warnings.add("SLOPE_LIMIT value '{}' on {} couldn't be converted\n"
                             "NEXT STEP: Set your Slope Limits manually"
                             .format(slope_limit_value, prop_source.name))


        tilted_value, _ = xplane_249_helpers.find_property_in_parents(obj, "TILTED")
        if tilted_value is not None:
            layer.tilted = True

        layer_group_value, prop_source = xplane_249_helpers.find_property_in_parents(obj, "ATTR_layer_group", prop_types={"STRING"})
        if layer_group_value is not None:
            try:
                layer_group_type, layer_group_offset = layer_group_value.split()
                if layer_group_type.lower() in xplane_constants.LAYER_GROUPS_ALL:
                    layer.layer_group = layer_group_type.lower()
                else:
                    warnings.add("Layer Group Type '{}' on {} doesn't exist in modern XPlane2Blender\n"
                                 "NEXT STEP: Set your Layer Group manually".format(layer_group_type, prop_source.name))
            except ValueError: #split has too many or two few values to unpack (expected 2)
                warnings.add("ATTR_layer_group value '{}' on {} wasn't in the right format, must be <layer type> <offset>\n"
                             "NEXT STEP: Set your Layer Group and Layer Group Offset manually"
                             .format(layer_group_value, prop_source.name))
            else:
                if _isint(layer_group_offset) and -5 <= int(layer_group_offset) <= 5:
                    layer_group_offset = int(layer_group_offset)
                    layer.layer_group_offset = layer_group_offset
                else:
                    warnings.add("ATTR_layer_group offset on {} must be between and including -5 and 5, is '{}'\n"
                                 "NEXT STEP: Set Layer Group Offset manually"
                                 .format(prop_source.name, layer_group_offset))
                    break

        dry_value, _ = xplane_249_helpers.find_property_in_parents(obj, "REQUIRE_DRY", prop_types={"STRING"})
        if dry_value == "":
            layer.require_surface = xplane_constants.REQUIRE_SURFACE_DRY

        wet_value, _ = xplane_249_helpers.find_property_in_parents(obj, "REQUIRE_WET", prop_types={"STRING"})
        if wet_value == "":
            layer.require_surface = xplane_constants.REQUIRE_SURFACE_WET

        #---------------------------------------------------------------------
        # Draped Scenery Only Properties, export type hint: Instanced
        #---------------------------------------------------------------------
        LOD_draped_value, prop_source = xplane_249_helpers.find_property_in_parents(obj, "ATTR_LOD_draped")
        if LOD_draped_value is not None:
            if _isfloat(LOD_draped_value):
                if float(LOD_draped_value) >= 0.0:
                    layer.lod_draped = float(LOD_draped_value)
                else:
                    warnings.add("ATTR_LOD_draped's value '{}' on {} must be >= 0\n"
                                 "NEXT STEP: Set LOD Draped manually".format(LOD_draped_value, prop_source.name))
            else:
                warnings.add("ATTR_LOD_draped's value '{}' on {} is not a float\n"
                             "NEXT STEP: Set LOD Draped manually".format(LOD_draped_value, prop_source.name))

        layer_group_draped_value, prop_source = xplane_249_helpers.find_property_in_parents(obj, "ATTR_layer_group_draped", prop_types={"STRING"})
        if layer_group_draped_value is not None:
            try:
                layer_group_draped_type, layer_group_draped_offset = layer_group_draped_value.split()
                #print(layer_group_draped_type, layer_group_draped_offset)
            except ValueError: # Too many or too few to unpack
                warnings.add("ATTR_layer_group_draped's value '{}' on {} is not in the right format, must be <layer type> <offset>\n"
                             "NEXT STEP: Manually set Layer Group Draped and Layer Group Draped Offset".format(layer_group_draped_value, prop_source.name))
            else:
                if layer_group_draped_type in xplane_constants.LAYER_GROUPS_ALL:
                    layer.layer_group_draped = layer_group_draped_type
                    if _isint(layer_group_draped_offset) and -5 <= int(layer_group_draped_offset) <= 5:
                        layer.layer_group_draped_offset = int(layer_group_draped_offset)
                    else:
                        warnings.add("ATTR_layer_group offset on {} must be between and including -5 and 5, is '{}'\n"
                                     "NEXT STEP: Set Layer Group Draped's Offset manually"
                                     .format(prop_source.name, layer_group_draped_offset))
                else:
                    warnings.add("ATTR_layer_group_draped's type '{}' is not a known Layer Group\n"
                                 "NEXT STEP: Set Layer Group Draped and Layer Group Draped Offset Manually"
                                 .format(layer_group_draped_type))


        # Apply export type hints, from least specific to most specific
        if any([p is not None for p in [slope_limit_value, tilted_value, layer_group_value, dry_value, wet_value]]):
            layer.export_type = xplane_constants.EXPORT_TYPE_SCENERY

        if any([p is not None for p in [LOD_draped_value, layer_group_draped_value]]):
            layer.export_type = xplane_constants.EXPORT_TYPE_INSTANCED_SCENERY

    for warning in warnings:
        logger.warn(warning)


def _convert_lod_properties(search_objs: List[bpy.types.Object],
                            workflow_type: xplane_249_constants.WorkflowType,
                            dest_root: bpy.types.Object)->int:
    """
    Searches objs for "LOD_[0123]" properties to apply to dest_root's layer.lod
    member, returns the number of defined properties found unless the user defined the defaults
    """
    assert search_objs, "Must have objects to search"

    logger.info("", "raw")
    logger.info("Converting Any LOD Properties for Root Object '{}'\n"
                "--------------------------------------------------".format(dest_root.name))
    for obj in search_objs:
        additive_lod, has_prop_obj = xplane_249_helpers.find_property_in_parents(obj, "additive_lod")
        if additive_lod is not None:
            is_additive = bool(additive_lod)
            break
        instanced, has_prop_obj = xplane_249_helpers.find_property_in_parents(obj, "instanced", default=additive_lod)
        if instanced is not None and not bool(instanced):
            dest_root.xplane.layer.export_type = xplane_constants.EXPORT_TYPE_INSTANCED_SCENERY
    else: #nobreak
        is_additive = workflow_type == xplane_249_constants.WorkflowType.BULK

    if is_additive:
        dest_root.xplane.layer.export_type = xplane_constants.EXPORT_TYPE_INSTANCED_SCENERY

    lod_props_249 = [0, 1000, 4000, 10000]
    # In 2.49, if 2 or more layers were used, the defaults were always applied
    found_lod_props = 0

    layers_used = [False, False, False]
    warnings = set() # type: Set[str]
    for obj in search_objs:
        layers_used[0] |= obj.layers[0]
        layers_used[1] |= obj.layers[1]
        layers_used[2] |= obj.layers[2]
        for i in range(4):
            lod_prop_value, prop_source = xplane_249_helpers.find_property_in_parents(obj, "LOD_{}".format(i))
            if lod_prop_value is not None:
                try:
                    lod_props_249[i] = int(lod_prop_value)
                    found_lod_props += 1
                except (TypeError, ValueError) as e:
                    warnings.add("Property 'LOD_{}':'{}' on {} could not be converted to an int, using {} instead"
                                 .format(i, lod_prop_value, prop_source.name, lod_props_249[i]))

    if (not found_lod_props and
        not (layers_used[1] and layers_used[2])):
        #print("Found no LOD properties for {}".format(dest_root.name))
        for warning in warnings:
            logger.warn(warning)
        return 0

    dest_root.xplane.layer.lods = "3"
    if is_additive:
        for i, breakpoint in enumerate(lod_props_249[1:]):
            l = dest_root.xplane.layer.lod[i]
            l.near, l.far = 0, breakpoint
    else:
        for i, (near, far) in enumerate(zip(lod_props_249[:-1], lod_props_249[1:])):
            l = dest_root.xplane.layer.lod[i]
            l.near, l.far = int(near), int(far)

    final_logger_msg = ("{} now has {} for LODs: {}\n"
                        "NEXT STEP: Check if these LODs are necessary and correct")
    if any(filter(lambda lod: lod.far in {1000, 4000, 10000}, dest_root.xplane.layer.lod[1:])):
        final_logger_msg += ", especially some your new values are the 2.49 defaults"

    warnings.add(final_logger_msg.format(
        dest_root.name,
        dest_root.xplane.layer.lods,
        [(l.near, l.far) for l in dest_root.xplane.layer.lod])
    )

    for warning in warnings:
        logger.warn(warning)
    return found_lod_props


def do_convert_layer_properties(scene: bpy.types.Scene, workflow_type, root_objects: List[bpy.types.Object]):
    assert workflow_type != xplane_249_constants.WorkflowType.SKIP

    for root_object in root_objects:
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
