'''
this modules handles converting CLights, VLights, and NLights
into XPlane2Blender 2.7x's information
'''

from typing import Callable, Dict, List, Optional, Tuple, Union

import bpy


from io_xplane2blender import xplane_constants, xplane_helpers
from xplane_helpers import logger
from io_xplane2blender.tests import test_creation_helpers
from io_xplane2blender.xplane_249_converter import xplane_249_constants, xplane_249_helpers

def convert_lights(scene: bpy.types.Scene, workflow_type: xplane_249_constants.WorkflowType, root_object: bpy.types.Object):
    if workflow_type == xplane_249_constants.WorkflowType.REGULAR:
        search_objs = scene.objects
    elif workflow_type == xplane_249_constants.WorkflowType.BULK:
        search_objs = [root_object] + xplane_249_helpers.get_all_children_recursive(root_object, scene)
    else:
        assert False, "Unknown workflow type"

    print([o.name for o in search_objs])
    def isLight(obj: bpy.types.Object):
        try:
            if (obj.type == "LAMP"):
                return True
            if (obj.type == "MESH"
                and obj.material_slots
                and obj.material_slots[0].material.type == "HALO"):
                return True
        except (AttributeError, IndexError) as e: # material is None, or material_slots is empty
            return False

    for search_obj in filter(isLight, search_objs):
        if search_obj.type == "LAMP" and search_obj.data.type != "POINT":
            logger.warn("Modern XPlane2Blender exports all lamp including {}s\n"
                        "NEXT STEPS: Move {} to a non-exporting layer or root object, or use another method to prevent export"
                        .format(search_obj.data.type.title(), search_obj.name))
        simple_name = (search_obj.name[:search_obj.name.index('.')]
                       if '.' in search_obj.name else search_obj.name).strip().casefold()
        logger.info("Attempting to convert {}".format(simple_name))
        if search_obj.type == "MESH":
            print("CUSTOM LAMP!")
            for vert in search_obj.data.vertices:
                #TODO NEED R,G,B, S1,T1, S2, T2 and custom dataref
                if search_obj.rotation_mode == "AXIS_ANGLE":
                    rotation = search_obj.rotation_axis_angle
                elif search_obj.rotation_mode == "QUATERNION":
                    rotation = search_obj.rotation_quaternion
                else:
                    rotation = search_obj.rotation_euler

                clight = test_creation_helpers.create_datablock_lamp(
                    test_creation_helpers.DatablockInfo(
                        "LAMP",
                        name=simple_name, # Blender naturally orders this for us
                        layers=search_obj.layers,
                        parent_info=test_creation_helpers.ParentInfo(
                            search_obj.parent,
                            search_obj.parent_type,
                            search_obj.parent_bone),
                        location=vert.co+search_obj.matrix_world.translation,
                        rotation_mode=search_obj.rotation_mode,
                        rotation=rotation
                    ),
                    blender_light_type="SPOT" if simple_name.endswith("_sp") else "POINT"
                )
                clight.xplane.type = xplane_constants.LIGHT_CUSTOM
                logger.warn("Custom Light '{}' created from a vertex of {}\n"
                            "NEXT STEPS: Consider deleting {} as modern XPlane2Blender won't use it"
                            .format(clight.name, search_obj, search_obj))
        else:
            light = search_obj
            if 'pulse' in simple_name:
                light.data.xplane.type = xplane_constants.LIGHT_PULSING
            elif 'strobe' in simple_name:
                light.data.xplane.type = xplane_constants.LIGHT_STROBE
            elif 'traffic' in simple_name:
                light.data.xplane.type = xplane_constants.LIGHT_TRAFFIC
            elif 'flash' in simple_name:
                light.data.xplane.type = xplane_constants.LIGHT_FLASHING
            elif 'lamp' in simple_name:
                light.data.xplane.type = xplane_constants.LIGHT_DEFAULT
            elif simple_name in {'smoke_black', 'smoke_white'}:
                logger.warn("Smoke type lights are not supported in XPlane2Blender\n"
                            "NEXT STEPS: Consider using a modern particle emitter instead")
            else: # named/param light
                props = {p.name.casefold(): p.value for p in light.game.properties}
                light.data.xplane.name = props["name"].strip() if "name" in props else simple_name
                params = props["params"].strip() if "params" in props else ""
                if params:
                    light.data.xplane.type = xplane_constants.LIGHT_PARAM
                    light.data.xplane.params = params
                else:
                    light.data.xplane.type = xplane_constants.LIGHT_NAMED

                light.data.type = "SPOT" if simple_name.endswith("_sp") else "POINT"
            logger.info("Set {}'s X-Plane Light Type to {}".format(simple_name, light.data.xplane.type.title()))
