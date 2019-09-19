'''
this modules handles converting CLights, VLights, and NLights
into XPlane2Blender 2.7x's information
'''

import re
from typing import cast, Callable, Dict, List, Match, Optional, Tuple, Union

import bpy
import mathutils


from io_xplane2blender import xplane_constants, xplane_helpers
from io_xplane2blender.xplane_helpers import logger
from io_xplane2blender.tests import test_creation_helpers
from io_xplane2blender.xplane_249_converter import xplane_249_constants, xplane_249_dataref_decoder, xplane_249_helpers
from io_xplane2blender.xplane_types import xplane_lights_txt_parser


def _could_autospot(lamp_obj: bpy.types.Object)->bool:
    #TODO: xplane_lights_txt_parser.parse_lights_file's lazy parsing is dumb
    is_parsed = xplane_lights_txt_parser.parse_lights_file()
    if is_parsed == False:
        logger.error("lights.txt file could not be parsed")
        return False

    return bool(xplane_lights_txt_parser.get_overload(lamp_obj.data.xplane.name))


def _convert_custom_lights(search_obj: bpy.types.Object)->List[bpy.types.Object]:
    '''
    Creates Custom Lights with the information of an applicable MESH object,
    returning a list of those new light objects (if any)
    '''
    assert (search_obj.type == "MESH" \
            and search_obj.material_slots \
            and search_obj.material_slots[0].material.type == "HALO"), \
            "{} must be an applicable MESH type".format(search_obj.name)
    new_name = (search_obj.name[:search_obj.name.index('.')] if '.' in search_obj.name else search_obj.name)
    clights = [] # type: List[bpy.types.Object]
    for vert in [search_obj.matrix_local * v.co for v in search_obj.data.vertices]:
        clight_obj = test_creation_helpers.create_datablock_lamp(
            test_creation_helpers.DatablockInfo(
                "LAMP",
                name=new_name, # Blender naturally adds numbers, ordering these for us
                layers=search_obj.layers,
                parent_info=test_creation_helpers.ParentInfo(
                    search_obj.parent,
                    search_obj.parent_type,
                    search_obj.parent_bone),
                location=vert,
                rotation_mode=search_obj.rotation_mode
            ),
            blender_light_type="POINT"
        ) # type: bpy.types.Object
        clights.append(clight_obj)
        clight_obj.data.xplane.type = xplane_constants.LIGHT_CUSTOM
        material = search_obj.material_slots[0].material #Guaranteed from assertion

        def find_color(color:str)->float:
            assert color in {"R", "G", "B", "A"}, "Color must be R, G, B, or A"
            try:
                if search_obj.game.properties[color].type in {"FLOAT", "INT"}:
                    return float(search_obj.game.properties[color].value)
                else:
                    raise TypeError("Prop '{}' is of type '{}', but should have been a 'FLOAT' or 'INT'"
                                    .format(color, search_obj.game.properties[color].type))
            except (KeyError, TypeError) as e:
                if color == "A":
                    return material.alpha
                else:
                    return material.diffuse_color[["R", "G", "B"].index(color)]

        clight_obj.data.color = (find_color("R"), find_color("G"), find_color("B"))
        clight_obj.data.energy = (find_color("A"))
        clight_obj.data.xplane.size = material.halo.size

        try:
            tex = material.texture_slots[0].texture
            clight_obj.data.xplane.uv = (tex.crop_min_x, tex.crop_min_y, tex.crop_max_x, tex.crop_max_y)
        except AttributeError: # No texture slots or tex doesn't have crop_min/max_x/y
            clight_obj.data.xplane.uv = (0, 0, 1, 1)
            logger.warn("{}'s material has no suitable texture to take Texture Coordinates from: using {}\n"
                        "NEXT STEPS: Consider adding an Image texture to your Custom Light\n"
                        .format(search_obj.name, clight_obj.data.xplane.uv[:]))

        #--- Custom Dataref Light Lookup) -------------------------------------
        try:
            s_or_tailname = search_obj.game.properties["name"]
        except KeyError:
            clight_obj.data.xplane.dataref = "none"
            logger.warn("{} has no 'name' properties, using dataref '{}'"
                        .format(clight_obj.name, clight_obj.data.xplane.dataref))
        else:
            lookup_record = xplane_249_dataref_decoder.lookup_dataref(s_or_tailname.value, s_or_tailname.value)
            if lookup_record.record:
                clight_obj.data.xplane.dataref = lookup_record.record[0]
                logger.info("Using dataref '{}' for custom light {}"
                            .format(clight_obj.data.xplane.dataref, clight_obj.name))
                if lookup_record.record[1] != 9:
                    logger.warn("Dataref '{}'  doesn't use an array of 9 floats or ints\n"
                                "NEXT STEPS: Choose a different dataref which uses an array of 9 floats or ints\n"
                                .format(clight_obj.data.xplane.dataref))
            elif not lookup_record.sname_success or not lookup_record.tailname_success:
                # We can disambiguate without all the madness!
                try:
                    disamb_path = search_obj.game.properties[s_or_tailname.value].value
                    clight_obj.data.xplane.dataref = (disamb_path if disamb_path[-1] == "/" else disamb_path + "/") + s_or_tailname.value
                    logger.info("Using custom dataref '{}' for custom light {}".format(clight_obj.data.xplane.dataref, clight_obj.name))
                except KeyError:
                    clight_obj.data.xplane.dataref = "none"
                    logger.warn("Could not disambiguate custom dataref '{}', using '{}' instead\n"
                                "NEXT STEPS: If desired, re-enter your own dataref\n"
                                .format(s_or_tailname.value, clight_obj.data.xplane.dataref))

        #----------------------------------------------------------------------

        # TODO: If you ever refactor xplane_lights_txt_parser's API where
        # baking doesn't exist, fix this. - Ted, 04/09/2019
        #
        # Because xplane_lights_txt_parser's API is terrible, we can't
        # easily look up Dataref -> List[ParsedLightOverload] to see
        # about autospot conversion. Instead, I've hardcoded some common patterns
        # in lights.txt of DREFs that are used with SPILL_ overloads
        if (clight_obj.data.xplane.dataref.endswith("spill")
            or clight_obj.data.xplane.dataref.endswith("_sp")):
            #TODO: Maybe we should just do it and if they didn't like it, they can turn it back.
            # How many cases are there where a light ending in "spill" or "_sp" wouldn't be a spot light?
            logger.info("{} may be able to use the Lamp's rotation for aiming\n"
                        "NEXT STEP: Consider changing {}'s type to 'Spot' to enable light aiming via Lamp rotation\n".format(clight_obj.name, clight_obj.name))

    test_creation_helpers.delete_datablock(search_obj)
    return clights

def convert_lights(scene: bpy.types.Scene, workflow_type: xplane_249_constants.WorkflowType, root_object: bpy.types.Object)->List[bpy.types.Object]:
    if workflow_type == xplane_249_constants.WorkflowType.REGULAR:
        search_objs = scene.objects
    elif workflow_type == xplane_249_constants.WorkflowType.BULK:
        search_objs = [root_object] + xplane_249_helpers.get_all_children_recursive(root_object, scene)
    else:
        assert False, "Unknown workflow type"

    def add_converted_light(converted_obj: bpy.types.Object):
        assert converted_obj.type == "LAMP"
        #l_type = converted_obj.data.xplane.type
        #msg = "Converted {}".format(converted_obj.name)
        #msg += ", Type: {}".format("Non-Exporting" if l_type == xplane_constants.LIGHT_NON_EXPORTING else l_type.title())
        #msg += ", Light Name: '{}'".format(converted_obj.data.xplane.name) if converted_obj.data.xplane.name else ""
        #msg += ", Light Params: '{}'".format(converted_obj.data.xplane.params) if converted_obj.data.xplane.params else ""
        #print(msg)

        converted_objects.append(converted_obj)

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

    # All objects we change or create (but not remove)
    converted_objects = [] # type: List[bpy.types.Object]
    infos = set()
    warnings = set()
    for search_obj in filter(isLight, search_objs):
    #--- All Lights -----------------------------------------------------------
        #print("Attempting to convert {}".format(search_obj.name))
        if (search_obj.type == "LAMP"
            and search_obj.data.type != "POINT"):
            # No autospot correction because we don't know their intent for the light
            search_obj.data.xplane.type = xplane_constants.LIGHT_NON_EXPORTING
            converted_objects.append(search_obj)
            continue

        simple_name = (search_obj.name[:search_obj.name.index('.')]
                       if '.' in search_obj.name else search_obj.name).strip().casefold()
        #--- Custom Lights ---------------------------------------------------
        if search_obj.type == "MESH" and search_obj.data.vertices:
            clights = _convert_custom_lights(search_obj)
            if clights:
                converted_objects.extend(clights)
                infos.add("Original meshes representing Custom Lights deleted after conversion")
        #--- End Custom Lights ------------------------------------------------
        else:
        #--- Not Custom Lights ------------------------------------------------
            #--- Default and Deprecated Lights --------------------------------
            lamp_obj = search_obj
            if "pulse" in simple_name:
                lamp_obj.data.xplane.type = xplane_constants.LIGHT_PULSING
                add_converted_light(lamp_obj)
            elif "strobe" in simple_name:
                lamp_obj.data.xplane.type = xplane_constants.LIGHT_STROBE
                add_converted_light(lamp_obj)
            elif "traffic" in simple_name:
                lamp_obj.data.xplane.type = xplane_constants.LIGHT_TRAFFIC
                add_converted_light(lamp_obj)
            elif "flash" in simple_name:
                lamp_obj.data.xplane.type = xplane_constants.LIGHT_FLASHING
                add_converted_light(lamp_obj)
            elif "lamp" in simple_name:
                lamp_obj.data.xplane.type = xplane_constants.LIGHT_DEFAULT
                add_converted_light(lamp_obj)
            elif simple_name in {"smoke_black", "smoke_white"}:
                warnings.add("Smoke type lights are no longer supported, set light to Non-Exporting instead\n"
                            "NEXT STEPS: Consider using a modern particle emitter instead\n")
                lamp_obj.data.xplane.type = xplane_constants.LIGHT_NON_EXPORTING
                add_converted_light(lamp_obj)
                continue
            #--- End Default and Deprecated Lights ----------------------------
            else:
            #--- Named/Param/Magent Lights ------------------------------------
                props = {p.name.casefold(): p.value for p in lamp_obj.game.properties}
                lamp_obj.data.xplane.name = props["name"].strip() if "name" in props else simple_name
                params = props["params"].strip() if "params" in props else ""

                #--- Magnets --------------------------------------------------
                if lamp_obj.data.xplane.name.casefold() == "magnet".casefold():
                    if search_obj.rotation_mode == "AXIS_ANGLE":
                        rotation = search_obj.rotation_axis_angle
                    elif search_obj.rotation_mode == "QUATERNION":
                        rotation = search_obj.rotation_quaternion
                    else:
                        rotation = search_obj.rotation_euler

                    empty = test_creation_helpers.create_datablock_empty(
                        test_creation_helpers.DatablockInfo("EMPTY",
                                                            lamp_obj.name,
                                                            lamp_obj.layers,
                                                            test_creation_helpers.ParentInfo(
                                                                lamp_obj.parent, lamp_obj.parent_type, lamp_obj.parent_bone),
                                                            lamp_obj.location,
                                                            lamp_obj.rotation_mode,
                                                            rotation),
                        xplane_constants.EMPTY_USAGE_MAGNET)
                    bpy.data.objects.remove(lamp_obj, do_unlink=True)
                    converted_objects.append(empty)
                    logger.info("Changed {} from a Lamp to a special Magnet Empty"
                                .format(empty.name))
                    magnet_props = empty.xplane.special_empty_props.magnet_props
                    # We want them to start exporting quickly, even with "magnet" as a debug name
                    magnet_props.debug_name = empty.name
                    logger.info("NEXT STEPS: Consider choosing a new Magnet Debug Name for {}\n".format(empty.name))

                    match = re.match(r"(?P<magnet_type>xpad/flashlight|xpad|flashlight)", params)
                    try:
                        d = cast(Match, match).groupdict()
                        if "xpad" in d["magnet_type"]:
                            magnet_props.magnet_type_is_xpad = True
                        if "flashlight" in d["magnet_type"]:
                            magnet_props.magnet_type_is_flashlight = True
                    except AttributeError: #None doesn't have groupdict()
                        logger.warn("{em_name}'s params property '{params}' does not have a valid magnet type\n"
                                    "NEXT STEPS: Ensure {em_name} has Magnet types checked\n"
                                    .format(em_name=empty.name, params=params))
                    root_object.xplane.layer.export_type = xplane_constants.EXPORT_TYPE_COCKPIT
                    continue
                #--- End Magnets ----------------------------------------------
                else:
                #--- Named/Param ----------------------------------------------
                    if params:
                        lamp_obj.data.xplane.type = xplane_constants.LIGHT_PARAM
                        lamp_obj.data.xplane.params = params
                    else:
                        lamp_obj.data.xplane.type = xplane_constants.LIGHT_NAMED

                    add_converted_light(lamp_obj)
                    if _could_autospot(lamp_obj):
                        logger.info("{} may be able to use the Lamp's rotation for aiming\n"
                                    "NEXT STEP: Consider changing {}'s type to 'Spot' to enable light aiming via Lamp rotation\n".format(lamp_obj.name, lamp_obj.name))

                #--- End Named/Param Lights -----------------------------------
            #--- End Named/Param/Magent Lights --------------------------------
        #--- End Not Custom Lights --------------------------------------------
    list(map(logger.info, infos))
    list(map(logger.warn, warnings))
    #--- End All Lights -------------------------------------------------------
    return converted_objects
