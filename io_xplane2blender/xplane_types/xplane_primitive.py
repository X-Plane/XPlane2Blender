import collections
import math
import sys

import bpy
from mathutils import Vector

from .xplane_attribute import XPlaneAttribute
from .xplane_material import XPlaneMaterial
from .xplane_object import XPlaneObject
from ..xplane_config import getDebug
from ..xplane_constants import *
from ..xplane_helpers import logger
import io_xplane2blender.xplane_types
from io_xplane2blender import xplane_helpers

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
                '''
                Drag rotate manipulators must follow either one of two patterns
                1. The manipulator is attached to a translating XPlaneBone which has a rotating parent bone
                2. The manipulator is attached to a rotation bone

                Special rules for Rotation Bone:
                - Can only be rotated around one axis, no matter the rotation mode
                - Rotation keyframe tables must be sorted in ascending or decending order
                - Rotation keyframe table must have at least 2 rotation keyframes
                - Must be driven by only 1 dataref
                - 0 degree rotation not allowed
                - Clockwise and counterclockwise rotations are supported

                Special rules for Translation Bone:
                - Must be a leaf bone
                - Must have a parent with rotation
                - Must only be driven by only 1 dataref
                - Must have exactly 2 keyframes
                - The animation must start or end at the origin of the bone
                - The positions at each keyframe must not be the same, including both being 0 
                '''
                rotation_bone = None
                translation_bone = None
                translation_values = None

                # Clean any clamped keyframes away
                # List[Tuple[float,float]] -> List[Tuple[float,float]]
                def clean_clamped_keyframes(keyframes,attr):
                    assert isinstance(attr,str)
                    cleaned_keyframes = keyframes[:]
                    # Remove clamp values
                    # List[Tuple[float,float]],value_str -> None
                    def remove_clamp_keyframes(keyframes,attr):
                        itr = iter(keyframes)
                        while True:
                            current       = next(itr)
                            next_keyframe = next(itr,None)

                            if next_keyframe is not None:
                                if getattr(current,attr) == getattr(next_keyframe,attr):
                                    del keyframes[keyframes.index(current)]
                                    itr = iter(keyframes)
                                else:
                                    break

                    remove_clamp_keyframes(cleaned_keyframes,attr)
                    cleaned_keyframes.reverse()
                    remove_clamp_keyframes(cleaned_keyframes,attr)
                    cleaned_keyframes.reverse()
                    
                    return cleaned_keyframes

                lift_at_max = 0.0 
                if len(self.xplaneBone.children) > 0:
                    logger.error("Drag Rotate manipulator must attached to a childless object")
                    return
                elif self.xplaneBone.isDataRefAnimatedForTranslation():
                    if self.xplaneBone.parent is None or not self.xplaneBone.parent.isDataRefAnimatedForRotation():
                        logger.error("Drag Rotate manipulator has detents but no parent with rotation")
                        return
                    else: 
                        rotation_bone = self.xplaneBone.parent
                        
                        translation_bone = self.xplaneBone
                        if len(translation_bone.animations) == 1:
                            keyframe_col = next(iter(translation_bone.animations.values()))
                        else:
                            logger.error("Drag Rotate manipulator cannot be driven by more than one datarefs cannot have more than 1 dataref")
                            return

                        translation_values = keyframe_col.getTranslationKeyframeTable()
                        translation_values_cleaned = clean_clamped_keyframes(translation_values,"location")
                        if len(translation_values_cleaned) == 2:
                            lift_at_max = (translation_values_cleaned[1][1] - translation_values_cleaned[0][1]).magnitude
                        else:
                            logger.error("Drag Rotate manipulator must have exactly two keyframes for its location animation")
                            return
                        
                        def round_vector(vec):
                            return Vector([round(comp,5) for comp in vec])
                        
                        origin  = round_vector(rotation_bone.getBlenderWorldMatrix().to_translation())
                        anim_stop_one = round_vector(translation_values_cleaned[0][1])
                        anim_stop_two = round_vector(translation_values_cleaned[1][1])

                        # TODO: Which of these dataref values goes with the start of the animation?
                        # Last time we said assume the smaller dataref value is the start.
                        # TODO: Does it matter?
                        if not anim_stop_one == origin and not anim_stop_two == origin: 
                            logger.error("Drag Rotate manipulator's location animation must start or end at the origin of rotation")
                            return

                elif self.xplaneBone.isDataRefAnimatedForRotation():
                    rotation_bone = self.xplaneBone

                rotation_origin = rotation_bone.getBlenderWorldMatrix().to_translation()

                if len(rotation_bone.animations) == 1:
                    keyframe_col_parent = next(iter(rotation_bone.animations.values())).keyframesAsAA()
                    rotation_keyframe_table = keyframe_col_parent.getRotationKeyframeTable()
                    if len(rotation_keyframe_table) > 1:
                        logger.error("Drag Rotate manipulator can only rotate around one axis")
                    rotation_axis = rotation_keyframe_table[0][0]

                    rotation_keyframe_data = rotation_keyframe_table[0][1]
                    if not (rotation_keyframe_data == sorted(rotation_keyframe_data) or\
                            rotation_keyframe_data == sorted(rotation_keyframe_data[::-1])):
                        logger.error("Drag Rotate manipulator's dataref values are not in ascending or descending order")
                        return
                    if len(rotation_keyframe_data) < 2:
                        logger.error("Drag Rotate manipulator must have at least 2 rotation keyframes")
                        return

                    rotation_keyframe_values_cleaned = clean_clamped_keyframes(rotation_keyframe_data,"degrees")
                else:
                    logger.error("Drag Rotate manipulator's parent rotation bone cannot be driven by more than one dataref")
                    return
                
                if translation_values is not None and translation_values[0] == translation_values[1]:
                    logger.error("Drag Rotate manipulator's translation min %s and max %s cannot be the same" % (translation_values[0],translation_values[1]))
                elif translation_values is None:
                    v2_min = 0.0
                    v2_max = 0.0
                else:
                    v2_min = 0.0
                    v2_max = lift_at_max
                
                if manip.autodetect_datarefs:
                    manip.dataref1 = next(iter(rotation_bone.datarefs))
                    if translation_bone is not None:
                        manip.dataref2 = next(iter(translation_bone.datarefs))
                    else:
                        manip.dataref2 = "none"

                rotation_origin_xp = xplane_helpers.vec_b_to_x(rotation_origin)
                rotation_axis_xp   = xplane_helpers.vec_b_to_x(rotation_axis)
                
                angle1 = rotation_keyframe_values_cleaned[0].degrees
                angle2 = rotation_keyframe_values_cleaned[-1].degrees

                if round(angle1,5) == round(angle2,5):
                    logger.error("0 degree rotation not allowed")
                    return
                
                #TODO: Should be cleaned keyframe data instead?
                for entry in rotation_keyframe_data:
                    if entry.degrees == angle1:
                        v1_min = entry.value

                for entry in reversed(rotation_keyframe_data):
                    if entry.degrees == angle2:
                        v1_max = entry.value
                
                if v1_min == v1_max:
                    logger.error("Drag Rotate manipulator's Dataref 1 minimum cannot equal Dataref 1 maximum")
                    return

                value = (
                        manip.cursor,
                        rotation_origin_xp[0], #x
                        rotation_origin_xp[1], #y
                        rotation_origin_xp[2], #z
                        rotation_axis_xp[0],   #dx
                        rotation_axis_xp[1],   #dy
                        rotation_axis_xp[2],   #dz
                        angle1,
                        angle2,
                        lift_at_max,
                        v1_min,
                        v1_max,
                        v2_min,
                        v2_max,
                        manip.dataref1,
                        manip.dataref2,
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
            if manipType == MANIP_DRAG_ROTATE and bpy.context.scene.xplane.version >= VERSION_1110:
                
                #List[AxisDetentRange] -> bool
                def validate_axis_detent_ranges(axis_detent_ranges,v1_min,v1_max,lift_at_max):
                    '''
                    Rules for Axis Detent Ranges
                    
                    Basic rules
                    - The detent ranges must cover [v1_min,v1_max] without gaps.
                      Therefore
                          - The start of one range must be the end of another
                          - ranges[0].start == v1_min, ranges[-1].end == v1_max
                    - A range's start must be <= its end
                    - Height must be between 0 and lift_at_max
                    
                    Stop Pits
                    - A stop pit is defined as range.start == range.end, range.height is less than each of it's neighbors.
                    - A pit can be the first or last detent range, but never the only one
                    - Stop pegs, where height is equal to or greater than it's neighbor's height, are never allowed
                    '''
                    assert len(axis_detent_ranges) > 0

                    if not axis_detent_ranges[0].start == v1_min:
                        logger.error("Axis detent range list must start at Dataref 1's minimum value {0}".format(v1_min))
                        return False
                        
                    if not axis_detent_ranges[-1].end == v1_max:
                        logger.error("Axis detent range list must end at Dataref 1's maximum value {0}".format(v1_max))
                        return False

                    if len({range.height for range in axis_detent_ranges}) == 1:
                        logger.warn("All axis detent ranges have the same height. Check your entered data")

                    for i in range(len(axis_detent_ranges)):
                        detent_range = axis_detent_ranges[i]
                        if not detent_range.start <= detent_range.end:
                            logger.error(
                                "The start of axis detent range {0} must be less than or equal to its end".format(detent_range)
                                )
                            return False

                        if not 0.0 <= detent_range.height <= lift_at_max:
                            logger.error(
                                "Height in axis detent range {0} must be between 0.0 and the maximum lift height ({1})".format(detent_range,lift_at_max))
                            return False

                        # Pit detection portion
                        if len(axis_detent_ranges) == 1 and detent_range.start == detent_range.end:
                            logger.error("Cannot have stop pit on detent range with only one detent")
                            return False

                        AxisDetentStruct = collections.namedtuple("AxisDetentStruct", ['start','end','height'])
                        try:
                            detent_range_next = axis_detent_ranges[i+1]
                        except:
                            detent_range_next = AxisDetentStruct(detent_range.end, v1_max, float('inf'))


                        if not detent_range.end == detent_range_next.start:
                            logger.error("The start of a detent range must be the end of the previous detent range {0},{1}".format(
                                detent_range,
                                (detent_range_next.start,detent_range_next.end,detent_range.height)))
                            return False
                        
                        try:
                            detent_range_prev = axis_detent_ranges[i-1]
                        except:
                            detent_range_prev = AxisDetentStruct(v1_min, detent_range.start, float('inf'))
                            
                        if detent_range.start == detent_range.end and\
                           not detent_range_prev.height > detent_range.height < detent_range_next.height:
                            logger.error("Stop pit created by detent_range {0} must be lower than"
                                         " previous {1} and next detent ranges {2}".format(
                                            (detent_range),
                                            (detent_range_prev.start,detent_range_prev.end,detent_range.height),
                                            (detent_range_next.start,detent_range_next.end,detent_range_next.height))
                                         )
                            return False

                    return True

                if len(manip.axis_detent_ranges) > 0:
                    if not validate_axis_detent_ranges(manip.axis_detent_ranges,manip.v1_min,manip.v1_max, lift_at_max):
                        return

                for axis_detent_range in manip.axis_detent_ranges:
                    self.cockpitAttributes.add(XPlaneAttribute('ATTR_axis_detent_range',
                        (axis_detent_range.start, axis_detent_range.end, axis_detent_range.height)))

                if len(rotation_keyframe_values_cleaned) > 2:
                    for rot_keyframe in rotation_keyframe_values_cleaned[1:-1]:
                        self.cockpitAttributes.add(
                            XPlaneAttribute('ATTR_manip_keyframe', (rot_keyframe.value,rot_keyframe.degrees))
                        )
            else:
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
