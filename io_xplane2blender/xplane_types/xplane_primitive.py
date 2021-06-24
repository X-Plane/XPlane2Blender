import collections
import math
import sys
from typing import Any

import bpy
from mathutils import Vector

from io_xplane2blender import xplane_helpers
from io_xplane2blender.xplane_constants import (
    MANIP_DRAG_AXIS_DETENT,
    MANIP_DRAG_ROTATE_DETENT,
)
from io_xplane2blender.xplane_types import xplane_manipulator

from ..xplane_config import getDebug
from ..xplane_constants import *
from ..xplane_helpers import logger
from .xplane_attribute import XPlaneAttribute
from .xplane_manipulator import XPlaneManipulator
from .xplane_material import XPlaneMaterial
from .xplane_object import XPlaneObject


class XPlanePrimitive(XPlaneObject):
    """
    Used to represent Mesh objects and their XPlaneObjectSettings
    """

    def __init__(self, blenderObject: bpy.types.Object):
        assert blenderObject.type == "MESH"
        super().__init__(blenderObject)
        # Starting end ending indices for this object.
        self.indices = [0, 0]
        self.material = XPlaneMaterial(self)
        self.manipulator = XPlaneManipulator(self)
        self.setWeight()

    def setWeight(self, defaultWeight:int = 0)->None:
        """
        If not default, weight will 0 if no materials
        given, or it will be the index of the last matching material
        in the bpy.data.materials array + XPlaneObject's
        weight.
        """
        super().setWeight(defaultWeight)
        if self.blenderObject.xplane.override_weight:
            self.weight = self.blenderObject.xplane.weight
        else:
            try:
                ref_mat = self.blenderObject.data.materials[0]
                if ref_mat is None:
                    raise TypeError
            except (IndexError, TypeError):
                pass
            else:
                weight = 0
                for i, mat in enumerate(bpy.data.materials):
                    if ref_mat == mat:
                        weight = i
            self.weight += defaultWeight

    def collect(self) -> None:
        super().collect()

        # add manipulator attributes
        self.manipulator.collect()

        # need reordering again as manipulator attributes may have been added
        self.cockpitAttributes.order()

        if self.material:
            self.material.collect()

    def write(self) -> str:
        debug = getDebug()
        indent = self.xplaneBone.getIndent()
        o = ""

        xplaneFile = self.xplaneBone.xplaneFile
        commands = xplaneFile.commands

        if debug:
            o += "%s# %s: %s\tweight: %d\n" % (
                indent,
                self.type,
                self.name,
                self.weight,
            )

        o += commands.writeReseters(self)

        for attr in self.attributes:
            o += commands.writeAttribute(self.attributes[attr], self)

        # rendering (do not render meshes/objects with no indices)
        if self.indices[1] > self.indices[0]:
            o += self.material.write()

        # if the file is a cockpit file write all cockpit attributes
        if xplaneFile.options.export_type == EXPORT_TYPE_COCKPIT:
            if self.blenderObject.xplane.manip.enabled:
                manip = self.blenderObject.xplane.manip
                if (
                    manip.type == MANIP_DRAG_AXIS
                    or manip.type == MANIP_DRAG_AXIS_DETENT
                    or manip.type == MANIP_DRAG_ROTATE
                    or manip.type == MANIP_DRAG_ROTATE_DETENT
                ):
                    if not xplane_manipulator.check_bone_is_leaf(
                        self.xplaneBone, True, self.manipulator
                    ):
                        return ""

            for attr in self.cockpitAttributes:
                o += commands.writeAttribute(self.cockpitAttributes[attr], self)

        if self.indices[1] > self.indices[0]:
            offset = self.indices[0]
            count = self.indices[1] - self.indices[0]
            o += "%sTRIS\t%d %d\n" % (indent, offset, count)

        return o
