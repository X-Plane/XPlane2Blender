import math
import re

from .xplane_object import XPlaneObject
from ..xplane_helpers import floatToStr, FLOAT_PRECISION, logger
from ..xplane_constants import *
from ..xplane_config import getDebug
import mathutils
from mathutils import Vector, Matrix, Euler
from itertools import zip_longest
from io_xplane2blender import xplane_constants
from io_xplane2blender.xplane_types.xplane_lights_txt_parser import *
from io_xplane2blender.xplane_types import xplane_lights_txt_parser
from copy import deepcopy
from typing import List, Optional


# Class: XPlaneLight
# A Light
#
# Extends:
#   <XPlaneObject>
class XPlaneLight(XPlaneObject):
    # Property: indices
    # list - [start,end] Starting end ending indices for this light.

    # Property: color
    # list - [r,g,b] Color taken from the original Blender light. Can change depending on <lightType>.

    # Property: energy
    # float - Energy taken from Blender light.

    # Property: lightType
    # string - Type of the light taken from <XPlaneLampSettings>.

    # Property: size
    # float - Size of the light taken from <XPlaneLampSettings>.

    # Property: lightName
    # string - Name of the light taken from <XPlaneLampSettings>.

    # Property: params
    # string - Parameters taken from <XPlaneLampSettings>.

    # Property: dataref
    # string - Dataref path taken from <XPlaneLampSettings>.

    # Constructor: __init__
    #
    # Parameters:
    #   object - A Blender object
    def __init__(self, blenderObject):
        super(XPlaneLight, self).__init__(blenderObject)
        self.indices = [0,0]
        if blenderObject.data.xplane.enable_rgb_override:
            self.color = blenderObject.data.xplane.rgb_override_values[:]
        else:
            self.color = blenderObject.data.color[:]
        
        self.energy = blenderObject.data.energy
        self.lightType = blenderObject.data.xplane.type
        self.size = blenderObject.data.xplane.size
        self.lightName = blenderObject.data.xplane.name
        self.params = blenderObject.data.xplane.params
        
        self.lightOverload = None
        
        self.comment = None

        self.is_omni = False
        self.uv = blenderObject.data.xplane.uv
        self.dataref = blenderObject.data.xplane.dataref

        # change color according to type
        if self.lightType == LIGHT_FLASHING:
            self.color[0] = -self.color[0]
        elif self.lightType == LIGHT_PULSING:
            self.color[0] = 9.9
            self.color[1] = 9.9
            self.color[2] = 9.9
        elif self.lightType == LIGHT_STROBE:
            self.color[0] = 9.8
            self.color[1] = 9.8
            self.color[2] = 9.8
        elif self.lightType == LIGHT_TRAFFIC:
            self.color[0] = 9.7
            self.color[1] = 9.7
            self.color[2] = 9.7

        self.getWeight(10000)

    def collect(self):
        super().collect()

        is_parsed = xplane_lights_txt_parser.parse_lights_file()
        if is_parsed == False:
            logger.error("lights.txt file could not be parsed")
            return

        if self.lightType != LIGHT_CUSTOM:
            self.lightOverload = xplane_lights_txt_parser.get_overload(self.lightName)
        else:
            self.lightOverload = None

        if self.lightOverload is None and (self.lightType == LIGHT_NAMED or self.lightType == LIGHT_PARAM):
            logger.warn("Light name %s is not a known light name, no autocorrection will occur. Check spelling or update lights.txt" % self.lightName)

        if self.lightType == LIGHT_NAMED and self.lightOverload is not None:
            if self.lightOverload.is_param_light():
                logger.error("light name %s is a known param light, being used as a name light. Check the light name or light type" % self.lightName)
                return

            if self.lightOverload.get("DREF") is not None:
                self.lightOverload.apply_sw_light_callback()
        elif self.lightType == LIGHT_PARAM and self.lightOverload is not None:

            if self.lightOverload.is_param_light() is False:
                logger.error("Light name %s appears to be known as a named light, not a param light."
                             "Check the light type drop down menu" % self.lightName)
                return

            params_formal = self.lightOverload.light_param_def.prototype
            params_actual = re.findall(r" *[^ ]*",self.params)[:-1]
            
            if len(params_actual) < len(params_formal):
                logger.error("Not enough actual parameters (%s) to satisfy LIGHT_PARAM_DEF %s" % (' '.join(params_actual),' '.join(params_formal)))
                return

            if len(params_actual) > len(params_formal):
                self.comment = (''.join(params_actual[len(params_formal):])).lstrip()
                if not (self.comment.startswith("//") or self.comment.startswith("#")):
                    logger.warn("Comment in param light %s does not start with '//' or '#'" % self.comment)
            

            params_actual = [p.strip() for p in params_actual[0:len(params_formal)]]
            user_values   = [None]*len(params_actual) # type: List[Optional[float]]
            for i,param in enumerate(params_actual):
                def isfloat(number_str):
                    try:
                        val = float(number_str)
                    except:
                        return False
                    else:
                        return True
                if isfloat(param):
                    user_values[i] = float(param) 
                else:
                    logger.error("Parameter %s (%s) is not a number" % (i,param))
                    return

            self.lightOverload.bake_user_values(user_values)

            self.is_omni = float(self.lightOverload.get("WIDTH")) >= 1.0
            dir_vec = Vector((self.lightOverload.get("DX"),self.lightOverload.get("DY"),self.lightOverload.get("DZ")))
            if dir_vec.magnitude == 0.0 and self.is_omni is False: 
                logger.error("Non-omni light cannot have (0.0,0.0,0.0) for direction")
           
            if logger.hasErrors():
                return
        elif self.lightType == LIGHT_PARAM and self.lightOverload is None:
            if len(self.params.split()) == 0:
                logger.error("light name %s has an empty parameters box" % self.lightName)
                return

    def clamp(self, num, minimum, maximum):
        if num < minimum:
            num = minimum
        elif num > maximum:
            num = maximum
        return num

    def write(self):
        debug = getDebug()
        indent = self.xplaneBone.getIndent()
        o = super(XPlaneLight, self).write()

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
                dir_vec_b_norm = bakeMatrix.to_3x3() * Vector((0,0,-1))

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
                    translation = rot_matrix.inverted() * translation
                    has_anim = True

        if self.lightType == LIGHT_NAMED:
            o += "%sLIGHT_NAMED\t%s %s %s %s\n" % (
                indent, self.lightName,
                floatToStr(translation[0]),
                floatToStr(translation[2]),
                floatToStr(-translation[1])
            )
        elif self.lightType == LIGHT_PARAM:
            o += "%sLIGHT_PARAM\t%s %s %s %s %s\n" % (
                indent, self.lightName,
                floatToStr(translation[0]),
                floatToStr(translation[2]),
                floatToStr(-translation[1]),
                self.params
            )
        elif self.lightType == LIGHT_CUSTOM:
            o += "%sLIGHT_CUSTOM\t%s %s %s %s %s %s %s %s %s %s %s %s %s\n" % (
                indent,
                floatToStr(translation[0]),
                floatToStr(translation[2]),
                floatToStr(-translation[1]),
                floatToStr(self.color[0]),
                floatToStr(self.color[1]),
                floatToStr(self.color[2]),
                floatToStr(self.energy),
                floatToStr(self.size),
                floatToStr(self.uv[0]),
                floatToStr(self.uv[1]),
                floatToStr(self.uv[2]),
                floatToStr(self.uv[3]),
                self.dataref
            )

        # do not render lights with no indices
        elif self.indices[1] > self.indices[0]:
            offset = self.indices[0]
            count = self.indices[1] - self.indices[0]
            o += "%sLIGHTS\t%d %d\n" % (indent, offset, count)

        if has_anim:
            o += "%sANIM_end\n" % indent

        return o
