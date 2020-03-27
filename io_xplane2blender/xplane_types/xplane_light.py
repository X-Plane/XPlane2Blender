import math
import re
from copy import deepcopy
from itertools import zip_longest
from typing import List, Optional

import bpy
import mathutils
from mathutils import Euler, Matrix, Vector

from io_xplane2blender import xplane_constants, xplane_utils, xplane_types
from io_xplane2blender.xplane_types import xplane_object

from ..xplane_config import getDebug
from ..xplane_constants import *
from ..xplane_helpers import FLOAT_PRECISION, floatToStr, logger


class XPlaneLight(xplane_object.XPlaneObject):
    def __init__(self, blenderObject:bpy.types.Object):
        super().__init__(blenderObject)
        self.indices = [0,0]
        if blenderObject.data.xplane.enable_rgb_override:
            self.color = blenderObject.data.xplane.rgb_override_values[:]
        else:
            self.color = list(blenderObject.data.color[:])

        self.energy = blenderObject.data.energy
        self.lightType = blenderObject.data.xplane.type
        self.size = blenderObject.data.xplane.size
        self.lightName = blenderObject.data.xplane.name
        self.params = blenderObject.data.xplane.params

        # The combinination of lights.txt overload, filled in params,
        # and applied sw_light_callback
        self.params_completed:Optional[xplane_utils.xplane_lights_txt_parser.ParsedLightOverload] = None

        self.comment = None

        self.is_omni = False
        self.uv = blenderObject.data.xplane.uv
        self.dataref = blenderObject.data.xplane.dataref

        # change color according to type
        if self.lightType == LIGHT_FLASHING:
            self.color[0] = -self.color[0]
        elif self.lightType == LIGHT_PULSING:
            self.color[:] = 9.9
        elif self.lightType == LIGHT_STROBE:
            self.color[:] = 9.8
        elif self.lightType == LIGHT_TRAFFIC:
            self.color[:] = 9.7

        self.setWeight(10000)

    def collect(self)->None:
        super().collect()

        if self.lightType != LIGHT_CUSTOM:
            try:
                parsed_light = xplane_utils.xplane_lights_txt_parser.get_parsed_light(self.lightName)
            except KeyError:
                if parsed_light in {LIGHT_NAMED,LIGHT_PARAM}:
                    logger.warn(
                        f"Light name {self.lightName} is not a known light name, no autocorrection will occur. "
                        f"Check spelling or update lights.txt"
                    )

        if self.lightType == LIGHT_NAMED and parsed_light:
            if parsed_light.light_param_def:
                logger.error("light name %s is a known param light, being used as a name light. Check the light name or light type" % self.lightName)
                return

            if parsed_light.overloads[0].overload_type in {"BILLBOARD_SW", "SPILL_SW"}:
                self.params_completed = parsed_light.overloads[0]
                self.params_completed.apply_sw_callback()
        elif self.lightType == LIGHT_PARAM and parsed_light:
            if not parsed_light.light_param_def:
                logger.error(f"Light name {self.lightName} appears to be known as a named light, not a param light."
                             f" Check the light type drop down menu")
                return

            params_formal = parsed_light.light_param_def
            params_actual = re.findall(r" *[^ ]*",self.params)[:-1]

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
            for i, (pformal, pactual) in enumerate(zip(params_formal, params_actual)):
                try:
                    self.params_completed[pformal] = float(pactual)
                except (ValueError, TypeError):
                    logger.error(f"Parameter {i} ({pactual}) of {self.blenderObject.name} is not a number")
                    return

            if parsed_light.overloads[0].overload_type in {"BILLBOARD_SW", "SPILL_SW"}:
                self.params_completed.apply()

            is_omni = self.params_completed["WIDTH"] >= 1.0
            dir_vec = Vector(map(self.params_completed.__getitem__, ["DX","DY","DZ"]))
            #TODO: This aught to have rounding?
            if dir_vec.magnitude == 0.0 and not is_omni:
                logger.error("Non-omni light cannot have (0.0,0.0,0.0) for direction")
                return

        elif self.lightType == LIGHT_PARAM and not parsed_light:
            if len(self.params.split()) == 0:
                logger.error("light name %s has an empty parameters box" % self.lightName)
                return
        elif self.lightType == LIGHT_AUTOMATIC:
            parsed_light = xplane_utils.xplane_lights_txt_parser.get_parsed_light(self.lightName)
            if parsed_light.light_param_def:
                light_overload_filled_in = parsed_light.overloads[0]
                def isfloat(f):
                    try:
                        float(f)
                        return True
                    except:
                        return False

                light = self.blenderObject.data
                width = round(math.degrees(light.spot_size), 5) if light.spot_size < math.pi else 1.0
                convert_table = {
                        "R":self.color[0],
                        "B":self.color[1],
                        "G":self.color[2],
                        "A":1,
                        "W":width,
                        "WIDTH": width,
                        "F":     width,
                        "FOCUS": width,
                        "INDEX": light.xplane.param_index,
                        "FREQ":  light.xplane.param_freq,
                }
                self.params = " ".join(parsed_light.overloads[0].overload_arguments)

                def tofloat(f):
                    try:
                        float(f)
                        return True
                    except:
                        return False

                for i, arg in filter(lambda arg: not tofloat(arg[1]), enumerate(parsed_light.overloads[0].overload_arguments)):
                    #TODO: This isn't good. Doesn't account for 1st, 2nd, instance. Finding W in Width
                    print(i, arg)
                    print("Before:", self.params)
                    try:
                        self.params = self.params.replace(arg, str(convert_table[arg]))
                    except KeyError:
                        print("KEY ERROR!", arg)
                        self.params.replace(arg, "NotImplementedYet")

                    print("After: ", self.params)

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

        bakeMatrix = self.xplaneBone.getBakeMatrixForAttached()
        translation = bakeMatrix.to_translation()
        has_anim = False

        def vec_b_to_x(v):
            return Vector((v.x, v.z, -v.y))

        def vec_x_to_b(v):
            return Vector((v.x, -v.z, v.y))

        if self.blenderObject.data.type == 'POINT':
            pass
        elif self.blenderObject.data.type != 'POINT' and self.lightOverload is not None:
            # Vector P(arameters), in Blender Space
            (dx,dy,dz) = (self.lightOverload.get("DX"),self.lightOverload.get("DY"),self.lightOverload.get("DZ"))
            if dx is not None and dy is not None and dz is not None:
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

                translation = bakeMatrix.to_translation()

                # Ben says: lights always have some kind of offset because the light itself
                # is "at" 0,0,0, so we treat the translation as the light position.
                # But if there is a ROTATION then in the light's bake matrix, the
                # translation is pre-rotation.  but we want to write a single static rotation
                # and then NOT write a translation every time.
                #
                # Inverse to change our animation order (so we really have rot, trans when we
                # originally had trans, rot) and now we can use the translation in the lamp
                # itself.
                if round(axis_angle_theta,5) != 0.0 and self.is_omni is False:
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

        x,y,z = list(map(floatToStr,(translation[0],translation[2],-translation[1])))
        if self.lightType == LIGHT_NAMED:
            o += f"{indent}LIGHT_NAMED\t{self.lightName} {x} {y} {z}\n"
        elif self.lightType == LIGHT_PARAM or self.lightType == LIGHT_AUTOMATIC:
            o += f"{indent}LIGHT_PARAM\t{self.lightName} {x} {y} {z} {self.params}\n"
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
