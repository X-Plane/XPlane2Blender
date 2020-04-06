from typing import List
from ..xplane_helpers import floatToStr
from ..xplane_constants import *
from io_xplane2blender.xplane_types import xplane_light

# TODO: deprecate someday...
class XPlaneLights():
    """
    Makes the VLIGHT table for all old LIGHT types (DEFAULT, FLASHING,
    STROBE, etc) ands writes it.

    The actual LIGHTS directive is written in xplane_light.write
    """

    def __init__(self)->None:
        # The XPlaneLights that will reference the VLIGHT table
        self.items:List[xplane_light.XPlaneLight] = []
        # The content of the VLIGHT table
        self.lines:List[str] = []
        # The indices of the VLIGHT table
        self.indices:List[int] = []
        # Current global light index.
        self.globalindex = 0

    def append(self, light:xplane_light.XPlaneLight)->None:
        # we only write vlights here, all other lights go into the commands table directly
        if light.lightType in LIGHTS_OLD_TYPES:
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

    def write(self)->str:
        """
        Returns the OBJ VLIGHT table
        """
        return "\n".join(self.lines)
