from ..xplane_helpers import floatToStr

# Class: XPlaneLights
# Creates OBJ lights.
class XPlaneLights():
    items = []

    # Property: lines
    # list - All lines.
    lines = []

    # Property: indices
    # list - All light indices.
    indices = []

    # Property: globalindex
    # int - Current global light index.
    globalindex = 0

    # Constructor: __init__
    #
    # Parameters:
    #   dict file - A file dict coming from <XPlaneData>
    def __init__(self):
        self.items = []
        self.lines = []
        self.indices = []
        self.globalindex = 0

    def append(self, light):
        self.items.append(light)
        light.indices[0] = self.globalindex

        # we only write vlights here, all other lights go into the commands table directly
        if  light.lightType not in ('named','param','custom'):
            # get the location
            co = light.blenderObject.location

            self.lines.append("VLIGHT\t%s\t%s\t%s\t%s\t%s\t%s" % (
                floatToStr(co[0]), floatToStr(co[1]), floatToStr(co[2]),
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
