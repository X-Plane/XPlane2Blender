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

test_param_lights = {
    # NAMED LIGHTS
    # Spill version
    'taillight' : ((),('0.4','0.05','0','0.8','3','0','-0.5','0.86','0.0','0')),
    
    # PARAMETER LIGHTS
    'airplane_nav_left_size':(('SIZE','FOCUS'), 
        ('FOCUS','0','0','1','SIZE','1','7','7','0','0','0','1','sim/graphics/animation/lights/airplane_navigation_light_dir')),

    'airplane_nav_right_size':(('SIZE','FOCUS'), 
        ('FOCUS','0','0','1','SIZE','1','6','7','0','0','0','1','sim/graphics/animation/lights/airplane_navigation_light_dir')),

    'area_lt_param_sp': (('DX','DY','DZ','THROW'),
                         ('0.85', '0.75', '1.0', '0.6','THROW','DX', 'DY', 'DZ', '0.3', '0')),

    'full_custom_halo': (('R','G','B','A','S','X','Y','Z','F'),
                         ('R', 'G', 'B', 'A', 'S','X','Y','Z','F','1')),

    'helipad_flood_sp': (('BRIGHT', 'THROW', 'X', 'Y', 'Z', 'FOCUS'),
                         ('0.996', '0.945', '0.882', 'BRIGHT', 'THROW', 'X', 'Y', 'Z', 'FOCUS', '0')),

    'helipad_flood_bb': (('X', 'Y', 'Z', 'WIDTH'),
                         ('1', '1', '1', '0.5', '1', '2', '6', 'X', 'Y', 'Z', 'WIDTH', '0', '0', '0', '0')),

    'spot_params_sp':   (('R','G','B','BRIGHT','THROW','X','Y','Z','FOCUS'),
                         ('R','G','B','BRIGHT','THROW','X','Y','Z','FOCUS')),

    'spot_params_bb':   (('R','G','B','SIZE','X','Y','Z','WIDTH'),
                         ('R', 'G', 'B', '1.0', 'SIZE',  '2',  '5',  '2', 'X', 'Y', 'Z', 'WIDTH',  '0',  '0',  '0',  '0')),

    'radio_obs_flash':  (('X','Y','Z'),
                         ('1', '0.8', '0.8', '1', '1.5', '1', '4', '5', 'X', 'Y', 'Z', '0.5', '0.25', '0', '1.5', '1'))
}

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
        self.color = [blenderObject.data.color[0], blenderObject.data.color[1], blenderObject.data.color[2]]
        self.energy = blenderObject.data.energy
        self.type = XPLANE_OBJECT_TYPE_LIGHT
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
        xplane_lights_txt_parser.parse_lights_file()
        
        def is_number(number_str):
            try:
                float(number_str)
            except:
                return False
            else:
                return True

        self.lightOverload = parsed_lights[self.lightName]
        if self.lightName == LIGHT_NAMED:
            pass
        elif self.lightType == LIGHT_PARAM:
            params_formal = self.lightOverload.light_param_def.prototype
            params_actual = re.findall(r" *[^ ]*",self.params)
            del params_actual[-1] #'' will always be the last match in the group
            
            if len(params_actual) > len(params_formal):
                self.comment = (''.join(params_actual[len(params_formal):])).lstrip()
                if not (self.comment.startswith("//") or self.comment.startswith("#")):
                    logger.warn("Comment in param light %s does not start with '//' or '#'" % self.comment)
            
            params_actual = [p.strip() for p in params_actual]
            
            if len(params_actual) < len(params_formal):
                logger.error("Not enough actual parameters (%s) to satisfy LIGHT_PARAM_DEF %s" % (' '.join(params_actual),' '.join(params_formal)))
            
            params_actual = params_actual[0:len(params_formal)]
            for i,param in enumerate(params_actual):
                if is_number(param):
                    self.lightOverload.light_param_def.user_values[i] = float(param) 
                else:
                    logger.error("Parameter %s is not a number" % param)
                    return

            self.lightOverload.finalize_data()
            (dx,dy,dz) = (self.lightOverload.get("DX"),self.lightOverload.get("DY"),self.lightOverload.get("DZ"))
            
            if not None in (dx,dy,dz) and\
                Vector([float(d) for d in (dx,dy,dz)]).magnitude == 0.0 and self.is_omni is False: 
                logger.error("Non-omni light cannot have (0.0,0.0,0.0) for direction")
             
            self.is_omni = float(self.lightOverload.get("WIDTH")) >= 1.0
           
            if logger.hasErrors():
                return

        elif self.lightName not in parsed_lights:
            logger.warn("Light name %s is not a known light name, no autocorrection will occur. Check spelling or updates to lights.txt" % self.lightName)

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
        elif self.blenderObject.data.type != 'POINT' and\
            self.lightType == xplane_constants.LIGHT_PARAM and\
            self.lightName in test_param_lights:
            
            # Vector P(arameters), in Blender Space
            dx = self.parsed_params["X"] if self.parsed_params["X"] != None else self.parsed_params["DX"]
            dy = self.parsed_params["Y"] if self.parsed_params["Y"] != None else self.parsed_params["DY"]
            dz = self.parsed_params["Z"] if self.parsed_params["Z"] != None else self.parsed_params["DZ"]
            
            assert dx is not None and dy is not None and dz is not None
            
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
