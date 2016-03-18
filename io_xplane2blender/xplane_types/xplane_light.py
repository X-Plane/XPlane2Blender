from .xplane_object import XPlaneObject
from ..xplane_helpers import floatToStr
from ..xplane_constants import *

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

    def write(self):
        indent = self.xplaneBone.getIndent()
        o = super(XPlaneLight, self).write()

        bakeMatrix = self.xplaneBone.getBakeMatrixForAttached()

        translation = bakeMatrix.to_translation()
		# TODO: the bake matrix may have a rotation component.
		# in this case we need to emit static rotations to get the light
		# pointing in the right direction.
		#
		# Ideally we'd know whether the light has some kind of symetry (E.g.
		# axial around a given axis for Z or omni) and throw out unnecessary
		# transforms, since they are toxic to instancing.

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

        return o
