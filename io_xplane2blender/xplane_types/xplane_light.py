import math
import re
from copy import deepcopy
from itertools import zip_longest
from typing import List, Optional

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
        self.color:List[float] = [0,0,0]
        if self.lightType == LIGHT_FLASHING:
            self.color[0] = -blenderObject.data.color[0]
        elif self.lightType == LIGHT_PULSING:
            self.color[:] = 9.9
        elif self.lightType == LIGHT_STROBE:
            self.color[:] = 9.8
        elif self.lightType == LIGHT_TRAFFIC:
            self.color[:] = 9.7
        elif blenderObject.data.xplane.enable_rgb_override:
            self.color:List[float] = blenderObject.data.xplane.rgb_override_values[:]
        else:
            self.color:List[float] = list(blenderObject.data.color[:])

        self.dataref = blenderObject.data.xplane.dataref
        self.energy = blenderObject.data.energy
        # This refers to the size of the custom light,
        # not the SIZE parameter in a param light
        self.size = blenderObject.data.xplane.size
        self.uv = blenderObject.data.xplane.uv

        # Our lights.txt light name, not the Blender Object's name
        self.lightName = blenderObject.data.xplane.name

        # The combinination of lights.txt overload, filled in params,
        # and applied sw_light_callback
        self.params_completed:Optional[xplane_lights_txt_parser.ParsedLightOverload] = None
        self.comment:Optional[str] = None
        self.is_omni = False

        self.setWeight(10000)

    def collect(self)->None:
        super().collect()
        light_data = self.blenderObject.data
        try:
            parsed_light = xplane_lights_txt_parser.get_parsed_light(self.lightName)
        except KeyError:
            pass

        unknown_light_name_warning = (f"\"{self.blenderObject.name}\"'s Light Name '{self.lightName}' is unknown,"
                                      f" check your spelling or update your lights.txt file")

        # X-Plane Light Type | Light Type | parsed_light | light_param_defs | Result
        # -------------------|------------|--------------|------------------|-------
        # LIGHT_NAMED        | *          | Yes          | Yes              | Error, "known param used as named light"
        # LIGHT_NAMED        | *          | Yes          | No               | Apply sw_callback if possible
        # LIGHT_NAMED        | *          | No           | N/A              | Treat as unknown named light, Warning given, NAMED written as is, no SW callbacks applied
        if self.lightType == LIGHT_NAMED and parsed_light and parsed_light.light_param_def:
            logger.error(f"Light name {self.lightName} is a known param light, being used as a name light. Check the light name or light type")
            return
        elif self.lightType == LIGHT_NAMED and parsed_light and not parsed_light.light_param_def:
            self.params_completed = parsed_light.overloads[0]
            if parsed_light.overloads[0].overload_type in {"BILLBOARD_SW", "SPILL_SW"}:
                self.params_completed.apply_sw_callback()
        elif self.lightType == LIGHT_NAMED and not parsed_light:
            logger.warn(unknown_light_name_warning)
        # X-Plane Light Type | Light Type | parsed_light | light_param_defs | Result
        # -------------------|------------|--------------|------------------|-------
        # LIGHT_PARAM        | "POINT"    | Yes          | Yes              | Parse params, replace self.params_complete
        # LIGHT_PARAM        | not "POINT"| Yes          | Yes              | Parse params, replace self.params_complete, apply sw_callback if possible. Autocorrect with ANIM_
        # LIGHT_PARAM        | *          | Yes          | No               | Error, "known named light used as a param light"
        # LIGHT_PARAM        | *          | No           | N/A              | Warning given, PARAMS written as is, no auto correction_applied
        elif self.lightType == LIGHT_PARAM and parsed_light and parsed_light.light_param_def:
            params_formal = parsed_light.light_param_def

            # Parsed params from the params box, stripped and ignoring the commemnt
            params_actual = re.findall(r" *[^ ]*",self.blenderObject.data.xplane.params)[:-1]

            if len(params_actual) < len(params_formal):
                logger.error(f"Not enough actual parameters ({' '.join(params_actual)}) to"
                             f" satisfy LIGHT_PARAM_DEF {len(params_formal)} {' '.join(params_formal)}")
                return

            if len(params_actual) > len(params_formal):
                self.comment = (''.join(params_actual[len(params_formal):])).lstrip()
                if not (self.comment.startswith("//") or self.comment.startswith("#")):
                    logger.warn(f"Comment in param light {self.comment} does not start with '//' or '#'")

            self.params_completed = parsed_light.overloads[0]
            params_actual = [p.strip() for p in params_actual[0:len(params_formal)]]
            # What happenes when params_formal is longer than params_completed
            for i, (pformal, pactual) in enumerate(zip(params_formal, params_actual)):
                try:
                    float(pactual)
                except ValueError:
                    logger.error(f"Parameter {i} ({pactual}) of {self.blenderObject.name} is not a number")
                else:
                    try:
                        self.params_completed[pformal] = float(pactual)
                    except KeyError: # __setitem__ failed
                        # If the actual arguments doesn't have a replacement option,
                        # its okay. Some overloads don't use every one of them
                        pass

            if parsed_light.overloads[0].overload_type in {"BILLBOARD_SW", "SPILL_SW"}:
                self.params_completed.apply()

            self.is_omni = self.params_completed["WIDTH"] >= 1.0
            dir_vec = Vector(map(self.params_completed.__getitem__, ["DX","DY","DZ"]))
            #TODO: This aught to have rounding?
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
        # LIGHT_AUTOMATIC    |"POINT/SPOT"| Yes          | No               | Treat as named light, write as is
        # LIGHT_AUTOMATIC    |"POINT/SPOT"| No           | N/A              | Treat as named light, give warning, write as is
        # LIGHT_AUTOMATIC    | Any Others | N/A          | N/A              | Error, "Automatic lights require POINT or SPOT"
        elif self.lightType == LIGHT_AUTOMATIC and light_data.type not in {"POINT", "SPOT"}:
            logger.error(f"Automatic lights must be a Point or Spot light, change {self.blenderObject.name}'s type or change it's X-Plane Light Type")
            return
        elif self.lightType == LIGHT_AUTOMATIC and parsed_light and parsed_light.light_param_def:
            self.is_omni = light_data.type == "POINT"
            #"CELL_", "DAY", "DREF" are never parameterizable,
            #"DX", "DY", "DZ" cannot be filled in until later
            convert_table = {
                    "R":self.color[0],
                    "G":self.color[1],
                    "B":self.color[2],
                    #TODO: HACK. If Ben and Alex decide they want the "INDEX" name kept in
                    # lights.txt we'll make an entry in the dict. Else, we'll keep this or whatever
                    # solution we have
                    "A":light_data.xplane.param_index if parsed_light.has_index() else 1,
                    "SIZE":light_data.shadow_soft_size, # Radius
                    "WIDTH": math.cos(round(math.degrees(light_data.spot_size)) if light_data.type == "POINT" else 1,
                    "FREQ": light_data.xplane.param_freq,
                    "PHASE": light_data.xplane.param_phase,
                    "AMP": light_data.xplane.param_amp,
                }

            if "WIDTH" in parsed_light.light_param_def and round(light_data.spot_size) == math.pi:
                logger.error("Spotlight Size for {self.blenderObject.name} cannot be 180 degrees")
                return

            for i, arg in filter(lambda arg: isinstance(arg, str), parsed_light.overloads[0]):
                parsed_light.overloads[arg] = convert_table[arg]
        elif self.lightType == LIGHT_AUTOMATIC and parsed_light and not parsed_light.light_param_def:
            # Like LIGHT_NAMED but no autocorrection
            pass
        elif self.lightType == LIGHT_AUTOMATIC and not parsed_light:
            logger.warn(unknown_light_name_warning)
        # X-Plane Light Type | Light Type | parsed_light | light_param_defs | Result
        # -------------------|------------|--------------|------------------|-------
        # LIGHT_ old         | *          | N/A          | N/A              | Write
        elif self.lightType in LIGHTS_OLD_TYPES:
            pass
        else:
            assert False, f"{self.blenderObject.name} had some property configuation that was unaccounted for"

    def clamp(self, num:float, minimum:float, maximum:float)->float:
        if num < minimum:
            num = minimum
        elif num > maximum:
            num = maximum
        return num

    def write(self)->None:
        debug = getDebug()
        indent = self.xplaneBone.getIndent()
        o = super().write()

        light_data = self.blenderObject.data
        bakeMatrix = self.xplaneBone.getBakeMatrixForAttached()
        translation = bakeMatrix.to_translation()
        has_anim = False

        if (light_data.type != 'POINT'
            and self.lightType != LIGHT_AUTOMATIC
            and self.params_completed):
            # Vector P(arameters), in Blender Space
            try:
                (dx,dy,dz) = (self.params_completed[c] for c in ["DX", "DY", "DZ"])
            except KeyError:
                pass
            else:
                dir_vec_p_norm_b = vec_x_to_b(Vector((dx,dy,dz)).normalized())

                # Multiple bake matrix by Vector to get the direction of the Blender object
                dir_vec_b_norm = bakeMatrix.to_3x3() @ Vector((0,0,-1))

                # P is start rotation, and B is stop. As such, we have our axis of rotation.
                # "We take the X-Plane light and turn it until it matches what the artist wanted"
                axis_angle_vec3 = dir_vec_p_norm_b.cross(dir_vec_b_norm)

                dot_product_p_b = dir_vec_p_norm_b.dot(dir_vec_b_norm)

                if dot_product_p_b < 0:
                    axis_angle_theta = math.pi - math.asin(self.clamp(axis_angle_vec3.magnitude,-1.0,1.0))
                else:
                    axis_angle_theta = math.asin(self.clamp(axis_angle_vec3.magnitude,-1.0,1.0))

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
                    o += "%sANIM_begin\n" % indent

                    if debug:
                        o += indent + '# static rotation\n'

                    axis_angle_vec3_x = vec_b_to_x(axis_angle_vec3).normalized()
                    anim_rotate_dir =  indent + 'ANIM_rotate\t%s\t%s\t%s\t%s\t%s\n' % (
                        floatToStr(axis_angle_vec3_x[0]),
                        floatToStr(axis_angle_vec3_x[1]),
                        floatToStr(axis_angle_vec3_x[2]),
                        floatToStr(math.degrees(axis_angle_theta)), floatToStr(math.degrees(axis_angle_theta))
                    )
                    o += anim_rotate_dir

                    rot_matrix = mathutils.Matrix.Rotation(axis_angle_theta,4,axis_angle_vec3)
                    translation = rot_matrix.inverted() @ translation
                    has_anim = True
        elif (light_data.type == 'SPOT'
              and self.lightType == LIGHT_AUTOMATIC
              and self.params_completed):
            (dx,dy,dz) = vec_b_to_x(bakeMatrix.to_quaternion().to_axis_angle()[0])[:]
            try:
                self.params_completed.arguments["DX"] = dx
                self.params_completed.arguments["DY"] = dy
                self.params_completed.arguments["DZ"] = dz
            except KeyError:
                pass

        x,y,z = list(map(floatToStr,(translation[0],translation[2],-translation[1])))
        light_param_def = xplane_lights_txt_parser.get_parsed_light(self.lightName).light_param_def
        if (self.lightType == LIGHT_NAMED
            or (self.lightType == LIGHT_AUTOMATIC and not light_param_def)):
            o += f"{indent}LIGHT_NAMED\t{self.lightName} {x} {y} {z}\n"
        elif (self.lightType == LIGHT_PARAM
              or (self.lightType == LIGHT_AUTOMATIC and light_param_def)):
            o += f"{indent}LIGHT_PARAM\t{self.lightName} {x} {y} {z} {' '.join(self.params_completed)}\n"
        elif self.lightType == LIGHT_CUSTOM:
            o += (f"{indent}LIGHT_CUSTOM\t{x} {y} {z}"
                 f" {' '.join(self.color)} {self.energy} {self.size}"
                 f" {' '.join(self.uv)} {self.dataref}\n")
        # do not render lights with no indices
        elif self.indices[1] > self.indices[0]:
            offset = self.indices[0]
            count = self.indices[1] - self.indices[0]
            o += f"{indent}LIGHTS\t{offset} {count}\n"

        if has_anim:
            o += "{indent}ANIM_end\n"

        return o
