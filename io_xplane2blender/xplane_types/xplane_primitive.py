import collections
import math
import sys

import bpy
from io_xplane2blender import xplane_helpers
from io_xplane2blender.xplane_constants import (MANIP_DRAG_AXIS_DETENT,
                                                MANIP_DRAG_ROTATE_DETENT)
from io_xplane2blender.xplane_types import xplane_manipulator
from mathutils import Vector
from typing import Any

from ..xplane_config import getDebug
from ..xplane_constants import *
from ..xplane_helpers import logger
from .xplane_attribute import XPlaneAttribute
from .xplane_manipulator import XPlaneManipulator
from .xplane_material import XPlaneMaterial
from .xplane_object import XPlaneObject


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
        assert blenderObject.type == 'MESH'
        super(XPlanePrimitive, self).__init__(blenderObject)
        self.type = 'MESH'
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

    # Method: collectManipulatorAttributes
    # Defines Manipulator attributes in <cockpitAttributes> based on settings in <XPlaneManipulator>.
    def collectManipulatorAttributes(self):
        attr = 'ATTR_manip_'

        value = None # type: Tuple[Any]
        if self.blenderObject.xplane.manip.enabled:
            manip = self.blenderObject.xplane.manip
            xplane_version = int(bpy.context.scene.xplane.version)
            manipType = manip.type

            attr += manipType

            if manipType == MANIP_DRAG_XY:
                value = (
                    manip.cursor,
                    manip.dx,
                    manip.dy,
                    manip.v1_min,
                    manip.v1_max,
                    manip.v2_min,
                    manip.v2_max,
                    manip.dataref1,
                    manip.dataref2,
                    manip.tooltip
                )
            elif manipType == MANIP_DRAG_AXIS:
                value = (
                    manip.cursor,
                    manip.dx,
                    manip.dy,
                    manip.dz,
                    manip.v1,
                    manip.v2,
                    manip.dataref1,
                    manip.tooltip
                )
            elif manipType == MANIP_DRAG_AXIS_PIX:
                value = (
                    manip.cursor,
                    manip.dx,
                    manip.step,
                    manip.exp,
                    manip.v1,
                    manip.v2,
                    manip.dataref1,
                    manip.tooltip
                )
            elif manipType == MANIP_COMMAND:
                value = (manip.cursor, manip.command, manip.tooltip)
            elif manipType == MANIP_COMMAND_AXIS:
                value = (
                    manip.cursor,
                    manip.dx,
                    manip.dy,
                    manip.dz,
                    manip.positive_command,
                    manip.negative_command,
                    manip.tooltip
                )
            elif manipType in (MANIP_COMMAND_KNOB, MANIP_COMMAND_SWITCH_UP_DOWN, MANIP_COMMAND_SWITCH_LEFT_RIGHT):
                value = (
                    manip.cursor,
                    manip.positive_command,
                    manip.negative_command,
                    manip.tooltip
                )
            elif manipType == MANIP_PUSH:
                value = (
                    manip.cursor,
                    manip.v_down,
                    manip.v_up,
                    manip.dataref1,
                    manip.tooltip
                )
            elif manipType == MANIP_RADIO:
                value = (
                    manip.cursor,
                    manip.v_down,
                    manip.dataref1,
                    manip.tooltip
                )
            elif manipType == MANIP_TOGGLE:
                value = (
                    manip.cursor,
                    manip.v_on,
                    manip.v_off,
                    manip.dataref1,
                    manip.tooltip
                )
            elif manipType in (MANIP_DELTA, MANIP_WRAP):
                value = (
                    manip.cursor,
                    manip.v_down,
                    manip.v_hold,
                    manip.v1_min,
                    manip.v1_max,
                    manip.dataref1,
                    manip.tooltip
                )
            elif manipType in (MANIP_AXIS_SWITCH_UP_DOWN, MANIP_AXIS_SWITCH_LEFT_RIGHT):
                value = (
                    manip.cursor,
                    manip.v1,
                    manip.v2,
                    manip.click_step,
                    manip.hold_step,
                    manip.dataref1,
                    manip.tooltip
                )
            elif manipType == MANIP_NOOP:
                value = (
                    manip.dataref1,
                    manip.tooltip
                )

        else:
            attr = None

        if attr is not None:
            self.cockpitAttributes.add(XPlaneAttribute(attr, value))

            # add mouse wheel delta
            if manipType in MOUSE_WHEEL_MANIPULATORS and bpy.context.scene.xplane.version >= VERSION_1050 and manip.wheel_delta != 0:
                self.cockpitAttributes.add(XPlaneAttribute('ATTR_manip_wheel', manip.wheel_delta))

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
                if  manip.type == MANIP_DRAG_AXIS or\
                    manip.type == MANIP_DRAG_AXIS_DETENT or\
                    manip.type == MANIP_DRAG_ROTATE or\
                    manip.type == MANIP_DRAG_ROTATE_DETENT:
                    if not xplane_manipulator.check_bone_is_leaf(self.xplaneBone,True,self.manipulator):
                        return ''

            for attr in self.cockpitAttributes:
                o += commands.writeAttribute(self.cockpitAttributes[attr], self)

        if self.indices[1] > self.indices[0]:
            offset = self.indices[0]
            count = self.indices[1] - self.indices[0]
            o += "%sTRIS\t%d %d\n" % (indent, offset, count)

        return o
