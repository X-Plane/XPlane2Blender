from .xplane_object import XPlaneObject
from ..xplane_helpers import floatToStr, FLOAT_PRECISION, logger
from ..xplane_constants import *
from ..xplane_config import getDebug
import math
import mathutils

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

        bakeMatrix = self.xplaneBone.getBakeMatrixForAttached()
		
        if self.lightName == 'airplane_landing_sp':
            print (bakeMatrix)
            r = mathutils.Euler((math.radians(-90.0),0,0),'XYZ')
            print (r)
            bakeMatrix = bakeMatrix * r.to_matrix().to_4x4()
            print (bakeMatrix)
		
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
