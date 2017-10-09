from .xplane_object import XPlaneObject
from ..xplane_helpers import floatToStr, FLOAT_PRECISION, logger
from ..xplane_constants import *
from ..xplane_config import getDebug
import math
import mathutils
from mathutils import Vector, Matrix, Euler

#### BEN NEEDS TO DOC THIS LATER

def vec_b_to_x(v):
    return Vector((v.x, v.z, -v.y))

def vec_x_to_b(v):
    return Vector((v.x, -v.z, v.y))

def basis_for_dir(neg_z_axis):
    m = Matrix.Identity(3)
    z_axis = -neg_z_axis
    if z_axis.x == 0.0 and z_axis.y == 0.0:
        if z_axis.z > 0:
            x_axis = Vector((1,0,0))
            y_axis = Vector((0,1,0))
        else:
            x_axis = Vector((-1,0,0))
            y_axis = Vector((0,1,0))
    else:
        more_or_less_x = ((1,0,0))
        y_axis = z_axis.cross(more_or_less_x)
        x_axis = y_axis.cross(z_axis)
    m[0] = x_axis
    m[1] = y_axis
    m[2] = z_axis
    return m


####




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

    # COPY PASTA WARNING!!!
    #
    # This is stolen from the bone code's bake matrix exporter.  I wanted this copied out
    # to 1. avoid re-test late in beta and 2. to have the option to optimize this later
    # for lights that can have direction vectors.

    def _writeStaticRotationForLight(self, bakeMatrix):
        debug = getDebug()
        indent = self.xplaneBone.getIndent()
        o = ''
        bakeMatrix = bakeMatrix
        rotation = bakeMatrix.to_euler('XYZ')
        rotation[0] = round(rotation[0],5)
        rotation[1] = round(rotation[1],5)
        rotation[2] = round(rotation[2],5)
        
        # ignore noop rotations
        if rotation[0] == 0 and rotation[1] == 0 and rotation[2] == 0:
            return o

        if debug:
            o += indent + '# static rotation\n'

		# Ben says: this is SLIGHTLY counter-intuitive...Blender axes are
		# globally applied in a Euler, so in our XYZ, X is affected -by- Y
		# and both are affected by Z.
		#
		# Since X-Plane works opposite this, we are going to apply the
		# animations exactly BACKWARD! ZYX.  The order here must
		# be opposite the decomposition order above.
		#
		# Note that since our axis naming is ALSO different this will
		# appear in the OBJ file as Y -Z X.
		#
		# see also: http://hacksoflife.blogspot.com/2015/11/blender-notepad-eulers.html

        axes = (2, 1, 0)
        eulerAxes = [(0.0,0.0,1.0),(0.0,1.0,0.0),(1.0,0.0,0.0)]
        i = 0

        for axis in eulerAxes:
            deg = math.degrees(rotation[axes[i]])

            # ignore zero rotation
            if not deg == 0:
                o += indent + 'ANIM_rotate\t%s\t%s\t%s\t%s\t%s\n' % (
                    floatToStr(axis[0]),
                    floatToStr(axis[2]),
                    floatToStr(-axis[1]),
                    floatToStr(deg), floatToStr(deg)
                )

            i += 1

        return o

    def write(self):
        indent = self.xplaneBone.getIndent()
        o = super(XPlaneLight, self).write()

        test_param_lights = {
            # NAMED LIGHTS
            #Spill version
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

        bakeMatrix = self.xplaneBone.getBakeMatrixForAttached()
        if self.blenderObject.data.type == 'POINT':
            translation = bakeMatrix.to_translation()
            has_anim = False
        elif self.blenderObject.data.type != 'POINT':

            fixed_lights = {
                'airplane_landing_sp': (0.0, 0.0,-1.0),
                'headlight'          : (0.0, 0.0,-1.0),
                'taillight'          : (0.0, 0.0, 1.0),
                'taxi_b'             : (0.0,-1.0, 0.0),
                'taxi_r'             : (0.0,-1.0, 0.0),
                'full_custom_halo'   : (0.0,-1.0, 0.0)
                }

            if  round(self.blenderObject.rotation_euler[0],5) == 0.00 and \
                round(self.blenderObject.rotation_euler[1],5) == 0.00 and \
                round(self.blenderObject.rotation_euler[2],5) == 0.00:
                rot_vec_norm = Vector((0,0,0))
            else:
                rot_vec_norm = Vector(self.blenderObject.rotation_euler[:3]).normalized()

            b = basis_for_dir(vec_x_to_b(rot_vec_norm))

            bakeMatrix = bakeMatrix * b.to_4x4()

            translation = bakeMatrix.to_translation()
            rotation = bakeMatrix.to_euler('XYZ')
            
            rotation[0] = round(rotation[0],5)
            rotation[1] = round(rotation[1],5)
            rotation[2] = round(rotation[2],5)
            
            has_anim = False
        
            # Ben says: lights always have some kind of offset because the light itself
            # is "at" 0,0,0, so we treat the translation as the light position.
            # But if there is a ROTATION then in the light's bake matrix, the
            # translation is pre-rotation.  but we want to write a single static rotation
            # and then NOT write a translation every time.
            #
            # Soooo... we write a bake matrix and then we transform the translation by the
            # inverse to change our animation order (so we really have rot, trans when we
            # originally had trans, rot) and now we can use the translation in the lamp
            # itself.
            
            if rotation[0] != 0.0 or rotation[1] != 0.0 or rotation[2] != 0.0:
                rot_matrix = rotation.to_matrix().to_4x4()
                o += "%sANIM_begin\n" % indent
                o += self._writeStaticRotationForLight(rot_matrix)
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
