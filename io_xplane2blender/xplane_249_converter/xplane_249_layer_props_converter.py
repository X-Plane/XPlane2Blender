"""
Converts (some) 249 global properties whose destination is an XPlaneLayer
on a new root object. For instance, LODs, Slope Limits, Layer Groups, etc
"""
import collections
import math
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import bpy

from io_xplane2blender import xplane_constants, xplane_helpers
from xplane_helpers import logger
from io_xplane2blender.xplane_249_converter import (xplane_249_constants,
                                                    xplane_249_helpers)


def _convert_global_properties(search_objs: List[bpy.types.Object],
                               workflow_type: xplane_249_constants.WorkflowType,
                               dest_root: bpy.types.Object)->None:
    assert search_objs, "Must have objects to search"

    # We do a lot of "is it" testing...
    def _isint(s):
        try:
            int(s)
            return True
        except ValueError:
            return False

    def _isfloat(s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    logger.info("\nConverting Global OBJ Properties for Root Object '{}'\n"
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
                            dest_root: bpy.types.Object)->None:
    """
    Searches objs for "LOD_[0123]" properties to apply to dest_root's layer.lod
    member
    """
    assert search_objs, "Must have objects to search"

    logger.info("\nConverting LOD Properties for Root Object '{}'\n"
                "--------------------------------------------------".format(dest_root.name))
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

    lod_props_249 = collections.OrderedDict()
    lod_props_249[0] = 0
    lod_props_249[1] = 1000
    lod_props_249[2] = 4000
    lod_props_249[3] = 10000
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

    final_logger_msg = ("{} now has {} for LODs\n"
                        "NEXT STEP: Determine if any of these LODs are unnecessary")
    if any(filter(lambda lod: lod.far in {1000, 4000, 10000}, dest_root.xplane.layer.lod[1:])):
        final_logger_msg += ", especially some your new values are the 2.49 defaults"

    logger.warn(final_logger_msg.format(
        dest_root.name,
        dest_root.xplane.layer.lods,
        [(l.near, l.far) for l in dest_root.xplane.layer.lod])
    )


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
