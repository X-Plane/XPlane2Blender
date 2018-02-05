'''
Created on Jan 30, 2018

@author: Ted
'''
import collections

import bpy
from mathutils import Vector
from io_xplane2blender import xplane_helpers
from io_xplane2blender.xplane_helpers import logger
from io_xplane2blender.xplane_constants import *
from io_xplane2blender.xplane_types.xplane_keyframe_collection import XPlaneKeyframeCollection
from io_xplane2blender.xplane_types.xplane_attribute import XPlaneAttribute
from gettext import translation

def round_vector(vec,ndigits=5):
    return Vector([round(comp,ndigits) for comp in vec])


# Must rename these so the match a better "is_leaf_bone", "is_thing_true", to take advantage of if not is_thing_true pattern
def autodetect_must_be_leaf_bone(bone):
    if len(bone.children) > 0:
        logger.error("Manipulator bone must be the leaf bone")
        return False
    else:
        return True


def autodetect_must_have_parent(bone):
    if bone.parent is None:
        logger.error("Must have parent bone")
        return False
    else:
        return True


def autodetect_must_be_driven_by_exactly_n_datarefs(bone, num_datarefs):
    '''
    bone:XPlaneBone (not none) -> bool
    Checks animations dict, not datarefs dictionary because we're looking for the actual animation
    that will be considered for the OBJ, and the datarefs dictionary is not guaranteed to be semantically
    the same thing.
    '''
    
    if len(bone.animations) != num_datarefs:
        logger.error("Drag Rotate manipulator's location animation cannot be driven by more than {0} datarefs".format(num_datarefs))
        return False
    else:
        return True


def autodetect_keyframe_count_translation(translation_bone, count, exclude_clamping):
        keyframe_col = next(iter(translation_bone.animations.values()))
        
        if exclude_clamping:
            res = len(keyframe_col.getTranslationKeyframeTableNoClamps()) == count
        else:
            res = len(keyframe_col.getTranslationKeyframeTable()) == count

        if not res:
            logger.error("Drag Rotate manipulator must have exactly two non-clamping keyframes for its location animation")
            return False
        else:
            return True 

def autodetect_bone_rotated_around_n_axis(bone,num_axis_of_rotation):
    rotation_keyframe_table = next(iter(bone.animations.values())).asAA().getRotationKeyframeTable()
    if len(rotation_keyframe_table) != num_axis_of_rotation:
        logger.error("Drag Rotate manipulator can only rotate around one axis")
        return False
    else:
        return True

def autodetect_parent_must_be_animated_for_rotation(bone): 
    assert bone.parent is not None

    if not bone.parent.isDataRefAnimatedForRotation():
        logger.error("Drag Rotate's parent must be rotated for animation")
        return False
    else:
        return True

 
 # X-Plane note: X-Plane implements Drag Rotate manipulator using a system akin to polar co-ordinates
 # If the rotation axis is on Z, the Detent can be draged on the X,Y axis, have this translated into an angle.
 # The distance from the origin corresponds to the distance dragged. If a detent is animated at all on the Z axis,
 # X-Plane won't drag along there at all and it'll have problems
 # We take the dot product between the rotation axis and detent axis to discover if there is any compontent along that axis 
def translation_animation_at_origin_check(rotation_bone,child_bone):
    rotation_keyframe_table =\
        next(iter(rotation_bone.animations.values()))\
        .asAA()\
        .getRotationKeyframeTable()

    rotation_axis = rotation_keyframe_table[0][0]

    child_values_cleaned = next(iter(child_bone.animations.values()))\
        .getTranslationKeyframeTableNoClamps()

    child_axis = child_values_cleaned[1][1] - child_values_cleaned[0][1]

    dot_product = child_axis.dot(rotation_axis)
    if not -0.01 < dot_product < 0.01:
        logger.error("Drag Rotate manipulator's location animation must be orthoganal to rotation animation")
        return False
    else:
        return True


def get_lift_at_max(translation_bone):
    translation_values_cleaned = next(iter(translation_bone.animations.values()))\
        .getTranslationKeyframeTableNoClamps()
    return (translation_values_cleaned[1][1] - translation_values_cleaned[0][1]).magnitude


def get_rotation_bone(manipulator, manip_type):
    if manip_type == MANIP_DRAG_ROTATE:
        if manipulator.xplanePrimative.xplaneBone.isDataRefAnimatedForRotation():
            return manipulator.xplanePrimative.xplaneBone
        else:
            return manipulator.xplanePrimative.xplaneBone.parent
    else:
        assert False, "How did we get here?!"


def get_translation_bone(manipulator, manip_type):
    if manip_type == MANIP_DRAG_AXIS_DETENT:
        return manipulator.xplanePrimative.xplaneBone
    if manip_type == MANIP_DRAG_ROTATE:
        if not manipulator.xplanePrimative.xplaneBone.isDataRefAnimatedForRotation():
            # Accounts for translation_bones that have detents or not
            return manipulator.xplanePrimative.xplaneBone
        else:
            return None


class XPlaneManipulator():
    
    def __init__(self, xplanePrimative):
        self.manip = xplanePrimative.blenderObject.xplane.manip
        self.xplanePrimative = xplanePrimative

    def type(self):
        xplane_version = int(bpy.context.scene.xplane.version)
        if xplane_version >= int(VERSION_1110):
            return self.manip.type_v1110
        else:
            return self.manip.type

    
    def collect(self):
        attr = 'ATTR_manip_'
        value = True

        if self.manip.enabled:
            attr += self.type()

            if self.type() == MANIP_DRAG_XY:
                value = (
                    self.manip.cursor,
                    self.manip.dx,
                    self.manip.dy,
                    self.manip.v1_min,
                    self.manip.v1_max,
                    self.manip.v2_min,
                    self.manip.v2_max,
                    self.manip.dataref1,
                    self.manip.dataref2,
                    self.manip.tooltip
                )
            elif self.type() == MANIP_DRAG_AXIS:
                value = (
                    self.manip.cursor,
                    self.manip.dx,
                    self.manip.dy,
                    self.manip.dz,
                    self.manip.v1,
                    self.manip.v2,
                    self.manip.dataref1,
                    self.manip.tooltip
                )
            elif self.type() == MANIP_DRAG_AXIS_PIX:
                value = (
                    self.manip.cursor,
                    self.manip.dx,
                    self.manip.step,
                    self.manip.exp,
                    self.manip.v1,
                    self.manip.v2,
                    self.manip.dataref1,
                    self.manip.tooltip
                )
            elif self.type() == MANIP_DRAG_AXIS_DETENT:
                # Semantically speaking we don't have a new manipulator type. The magic is in ATTR_axis_detented
                attr = "ATTR_manip_" + MANIP_DRAG_AXIS
                '''
                Drag Axis/Drag Axis With Detents
                Empty/Bone -> main drag axis animation and (optionally) v1_min/max for validating axis_detent_ranges
                |_Child mesh -> manipulator settings and (optionally) detent axis animation
                  
                Common Rules:
                - Animations must only be driven by only 1 dataref
                - Animations must have exactly 2 (non-clamping) keyframes
                
                Special rules for the Translation Bone:
                - Must be a leaf bone
                - Must have a parent with translation
                - The animation must start or end at the origin of the bone
                - The positions at each keyframe must not be the same, including both being 0 
                '''
                
                if not autodetect_must_have_parent(self.xplanePrimative.xplaneBone):
                    return
                else:
                    parent_bone = self.xplanePrimative.xplaneBone.parent
                
                if not parent_bone.isDataRefAnimatedForTranslation():
                    logger.error("Parent bone must be animated for translation")
                    return

                translation_bone = get_translation_bone(self, MANIP_DRAG_AXIS_DETENT)

                if not autodetect_must_be_driven_by_exactly_n_datarefs(parent_bone, 1):
                    #logger.error("Parent has more than one animation")
                    return
                
                if not autodetect_must_be_driven_by_exactly_n_datarefs(translation_bone,1):
                    return

                if not autodetect_must_be_leaf_bone(translation_bone):
                    return

                #bone.animations - <DataRef,List<KeyframeCollection>>
                drag_axis_dataref = next(iter(parent_bone.animations))
                drag_axis_frames_cleaned = next(iter(parent_bone.animations.values())).getTranslationKeyframeTableNoClamps()
                drag_axis_b = drag_axis_frames_cleaned[1].location - drag_axis_frames_cleaned[0].location
                drag_axis_xp = xplane_helpers.vec_b_to_x(drag_axis_b)
                drag_axis_dataref_values = (drag_axis_frames_cleaned[0].value, drag_axis_frames_cleaned[1].value)
                        
                if not autodetect_keyframe_count_translation(parent_bone, count=2, exclude_clamping=True):
                    # taken care of logger.error("Drag Axis manipulator must have exactly two non-clamping keyframes for its drag axis animation")
                    return

                if not autodetect_must_be_driven_by_exactly_n_datarefs(translation_bone,1):
                    return
                elif not autodetect_keyframe_count_translation(translation_bone, count=2, exclude_clamping=True):
                    return
                else:
                    lift_at_max = get_lift_at_max(translation_bone)

                if not translation_animation_at_origin_check(drag_axis, translation_bone):
                    return
    
                v1_min = drag_axis_frames_cleaned[0].value
                v1_max = drag_axis_frames_cleaned[1].value

                value = (
                    self.manip.cursor,
                    drag_axis_xp.x,
                    drag_axis_xp.y,
                    drag_axis_xp.z,
                    drag_axis_dataref_values[0],
                    drag_axis_dataref_values[1],
                    drag_axis_dataref,
                    self.manip.tooltip
                )
            elif self.type() == MANIP_DRAG_ROTATE:
                '''
                Drag rotate manipulators must follow either one of two patterns
                1. The manipulator is attached to a translating XPlaneBone which has a rotating parent bone
                2. The manipulator is attached to a rotation bone

                Common
                - Manipulator must be animated

                Special rules for the Rotation Bone:
                - Can only be rotated around one axis, no matter the rotation mode
                - Rotation keyframe tables must be sorted in ascending or decending order
                - Rotation keyframe table must have at least 2 rotation keyframes (taken care of by other animation code)
                - Must be driven by only 1 dataref
                - 0 degree rotation not allowed
                - Clockwise and counterclockwise rotations are supported

                Special rules for Translation Bone:
                - Must be a leaf bone
                - Must have a parent with rotation
                - Must only be driven by only 1 dataref
                - Must have exactly 2 (non-clampping) keyframes
                - Must not animate along rotation bone's axis
                - The positions at each keyframe must not be the same, including both being 0 
                - Detents are optional
                - If detents are not used, axis detent ranges are not allowed
                '''
                if not autodetect_must_have_parent(self.xplanePrimative.xplaneBone):
                    return

                rotation_bone    = get_rotation_bone(self, self.type())
                translation_bone = get_translation_bone(self, self.type())
                lift_at_max = 0.0
                
                if translation_bone:
                    if rotation_bone is not None and\
                       rotation_bone.isDataRefAnimatedForRotation() and\
                       len(translation_bone.animations) > 0:
                        if not autodetect_must_be_driven_by_exactly_n_datarefs(translation_bone,1):
                            return
                        else:
                            keyframe_col = next(iter(translation_bone.animations.values()))

                        if not autodetect_keyframe_count_translation(translation_bone,count=2, exclude_clamping=True):
                            return
                        else:
                            lift_at_max = get_lift_at_max(translation_bone)

                    elif not autodetect_must_have_parent(translation_bone):
                        return
                    elif not autodetect_parent_must_be_animated_for_rotation(translation_bone):
                        return
                    else:
                        pass

                elif rotation_bone:
                    rotation_bone = self.xplanePrimative.xplaneBone
                else:
                    logger.error("Drag Rotate manipulator must be animated according to your intended manipulation goal (throttle vs trim wheel styel)")
                    return

                rotation_origin = rotation_bone.getBlenderWorldMatrix().to_translation()

                if autodetect_must_be_driven_by_exactly_n_datarefs(rotation_bone, 1):
                    if not autodetect_bone_rotated_around_n_axis(rotation_bone,1):
                        return
                    else:
                        rotation_keyframe_table =\
                            next(iter(rotation_bone.animations.values()))\
                            .asAA()\
                            .getRotationKeyframeTable()

                        rotation_axis = rotation_keyframe_table[0][0]
                        rotation_keyframe_data = rotation_keyframe_table[0][1]

                    if not (rotation_keyframe_data == sorted(rotation_keyframe_data) or\
                            rotation_keyframe_data == sorted(rotation_keyframe_data[::-1])):
                        logger.error("Drag Rotate manipulator's rotation dataref values are not in ascending or descending order")
                        return

                    rotation_keyframe_data_cleaned = XPlaneKeyframeCollection.filter_clamping_keyframes(rotation_keyframe_data,"degrees")
                else:
                    return

                if translation_bone is None:
                    v2_min = 0.0
                    v2_max = 0.0
                else:
                    if len(rotation_bone.animations) > 0 and len(translation_bone.animations) > 0:
                        if not translation_animation_at_origin_check(rotation_bone,translation_bone):
                            return
                    v2_min = 0.0
                    v2_max = lift_at_max
                
                if self.manip.autodetect_datarefs:
                    self.manip.dataref1 = next(iter(rotation_bone.datarefs))
                    if translation_bone is not None and len(translation_bone.datarefs) == 1:
                        self.manip.dataref2 = next(iter(translation_bone.datarefs))
                    else:
                        self.manip.dataref2 = "none"

                rotation_origin_xp = xplane_helpers.vec_b_to_x(rotation_origin)
                rotation_axis_xp   = xplane_helpers.vec_b_to_x(rotation_axis)
                
                angle1 = rotation_keyframe_data_cleaned[0].degrees
                angle2 = rotation_keyframe_data_cleaned[-1].degrees

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
                        self.manip.cursor,
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
                        self.manip.dataref1,
                        self.manip.dataref2,
                        self.manip.tooltip
                )
            elif self.type() == MANIP_COMMAND:
                value = (self.manip.cursor, self.manip.command, self.manip.tooltip)
            elif self.type() == MANIP_COMMAND_AXIS:
                value = (
                    self.manip.cursor,
                    self.manip.dx,
                    self.manip.dy,
                    self.manip.dz,
                    self.manip.positive_command,
                    self.manip.negative_command,
                    self.manip.tooltip
                )
            elif self.type() in (MANIP_COMMAND_KNOB, MANIP_COMMAND_SWITCH_UP_DOWN, MANIP_COMMAND_SWITCH_LEFT_RIGHT):
                value = (
                    self.manip.cursor,
                    self.manip.positive_command,
                    self.manip.negative_command,
                    self.manip.tooltip
                )
            elif self.type() in (MANIP_COMMAND_KNOB2, MANIP_COMMAND_SWITCH_UP_DOWN2, MANIP_COMMAND_SWITCH_LEFT_RIGHT2):
                value = (
                    self.manip.cursor,
                    self.manip.command,
                    self.manip.tooltip
                )
            elif self.type() == MANIP_PUSH:
                value = (
                    self.manip.cursor,
                    self.manip.v_down,
                    self.manip.v_up,
                    self.manip.dataref1,
                    self.manip.tooltip
                )
            elif self.type() == MANIP_RADIO:
                value = (
                    self.manip.cursor,
                    self.manip.v_down,
                    self.manip.dataref1,
                    self.manip.tooltip
                )
            elif self.type() == MANIP_TOGGLE:
                value = (
                    self.manip.cursor,
                    self.manip.v_on,
                    self.manip.v_off,
                    self.manip.dataref1,
                    self.manip.tooltip
                )
            elif self.type() in (MANIP_DELTA, MANIP_WRAP):
                value = (
                    self.manip.cursor,
                    self.manip.v_down,
                    self.manip.v_hold,
                    self.manip.v1_min,
                    self.manip.v1_max,
                    self.manip.dataref1,
                    self.manip.tooltip
                )
            elif self.type() in (MANIP_AXIS_SWITCH_UP_DOWN, MANIP_AXIS_SWITCH_LEFT_RIGHT):
                value = (
                    self.manip.cursor,
                    self.manip.v1,
                    self.manip.v2,
                    self.manip.click_step,
                    self.manip.hold_step,
                    self.manip.dataref1,
                    self.manip.tooltip
                )
            elif self.type() == MANIP_NOOP:
                value = (
                    self.manip.dataref1,
                    self.manip.tooltip
                )
            else:
                msg = "Manipulator type %s is unknown or unimplemented" % self.type
                logger.error(msg)
                raise Exception(msg)

        else:
            attr = None

        if attr is not None:
            # Order in OBJ (only added if applicable)
            # 1. "ATTR_manip_"+type
            self.xplanePrimative.cockpitAttributes.add(XPlaneAttribute(attr, value))
            
            ver_ge_1100 = int(bpy.context.scene.xplane.version) >= int(VERSION_1110)

            # 2. ATTR_axis_detented (DRAG_AXIS_DETENT)
            if (self.type() == MANIP_DRAG_AXIS_DETENT) and ver_ge_1100:
                detent_axis_dataref = next(iter(translation_bone.animations))
                detent_axis_frames_cleaned = next(iter(translation_bone.animations.values())).getTranslationKeyframeTableNoClamps()
                detent_axis_b = detent_axis_frames_cleaned[1].location - detent_axis_frames_cleaned[0].location
                detent_axis_xp = xplane_helpers.vec_b_to_x(detent_axis_b)
                self.xplanePrimative.cockpitAttributes.add(XPlaneAttribute("ATTR_axis_detented",
                                                           (detent_axis_xp.x,
                                                            detent_axis_xp.y,
                                                            detent_axis_xp.z,
                                                            detent_axis_frames_cleaned[0].value,
                                                            detent_axis_frames_cleaned[1].value,
                                                            detent_axis_dataref),
                                                           ))

            # 3. All ATTR_axis_detent_range (DRAG_AXIS_DETENT or DRAG_ROTATE)
            if (self.type() == MANIP_DRAG_AXIS_DETENT or self.type() == MANIP_DRAG_ROTATE) and ver_ge_1100:

                #List[AxisDetentRange] -> bool
                def validate_axis_detent_ranges(axis_detent_ranges, translation_bone, v1_min, v1_max, lift_at_max):
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
                    if not translation_bone.isDataRefAnimatedForTranslation() or len(axis_detent_ranges) > 0:
                        if not len(axis_detent_ranges) > 0 and translation_bone.isDataRefAnimatedForTranslation():
                            logger.error("Must have axis detent range if translation bone is animated")
                            return

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

                if len(self.manip.axis_detent_ranges) > 0:
                    if not validate_axis_detent_ranges(self.manip.axis_detent_ranges, translation_bone, v1_min, v1_max, lift_at_max):
                        return

                for axis_detent_range in self.manip.axis_detent_ranges:
                    self.xplanePrimative.cockpitAttributes.add(XPlaneAttribute('ATTR_axis_detent_range',
                        (axis_detent_range.start, axis_detent_range.end, axis_detent_range.height)))

            # 4. All ATTR_manip_keyframes (DRAG_ROTATE)
            if self.type() == MANIP_DRAG_ROTATE:
                if len(rotation_keyframe_data_cleaned) > 2:
                    for rot_keyframe in rotation_keyframe_data_cleaned[1:-1]:
                        self.xplanePrimative.cockpitAttributes.add(
                            XPlaneAttribute('ATTR_manip_keyframe', (rot_keyframe.value,rot_keyframe.degrees))
                        )
            # add mouse wheel delta
            if self.type() in MOUSE_WHEEL_MANIPULATORS and bpy.context.scene.xplane.version >= VERSION_1050 and self.manip.wheel_delta != 0:
                self.xplanePrimative.cockpitAttributes.add(XPlaneAttribute('ATTR_manip_wheel', self.manip.wheel_delta))

    def write(self):
        pass
    

