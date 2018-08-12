from ..xplane_helpers import floatToStr
from ..xplane_constants import *

# Class: XPlaneLights
# Creates OBJ lights.
# TODO: deprecate in v3.4
class XPlaneLights():
    # Constructor: __init__
    #
    # Parameters:
    #   dict file - A file dict coming from <XPlaneData>
    def __init__(self):
        self.items = []
        # list - All lines.
        self.lines = []
        # list - All light indices.
        self.indices = []
        # int - Current global light index.
        self.globalindex = 0

    def append(self, light):
        # we only write vlights here, all other lights go into the commands table directly
        if  light.lightType not in (LIGHT_NAMED, LIGHT_PARAM, LIGHT_CUSTOM):
            self.items.append(light)
            light.indices[0] = self.globalindex

            # get the location
            co = light.blenderObject.location

            self.lines.append("VLIGHT\t%s\t%s\t%s\t%s\t%s\t%s" % (
                floatToStr(co[0]), floatToStr(co[2]), floatToStr(-co[1]),
                floatToStr(light.color[0]), floatToStr(light.color[1]), floatToStr(light.color[2])
            ))
            self.indices.append(self.globalindex)
            self.globalindex += 1

            light.indices[1] = self.globalindex

    # Method: write
    # Returns the OBJ lights table by iterating <lines>.
    #
    # Returns:
    #   string - The OBJ lights table.
    def write(self):
        o= ''
        for l in self.lines:
            o += l + '\n'

        return o
