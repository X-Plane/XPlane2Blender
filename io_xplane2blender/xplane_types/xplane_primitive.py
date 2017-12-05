import math

import bpy
from .xplane_attribute import XPlaneAttribute
from .xplane_material import XPlaneMaterial
from .xplane_object import XPlaneObject
from ..xplane_config import getDebug
from ..xplane_constants import *
from ..xplane_helpers import logger
import io_xplane2blender.xplane_types

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
        self.collectManipulatorAttributes()

        # need reordering again as manipulator attributes may have been added
        self.cockpitAttributes.order()

        if self.material:
            self.material.collect()

    # Method: collectManipulatorAttributes
    # Defines Manipulator attributes in <cockpitAttributes> based on settings in <XPlaneManipulator>.
    def collectManipulatorAttributes(self):
        attr = 'ATTR_manip_'
        value = True

        if self.blenderObject.xplane.manip.enabled:
            manip = self.blenderObject.xplane.manip
            xplane_version = int(bpy.context.scene.xplane.version)
            if xplane_version >= int(VERSION_1110):
                manipType = manip.type_v1110
            else:
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
            elif manipType == MANIP_DRAG_ROTATE:
                #1. Are we the leaf with translation datarefs and a rotating parent
                #2. Are we the leaf with rotations and it doesn't matter what the parent is?
                rotation_bone = None
                translation_bone = None

                lift_at_max = 0.0 
                if len(self.xplaneBone.children) > 0:
                    logger.error("drag rotate manipulator must be a leaf mesh")
                    return
                elif self.xplaneBone.isDataRefAnimatedForTranslation():
                    if self.xplaneBone.parent is None or not self.xplaneBone.parent.isDataRefAnimatedForRotation():
                        logger.error("drag rotate manipulator has detent component, but no parent with rotation")
                        return
                    else: 
                        rotation_bone = self.xplaneBone.parent
                        
                        translation_bone = self.xplaneBone
                        if len(translation_bone.animations) == 1:
                            keyframe_col = next(iter(translation_bone.animations.values()))
                        else:
                            logger.error("drag rotate manipulator cannot be driven by more than one datarefs cannot have more than 1 dataref")
                            return

                        translation_values = keyframe_col.getTranslationValues()
                        if len(translation_values) == 2:
                            lift_at_max = (translation_values[1] - translation_values[0]).magnitude
                        else:
                            logger.error("drag rotate manipulator does not have exactly two keyframes for it's movement")
                            return
                elif self.xplaneBone.isDataRefAnimatedForRotation():
                    rotation_bone = self.xplaneBone
                
                rotation_origin = rotation_bone.getBlenderWorldMatrix().to_translation()
                if len(rotation_bone.animations) == 1:
                    keyframe_col_parent = next(iter(rotation_bone.animations.values())).keyframesAsAA()
                    rotation_axes = keyframe_col_parent.getReferenceAxes()
                    if len(rotation_axes) > 1:
                        logger.error("Drag rotate manipulator cannot be rotate around more than one axis")
                        #TODO add in more message suggesting changing Euler to AA, or not animiating Axis
                    rotation_axis = rotation_axes[0]

                    assert rotation_axes
                    rotation_values = sorted(keyframe_col.getRotationValues()[0][2])
                    dref2 = "none" if manip.dataref2.strip() == "" else manip.dataref2
                else:
                    logger.error("drag rotate manipulator parent rotation bone cannot be driven by more than one dataref")
                    return

                    
                value = (
                        manip.cursor,
                        rotation_origin[0],
                        rotation_origin[1],
                        rotation_origin[2],
                        rotation_axis[0],
                        rotation_axis[1],
                        rotation_axis[2],
                        math.degrees(rotation_values[0]),
                        math.degrees(rotation_values[-1]),
                        lift_at_max,
                        manip.v1_min,
                        manip.v1_max,
                        manip.v2_min,
                        manip.v2_max,
                        manip.dataref1, #TODO warning if dataref1 is empty?
                        dref2,
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
            elif manipType in (MANIP_COMMAND_KNOB2, MANIP_COMMAND_SWITCH_UP_DOWN2, MANIP_COMMAND_SWITCH_LEFT_RIGHT2):
                value = (
                    manip.cursor,
                    manip.command,
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
                msg = "Manipulator type %s is unknown or unimplemented" % manipType
                logger.error(msg)
                raise Exception(msg)

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
            for attr in self.cockpitAttributes:
                if attr == "ATTR_manip_drag_rotate":
                    v = ('#' + attr,
                        'cursor',
                        'x',
                        'y',
                        'z',
                        'dx',
                        'dy',
                        'dz',
                        'angle1',
                        'angle2',
                        'lift',
                        'v1min',
                        'v1max',
                        'v2min',
                        'v2max',
                        'dataref1',
                        'dataref2',
                        'tooltip')
                    o += '\t'.join(v) +'\n'
                o += commands.writeAttribute(self.cockpitAttributes[attr], self)

        if self.indices[1] > self.indices[0]:
            offset = self.indices[0]
            count = self.indices[1] - self.indices[0]
            o += "%sTRIS\t%d %d\n" % (indent, offset, count)

        return o
