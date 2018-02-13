import collections
import math
import sys

import bpy
from mathutils import Vector

from .xplane_attribute import XPlaneAttribute
from .xplane_manipulator import XPlaneManipulator
from .xplane_material import XPlaneMaterial
from .xplane_object import XPlaneObject

from ..xplane_config import getDebug
from ..xplane_constants import *
from ..xplane_helpers import logger

from io_xplane2blender import xplane_helpers
from io_xplane2blender.xplane_constants import MANIP_DRAG_AXIS_DETENT,\
    MANIP_DRAG_ROTATE_DETENT
from io_xplane2blender.xplane_types import xplane_manipulator

# Class: XPlanePrimitive
# A Mesh object.
#
# Extends:
#   <XPlaneObject>
class XPlanePrimitive(XPlaneObject):
    # Property: indices
    # list - [start,end] Starting end ending indices for this object.

    # Property: material
    # XPlaneMaterial - A <XPlaneMaterial>

    # Property: faces
    # XPlaneFaces - Instance of <XPlaneFaces> with all face of this mesh. Currently not in use. This should be used when commands will work on a per face basis.

    # Property: attributes
    # dict - Object attributes that will be turned into commands with <XPlaneCommands>.

    # Property: cockpitAttributes
    # dict - Object attributes for cockpit settings, that will be turned into commands with <XPlaneCommands>.

    # Constructor: __init__
    # Defines basic <attributes> and <cockpitAttributes>, Creates <material>, runs <getManipulatorAttributes>, <getLightLevelAttributes>, <XPlaneObject.getCoordinates> and <XPlaneObject.getAnimations>.
    #
    # Parameters:
    #   blenderObject - A Blender object
    def __init__(self, blenderObject):
        super(XPlanePrimitive, self).__init__(blenderObject)
        self.type = XPLANE_OBJECT_TYPE_PRIMITIVE
        self.indices = [0, 0]
        self.material = XPlaneMaterial(self)
        self.manipulator = XPlaneManipulator(self)

        #TODO: If it is currently unused, then maybe we shouldn't have it!
        # To qoute: "You aren't going to need it!
        self.faces = None 

        self.getWeight()

    def getWeight(self, defaultWeight = 0):
        super(XPlanePrimitive, self).getWeight(defaultWeight)

        if not hasattr(self.blenderObject.xplane, 'override_weight') or not self.blenderObject.xplane.override_weight:
            mat_weight = 0

            for i in range(0, len(bpy.data.materials)):
                if len(self.blenderObject.data.materials) > 0 and self.blenderObject.data.materials[0] == bpy.data.materials[i]:
                    mat_weight = i

            self.weight += mat_weight

    def collect(self):
        super(XPlanePrimitive, self).collect()

        # add manipulator attributes
        self.manipulator.collect()

        # need reordering again as manipulator attributes may have been added
        self.cockpitAttributes.order()

        if self.material:
            self.material.collect()

    def write(self):
        debug = getDebug()
        indent = self.xplaneBone.getIndent()
        o = ''

        xplaneFile = self.xplaneBone.xplaneFile
        commands =  xplaneFile.commands

        if debug:
            o += "%s# %s: %s\tweight: %d\n" % (indent, self.type, self.name, self.weight)

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
                if  manip.get_effective_type_id() == MANIP_DRAG_AXIS_DETENT or\
                    manip.get_effective_type_id() == MANIP_DRAG_ROTATE or\
                    manip.get_effective_type_id() == MANIP_DRAG_ROTATE_DETENT:
                    if not xplane_manipulator.check_bone_is_leaf(self.xplaneBone):
                        return ''

            for attr in self.cockpitAttributes:
                o += commands.writeAttribute(self.cockpitAttributes[attr], self)

        if self.indices[1] > self.indices[0]:
            offset = self.indices[0]
            count = self.indices[1] - self.indices[0]
            o += "%sTRIS\t%d %d\n" % (indent, offset, count)

        return o
