import math
import re
from copy import deepcopy
from itertools import takewhile, tee, zip_longest
from typing import Dict, List, Optional, Tuple, Union

import bpy
import mathutils
from mathutils import Euler, Matrix, Vector

from io_xplane2blender import xplane_constants, xplane_types, xplane_utils
from io_xplane2blender.xplane_types import xplane_object
from io_xplane2blender.xplane_utils import xplane_lights_txt_parser

from ..xplane_config import getDebug
from ..xplane_constants import *
from ..xplane_helpers import (FLOAT_PRECISION, floatToStr, logger, vec_b_to_x,
                              vec_x_to_b)


class XPlaneLight(xplane_object.XPlaneObject):
    def __init__(self, blenderObject:bpy.types.Object):
        super().__init__(blenderObject)
        # Indices for VLIGHTs table
        self.indices = [0,0]

        # Our light type, not the Blender light type
        self.lightType = blenderObject.data.xplane.type

        # Color, for use by CUSTOM or AUTOMATIC lights
        # change color according to type
        if self.lightType == LIGHT_FLASHING:
            self.color:List[float] = list(blenderObject.data.color)
            self.color[0] = -self.color[0]
        elif self.lightType == LIGHT_PULSING:
            self.color = [9.9] * 3
        elif self.lightType == LIGHT_STROBE:
            self.color = [9.8] * 3
        elif self.lightType == LIGHT_TRAFFIC:
            self.color = [9.7] * 3
        elif blenderObject.data.xplane.enable_rgb_override:
            self.color:List[float] = blenderObject.data.xplane.rgb_override_values[:]
        else:
            self.color:List[float] = list(blenderObject.data.color)

        self.dataref = blenderObject.data.xplane.dataref
        self.energy = blenderObject.data.energy
        # This refers to the size of the custom light,
        # not the SIZE parameter in a param light
        self.size = blenderObject.data.xplane.size
        self.uv = blenderObject.data.xplane.uv

        # Our lights.txt light name, not the Blender Object's name
        self.lightName = blenderObject.data.xplane.name

        # If the lightName is unknown
        #     params_completed and record_completed these will be none
        # Use __getitem__ and __contains__ to ask if there are columns
        # and fields we care about

        # self.params is the eventual content of the
        # LIGHT_PARAM OBJ directive
        if self.lightType == LIGHT_AUTOMATIC:
            self.params = {}
        elif self.lightType == LIGHT_PARAM:
            self.params = blenderObject.data.xplane.params
        else:
            self.params = None
        self.comment:Optional[str] = None

        # Used for auto correction For LIGHT_NAMED this is used for autocorrection (if applicable)
        self.record_completed:Optional[xplane_lights_txt_parser.ParsedLightOverload] = None
        self.is_omni = False

        self.setWeight(10000)

    def collect(self)->None:
        super().collect()
        light_data = self.blenderObject.data
        if not self.lightName and self.lightType in {LIGHT_NAMED, LIGHT_PARAM, LIGHT_AUTOMATIC}:
            logger.error(f"{self.blenderObject.name} is a {self.lightType.title()} light but has no light name")
            return
        try:
            parsed_light = xplane_lights_txt_parser.get_parsed_light(self.lightName)
        except KeyError:
            parsed_light = None

        unknown_light_name_warning = (f"\"{self.blenderObject.name}\"'s Light Name '{self.lightName}' is unknown,"
                                      f" check your spelling or update your lights.txt file")

        # X-Plane Light Type | Light Type | parsed_light | light_param_defs | Result
        # -------------------|------------|--------------|------------------|-------
        # LIGHT_NAMED        | *          | Yes          | Yes              | Error, "known param used as named light"
        # LIGHT_NAMED        | "POINT"    | Yes          | No               | Apply sw_callback, do not do autocorrect (POINT means OMNI)
        # LIGHT_NAMED        | not "POINT"| Yes          | No               | Apply sw_callback if possible, autocorrect
        # LIGHT_NAMED        | *          | No           | N/A              | Treat as unknown named light, Warning given, NAMED written as is, no SW callbacks applied
        if self.lightType == LIGHT_NAMED and parsed_light and parsed_light.light_param_def:
            logger.error(f"Light name {self.lightName} is a known param light, being used as a name light. Check the light name or light type")
            return
        elif self.lightType == LIGHT_NAMED and parsed_light and not parsed_light.light_param_def:
            self.record_completed = parsed_light.overloads[0]
            if "DREF" in self.record_completed.prototype():
                self.record_completed.apply_sw_callback()
        elif self.lightType == LIGHT_NAMED and not parsed_light:
            logger.warn(unknown_light_name_warning)
        # X-Plane Light Type | Light Type | parsed_light | light_param_defs | Result
        # -------------------|------------|--------------|------------------|-------
        # LIGHT_PARAM        | "POINT"    | Yes          | Yes              | Parse params, replace self.params_complete
        # LIGHT_PARAM        | not "POINT"| Yes          | Yes              | Parse params, replace self.params_complete, apply sw_callback if possible. Autocorrect with ANIM_
        # LIGHT_PARAM        | *          | Yes          | No               | Error, "known named light used as a param light"
        # LIGHT_PARAM        | *          | No           | N/A              | Warning given, PARAMS written as is, no auto correction_applied
        elif self.lightType == LIGHT_PARAM and parsed_light and parsed_light.light_param_def:
            # This section is actually validation/apply_sw_callback only, LIGHT_PARAM type inserts
            # xplane.params content directly into the OBJ
            params_formal = parsed_light.light_param_def

            # Parsed params from the params box, stripped and ignoring the commemnt
            # Make the actual parameters, if there are <= than params_formal, its okay
            # if here are more we have a comment.
            # Find nth group of whitespace space after the end the count

            params_actual = []
            params_itr = iter(self.blenderObject.data.xplane.params.lstrip())

            while len(params_actual) < len(params_formal):
                try:
                    n, params_itr = tee(params_itr)
                    next(n)
                except StopIteration:
                    break
                else:
                    actual = "".join(takewhile(lambda c: not c.isspace(), params_itr))
                    if actual:
                        params_actual.append(actual)
            self.comment = "".join(params_itr).lstrip()

            if len(params_actual) < len(params_formal):
                logger.error(f"Not enough actual parameters ('{' '.join(params_actual)}') to"
                             f" satisfy 'LIGHT_PARAM_DEF {len(params_formal)} {' '.join(params_formal)}'")
                return

            if self.comment and not self.comment.startswith(("//","#")):
                logger.warn(f"Comment in param light ({self.comment}) does not start with '//' or '#'")

            self.record_completed = parsed_light.overloads[0]
            for i, (pformal, pactual) in enumerate(zip(params_formal, params_actual)):
                try:
                    float(pactual)
                except ValueError: # pactual not a float
                    logger.error(f"Parameter {i} ({pactual}) of {self.blenderObject.name} is not a number")
                    return
                else:
                    try:
                        self.record_completed.replace_parameterization_argument(pformal, float(pactual))
                    except ValueError:
                        continue

            if "DREF" in self.record_completed.prototype():
                self.record_completed.apply_sw_callback()

            self.is_omni = self.record_completed["WIDTH"] >= 1.0

            dir_vec = Vector(map(self.record_completed.__getitem__, ["DX","DY","DZ"]))
            if dir_vec.magnitude == 0.0 and not self.is_omni:
                logger.error("Non-omni light cannot have (0.0,0.0,0.0) for direction")
                return
        elif self.lightType == LIGHT_PARAM and parsed_light and not parsed_light.light_param_def:
            logger.error(f"Light name {self.lightName} is a named light, not a param light."
                         f" Check the light type drop down menu")
            return
        # Even if we don't know the PARAM light, we still have to check if we're about to write out no params
        elif self.lightType == LIGHT_PARAM and not parsed_light:
            logger.warn(unknown_light_name_warning)
            if not self.blenderObject.data.xplane.params.split():
                logger.error(f"'{self.blenderObject.name}' has an empty parameters box")
                return
        # X-Plane Light Type | Light Type | parsed_light | light_param_defs | Result
        # -------------------|------------|--------------|------------------|-------
        # LIGHT_CUSTOM       | *          | N/A          | N/A              | Write custom light as is
        elif self.lightType == LIGHT_CUSTOM:
            pass
        # LIGHT_AUTOMATC preforms no autocorrection. IF POINT, it is interpreted as an omni-directional light
        #
        # X-Plane Light Type | Light Type | parsed_light | light_param_defs | Result
        # -------------------|------------|--------------|------------------|-------
        # LIGHT_AUTOMATIC    |"POINT/SPOT"| Yes          | Yes              | Fill out params and write
        # LIGHT_AUTOMATIC    |"POINT/SPOT"| Yes          | No               | Treat as named light, apply any sw_callbacks, write
        # LIGHT_AUTOMATIC    |"POINT/SPOT"| No           | N/A              | Treat as named light, give warning, write as is
        # LIGHT_AUTOMATIC    | Any Others | N/A          | N/A              | Error, "Automatic lights require POINT or SPOT"
        elif self.lightType == LIGHT_AUTOMATIC and light_data.type not in {"POINT", "SPOT"}:
            logger.error(f"Automatic lights must be a Point or Spot light, change {self.blenderObject.name}'s type or change it's X-Plane Light Type")
            return
        elif self.lightType == LIGHT_AUTOMATIC and parsed_light and parsed_light.light_param_def:
            self.is_omni = light_data.type == "POINT"

            #TODO: Need test
            if (light_data.type == "SPOT"
                and "SIZE" in parsed_light.light_param_def
                and not light_data.use_custom_distance):
                logger.error("Automatic Spot Lights with 'SIZE' as a parameter must have 'Custom Distance' checked")
                return

            #"CELL_", "DAY", "DREF" are never parameterizable,
            convert_table = {
                    "R":self.color[0],
                    "G":self.color[1],
                    "B":self.color[2],
                    "A": 1,
                    "INDEX": light_data.xplane.param_index,
                    "SIZE":light_data.cutoff_distance, # Custom Distance > Distance
                    "DX":"DX", # Filled in later
                    "DY":"DY", # Filled in later
                    "DZ":"DZ", # Filled in later
                    "WIDTH": 1 if self.is_omni else math.cos(light_data.spot_size * .5),
                    "FREQ": light_data.xplane.param_freq,
                    "PHASE": light_data.xplane.param_phase,
                    "UNUSED":0, # We just shove in something here
                    "ZERO":0,
                    "NEG_ONE":-1
                }

            #TODO: Need test
            #TODO: Need an error for problem case here:
            # A xplane_sp light in a Blender Point light = Problem?
            # A xplane_bb in a Blender Point Light = Autocorrect
            if "WIDTH" in parsed_light.light_param_def and round(light_data.spot_size) == math.pi:
                logger.error("Spotlight Size for {self.blenderObject.name} cannot be 180 degrees")
                return

            def strip_trailing_underscores(param:str)->str:
                """Return the param, stripped of any trailing '_'
                """
                if "UNUSED" in param:
                    return "UNUSED"
                elif "NEG_ONE" in param:
                    return "NEG_ONE"
                elif "ZERO" in param:
                    return "ZERO"
                elif "ONE" in param:
                    return "ONE"
                else:
                    return param

            self.params = {param:convert_table[strip_trailing_underscores(param)] for param in parsed_light.light_param_def}
            self.record_completed = parsed_light.overloads[0]
            for p_arg in filter(
                    lambda arg: isinstance(arg,str)
                                and not arg.startswith("sim")
                                and arg not in {"DX", "DY", "DZ"},
                            self.record_completed):
                self.record_completed.replace_parameterization_argument(p_arg, self.params[p_arg])

            # Leaving DXYZ in a record's arguments is okay
            # - It doesn't affect any sw_callbacks (as of 4/19/2020)
            # - We'll be filling in instead of autocorrecting
            if "DREF" in self.record_completed.prototype():
                self.record_completed.apply_sw_callback()

        elif self.lightType == LIGHT_AUTOMATIC and parsed_light and not parsed_light.light_param_def:
            # Like LIGHT_NAMED but no autocorrection
            self.record_completed = parsed_light.overloads[0]
            if "DREF" in self.record_completed.prototype():
                self.record_completed.apply_sw_callback()
        elif self.lightType == LIGHT_AUTOMATIC and not parsed_light:
            logger.warn(unknown_light_name_warning)
        # X-Plane Light Type | Light Type | parsed_light | light_param_defs | Result
        # -------------------|------------|--------------|------------------|-------
        # LIGHT_ old         | *          | N/A          | N/A              | Write
        elif self.lightType in LIGHTS_OLD_TYPES:
            pass
        else:
            assert False, f"{self.blenderObject.name} had some property configuation that was unaccounted for"

    def write(self)->None:
        debug = getDebug()
        indent = self.xplaneBone.getIndent()
        o = super().write()

        light_data = self.blenderObject.data
        try:
            parsed_light = xplane_lights_txt_parser.get_parsed_light(self.lightName)
        except KeyError:
            parsed_light = None

        bakeMatrix = self.xplaneBone.getBakeMatrixForAttached()
        translation = bakeMatrix.to_translation()
        has_anim = False

        def find_autocorrect_axis_angle(dir_vec_p_norm_b:Vector, bake_matrix:Matrix)->Tuple[Vector, float]:
            """
            Given a vector of where the light will be pointed in X-Plane and our real rotation,
            find the Axis-Angle for how we need to rotate via animation to make the difference
            """
            def clamp(num:float, minimum:float, maximum:float)->float:
                if num < minimum:
                    return minimum
                elif num > maximum:
                    return maximum
                else:
                    return num

            # Multiple bake matrix by Vector to get the direction of the Blender object
            dir_vec_b_norm = bakeMatrix.to_3x3() @ Vector((0,0,-1))

            # P is start rotation, and B is stop. As such, we have our axis of rotation.
            # "We take the X-Plane light and turn it until it matches what the artist wanted"
            axis_angle_vec3_b = dir_vec_p_norm_b.cross(dir_vec_b_norm)

            dot_product_p_b = dir_vec_p_norm_b.dot(dir_vec_b_norm)
            if dot_product_p_b < 0:
                axis_angle_theta = math.pi - math.asin(clamp(axis_angle_vec3_b.magnitude,-1.0,1.0))
            else:
                axis_angle_theta = math.asin(clamp(axis_angle_vec3_b.magnitude,-1.0,1.0))
            return axis_angle_vec3_b, axis_angle_theta

        def should_autocorrect_nonautomatic():
            try:
                return (self.lightType != LIGHT_AUTOMATIC
                        # Yes, '!= "POINT"' matters for historical reasons
                        and light_data.type != "POINT"
                        and all(param in self.record_completed for param in ["DX", "DY", "DZ"]))
            except TypeError as te: # self.record_completed is None
                return False

        def should_autocorrect_automatic():
            if (self.lightType == LIGHT_AUTOMATIC and light_data.type == "SPOT"):
                if self.params:
                    # If we will be LIGHT_PARAM but we won't be filling in DXYZ ourselves
                    return all(param not in self.params for param in ["DX", "DY", "DZ"])
                elif self.record_completed:
                    # If we will be LIGHT_NAMED and our overload has DXYZ columns to correct
                    return all(column in self.record_completed for column in ["DX", "DY", "DZ"])
            else:
                return False

        def should_fill_in_dxyz_for_automatic():
            try:
                return (self.lightType == LIGHT_AUTOMATIC
                    and light_data.type == "SPOT"
                    # If we have a DXYZ we'll use that instead of autocorrection
                    and {"DX", "DY", "DZ"} <= set(self.params))
            except TypeError: # self.params is None
                return False

        if (should_autocorrect_nonautomatic() or should_autocorrect_automatic()):
            axis_angle_vec_b, axis_angle_theta = find_autocorrect_axis_angle(
                    vec_x_to_b(
                        Vector(self.record_completed[param] for param in ["DX", "DY", "DZ"]).normalized()
                        ),
                    bakeMatrix)
            # Vector P(arameters), in Blender Space

            # Ben says: lights always have some kind of offset because the light itself
            # is "at" 0,0,0, so we treat the translation as the light position.
            # But if there is a ROTATION then in the light's bake matrix, the
            # translation is pre-rotation.  but we want to write a single static rotation
            # and then NOT write a translation every time.
            #
            # Inverse to change our animation order (so we really have rot, trans when we
            # originally had trans, rot) and now we can use the translation in the lamp
            # itself.
            if round(axis_angle_theta,5) != 0.0 and not self.is_omni:
                o += f"{indent}ANIM_begin\n"

                if debug:
                    o += f"{indent}# static rotation\n"

                axis_angle_vec3_x = vec_b_to_x(axis_angle_vec_b).normalized()
                tab = "\t"
                anim_rotate_dir = (
                        f"{indent}ANIM_rotate"
                        f"\t{tab.join(map(floatToStr,axis_angle_vec3_x))}"
                        f"\t{floatToStr(math.degrees(axis_angle_theta))}"
                        f"\t{floatToStr(math.degrees(axis_angle_theta))}"
                        f"\n"
                    )
                o += anim_rotate_dir

                rot_matrix = mathutils.Matrix.Rotation(axis_angle_theta,4,axis_angle_vec_b)
                translation = rot_matrix.inverted() @ translation
                has_anim = True
        elif should_fill_in_dxyz_for_automatic():
            dir_vec_b_norm = bakeMatrix.to_3x3() @ Vector((0,0,-1))
            for param, vec_comp in zip(["DX","DY","DZ"], vec_b_to_x(dir_vec_b_norm.normalized())):
                # self.record_completed isn't needed anymore, but,
                # to be tidy, we can finally update it too
                # in case we need to do something with it later
                # -Ted, 4/17/2020
                #self.record_completed[param] = vec_comp
                self.params[param] = vec_comp

        translation_x_str = " ".join(map(floatToStr,vec_b_to_x(translation)))
        known_named_automatic = self.lightType == LIGHT_AUTOMATIC and parsed_light and not parsed_light.light_param_def
        unknown_named_automatic = self.lightType == LIGHT_AUTOMATIC and not parsed_light
        if (self.lightType == LIGHT_NAMED
            or (known_named_automatic or unknown_named_automatic)):
            o += f"{indent}LIGHT_NAMED\t{self.lightName} {translation_x_str}\n"
        elif (self.lightType == LIGHT_PARAM
                or (self.lightType == LIGHT_AUTOMATIC and parsed_light.light_param_def)):
            o += f"{indent}LIGHT_PARAM\t{self.lightName} {translation_x_str}"
            o += " "
            o += f"{' '.join(map(floatToStr,self.params.values()))}" if self.lightType == LIGHT_AUTOMATIC else self.params
            o += "\n"
        elif self.lightType == LIGHT_CUSTOM:
            o += (f"{indent}LIGHT_CUSTOM\t{translation_x_str}"
                  f" {' '.join(map(floatToStr,self.color))}"
                  f" {' '.join(map(floatToStr,[self.energy, self.size]))}"
                  f" {' '.join(map(floatToStr,self.uv))}"
                  f" {self.dataref}\n")
        # do not render lights with no indices
        elif self.indices[1] > self.indices[0]:
            offset = self.indices[0]
            count = self.indices[1] - self.indices[0]
            o += f"{indent}LIGHTS\t{offset} {count}\n"

        if has_anim:
            o += f"{indent}ANIM_end\n"

        return o
