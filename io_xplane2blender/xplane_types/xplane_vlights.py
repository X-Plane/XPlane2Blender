from typing import List

import bpy

from io_xplane2blender.xplane_types import xplane_light

from ..xplane_constants import *
from ..xplane_helpers import floatToStr, vec_b_to_x


# TODO: deprecate someday...
class XPlaneVLights:
    """
    Makes the VLIGHT table for all old LIGHT types (DEFAULT, FLASHING,
    STROBE, etc) ands writes it.

    The actual LIGHTS directive is written in xplane_light.write
    """

    def __init__(self) -> None:
        # The XPlaneLights that will reference the VLIGHT table
        self.items: List[xplane_light.XPlaneLight] = []
        # The content of the VLIGHT table
        self.lines: List[str] = []
        # The indices of the VLIGHT table
        self.indices: List[int] = []
        # Current global light index.
        self.globalindex = 0

    def append(self, light: xplane_light.XPlaneLight) -> None:
        # we only write vlights here, all other lights go into the commands table directly
        if light.lightType in LIGHTS_OLD_TYPES:
            bpy.context.scene.frame_set(1)
            self.items.append(light)
            light.indices = [self.globalindex, self.globalindex + 1]
            self.indices.append(self.globalindex)
            self.globalindex += 1

            # get the location
            co = light.blenderObject.location

            tab = "\t"
            self.lines.append(
                f"VLIGHT"
                f"\t{tab.join(map(floatToStr, vec_b_to_x(co)))}"
                f"\t{tab.join(map(floatToStr, light.color))}"
                f"\n"
            )

    def write(self) -> str:
        """
        Returns the OBJ VLIGHT table
        """
        return "\n".join(self.lines)
