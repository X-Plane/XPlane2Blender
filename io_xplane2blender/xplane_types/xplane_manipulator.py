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
from io_xplane2blender.xplane_types.xplane_attribute import XPlaneAttribute
from io_xplane2blender.xplane_types.xplane_bone import XPlaneBone
from io_xplane2blender.xplane_types.xplane_keyframe_collection import XPlaneKeyframeCollection

def round_vector(vec,ndigits=5) -> Vector:
    return Vector([round(comp,ndigits) for comp in vec])


def get_manip_from_bone(bone:XPlaneBone):
    return bone.xplaneObject.manipulator.manip


'''
Some of these check_* methods break the rule of "no side effects in a boolean expression" when log_errors = True
However, without this, the logic must be duplicated, making it, in my opinion, worth it.

In addition, in order to give better error messages, some less used aspects of the data model are used. For instance,
using bone.datarefs instead of bone.animations for check_bone_has_n_datarefs
'''
def check_bone_has_n_datarefs(bone:XPlaneBone, num_datarefs:int, anim_type:str, log_errors=True) -> bool:
    '''
    Checks animations dict, not datarefs dictionary because we're looking for the actual animation
    that will be considered for the OBJ, and the datarefs dictionary is not guaranteed to be semantically
    the same thing.
    '''

    assert bone

    if len(bone.datarefs) != num_datarefs:
        try:
            manip = get_manip_from_bone(bone)
            if log_errors:
                logger.error("The {} animation for the {} manipulator attached to {} must have exactly {} datarefs for its animation".format(
                    anim_type,
                    manip.get_effective_type_name(),
                    bone.getBlenderName(),
                    num_datarefs))
        except:
            if log_errors:
                logger.error("The {} animation for {} must have exactly {} datarefs for its animation".format(
                    anim_type,
                    bone.getBlenderName(),
                    num_datarefs))

        return False
    else:
        return True


def check_bone_has_parent(bone:XPlaneBone, log_errors=True) -> bool:
    if bone.parent is None:
        if log_errors:
            logger.error("{} manipulator attached to {} must have a parent".format(
                get_manip_from_bone(bone).get_effective_type_name(),
                bone.getblendername()))
        return False
    else:
        return True


def check_bone_is_animated_for_rotation(bone:XPlaneBone,log_errors:bool=True) -> bool:
    assert bone is not None

    # Unfortunately this does not answer if we have one rotation keyframe, which, semantically
    # we are checking for. This makes us never able to really get a good error message for
    # "test_5_must_have_at_least_2_non_clamping_keyframes  See bug #333
    #
    # While it would nice to use the RotationKeyframeTable, we don't know if that can
    # be generated yet, a call to getReferenceAxes could fail if forced
    if not bone.isDataRefAnimatedForRotation():
        if log_errors:
            logger.error("{} manipulator attached to {} must have at least 2 rotation keyframes that are not the same".format(
                get_manip_from_bone(bone).get_effective_type_name(),
                bone.getBlenderName()))
        return False
    else:
        return True


def check_bone_is_animated_for_translation(bone:XPlaneBone,log_errors:bool=True) -> bool:
    assert bone is not None
    if len(next(iter(bone.animations.values())).getTranslationKeyframeTable()) == 0:
        if log_errors:
            logger.error("{} manipulator attached to {} must have location keyframes".format(
                get_manip_from_bone(bone).get_effective_type_name(),
                bone.getBlenderName()))
        return False
    else:
        return True


def check_bone_is_animated_on_n_axes(bone:XPlaneBone,num_axis_of_rotation:int, log_errors=True) -> bool:
    rotation_keyframe_table = next(iter(bone.animations.values())).getRotationKeyframeTable()

    if len(rotation_keyframe_table) == 3:
        deg_per_axis = []
        for axis,table in rotation_keyframe_table:
            deg_per_axis.append(sum([keyframe.degrees for keyframe in table]))

        real_num_axis_of_rotation = len((*filter(lambda total_rotations: round(total_rotations,8) != 0.0, deg_per_axis),))
    else:
        real_num_axis_of_rotation = len(rotation_keyframe_table)

    # The sum of the degrees rotated along each axis over every keyframe sorted from lowest-to-highest
    # should be 0,0,T. Having a second or all three rotating would mean that at least the second entry would be not 0
    if real_num_axis_of_rotation != num_axis_of_rotation:
        if log_errors:
            logger.error("{} manipulator attached to {} can only rotate around {} axis".format(
                get_manip_from_bone(bone).get_effective_type_name(),
                bone.getBlenderName(),
                num_axis_of_rotation))
        return False
    else:
        return True


def check_bone_is_leaf(bone:XPlaneBone, log_errors:bool=True) -> bool:
    if len(bone.children) > 0:
        if log_errors:
            logger.error("{} manipulator attached to {} must have no children".format(
                get_manip_from_bone(bone).get_effective_type_name(),
                bone.getBlenderName()))
        return False
    else:
        return True


def check_bone_is_not_animated_for_rotation(bone:XPlaneBone,log_errors:bool=True) -> bool:
    if check_bone_is_animated_for_rotation(bone, log_errors=False):
        if log_errors:
            logger.error("{} manipulator attached to {} must not have rotation keyframes".format(
                get_manip_from_bone(bone).get_effective_type_name(),
                bone.getBlenderName()))
        return False
    else:
        return True
    

def check_bone_is_not_animated_for_translation(bone:XPlaneBone,log_errors:bool=True) -> bool:
    if check_bone_is_animated_for_translation(bone, log_errors):
        if log_errors:
            logger.error("{} manipulator attached to {} must not have location keyframes".format(
                get_manip_from_bone(bone).get_effective_type_name(),
                bone.getBlenderName()))
        return False
    else:
        return True


def check_bone_parent_is_animated_for_rotation(bone:XPlaneBone, log_errors:bool=True) -> bool:
    assert bone.parent
    if not check_bone_is_animated_for_rotation(bone.parent, False):
        if log_errors:
            logger.error("{}'s parent {} must be animated with rotation".format(
                         bone.getBlenderName(),
                         bone.parent.getBlenderName()))
        return False
    else:
        return True
    


def check_bone_parent_is_animated_for_translation(bone:XPlaneBone, log_errors:bool=True) -> bool:
    assert bone.parent
    if not check_bone_is_animated_for_translation(bone.parent, log_errors):
        if log_errors:
            logger.error("{}'s parent {} must be animated with location keyframes".format(
                         bone.getBlenderName(),
                         bone.parent.getBlenderName()))
        return False
    else:
        return True


def check_bones_drag_detent_are_orthogonal(drag_axis_bone:XPlaneBone, detent_bone:XPlaneBone) -> bool:
    drag_axis_translation_keyframe_table =\
        next(iter(drag_axis_bone.animations.values()))\
        .getTranslationKeyframeTable()

    detent_axis_translation_keyframe_table =\
        next(iter(detent_bone.animations.values()))\
        .getTranslationKeyframeTable()

    # Assuming that these are only rotating on a single axis
    drag_axis = drag_axis_translation_keyframe_table[-1].location - drag_axis_translation_keyframe_table[0].location
    detent_axis = detent_axis_translation_keyframe_table[-1].location - detent_axis_translation_keyframe_table[0].location

    dot_product = drag_axis.dot(detent_axis)

    if not -0.01 < dot_product < 0.01:
        logger.error("Location animation for the {} manipulator attached to {} must not be along the main drag animation axis".format(
            get_manip_from_bone(detent_bone).get_effective_type_name(),
            detent_bone.getBlenderName()))
        return False
    else:
        return True


# X-Plane note: X-Plane implements the Drag Rotate manipulator using a system akin to polar co-ordinates.
# If the rotation axis is on Z, the detent can be draged any where in XY space. This will be translated into polar co-ordinates
# as angle, and distance is the distance draged from the origin.
# If the detent animation is animated at al on the Z axis, X-Plane won't drag there and it'll be a broken manipulator
#
# To detect this, we take the dot product between the rotation and detent axis to discover if there is any component along that axis
def check_bones_rotation_translation_animations_are_orthogonal(rotation_bone:XPlaneBone,child_bone:XPlaneBone) -> bool:
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
        logger.error("Location animation for the {} manipulator attached to {} must not be along the rotation animation axis".format(
            get_manip_from_bone(child_bone).get_effective_type_name(),
            child_bone.getBlenderName()))
        return False
    else:
        return True

def _check_keyframe_rotation_count(rotation_bone:XPlaneBone, count:int, exclude_clamping:bool, cmp_func, cmp_error_msg:str, log_errors:bool=True) -> bool:
    keyframe_col = next(iter(rotation_bone.animations.values())).asAA()

    if exclude_clamping:
        res = cmp_func(len(keyframe_col.getRotationKeyframeTableNoClamps()[0]),count)
    else:
        res = cmp_func(len(keyframe_col.getRotationKeyframeTable()[0]),count)

    if not res:
        try:
            manip = get_manip_from_bone(rotation_bone)
            logger.error("{} manipulator attached to {} must have {} {} {}keyframes for its rotation animation".format(
                get_manip_from_bone(rotation_bone).get_effective_type_name(),
                rotation_bone.getBlenderName(),
                cmp_error_msg,
                count,
                "non-clamping " if exclude_clamping else ""))
        except:
            logger.error("{} must have {} {} {}keyframes for its rotation animation".format(
                rotation_bone.getBlenderName(),
                cmp_error_msg,
                count,
                "non-clamping " if exclude_clamping else ""))

        return False
    else:
        return True


def check_keyframe_rotation_eq_count(rotation_bone:XPlaneBone, count:int, exclude_clamping:bool, log_errors:bool=True) -> bool:
    return _check_keyframe_rotation_count(rotation_bone, count, exclude_clamping, lambda x,y: x==y, "exactly", log_errors)


def check_keyframe_rotation_ge_count(rotation_bone:XPlaneBone, count:int, exclude_clamping:bool, log_errors:bool=True) -> bool:
    return _check_keyframe_rotation_count(rotation_bone, count, exclude_clamping, lambda x,y: x>=y, "greater than or equal to", log_errors)

def _check_keyframe_translation_count(translation_bone:XPlaneBone, count:int, exclude_clamping:bool, cmp_func, cmp_error_msg:str, log_errors:bool=True) -> bool:
    keyframe_col = next(iter(translation_bone.animations.values()))

    if exclude_clamping:
        res = cmp_func(len(keyframe_col.getTranslationKeyframeTableNoClamps()),count)
    else:
        res = cmp_func(len(keyframe_col.getTranslationKeyframeTable()),count)

    if not res:
        try:
            if log_errors:
                logger.error("{} manipulator attached to {} must have {} {} {}keyframes for its location animation".format(
                    get_manip_from_bone(translation_bone).get_effective_type_name(),
                    translation_bone.getBlenderName(),
                    cmp_error_msg,
                    count,
                    "non-clamping " if exclude_clamping else ""))
        except:
            if log_errors:
                logger.error("{} must have {} {} {}keyframes for its location animation".format(
                    translation_bone.getBlenderName(),
                    cmp_error_msg,
                    count,
                    "non-clamping " if exclude_clamping else ""))

        return False
    else:
        return True


def check_keyframe_translation_eq_count(translation_bone:XPlaneBone, count:int, exclude_clamping:bool, log_errors:bool=True) -> bool:
    return _check_keyframe_translation_count(translation_bone, count, exclude_clamping, lambda x,y: x==y, "exactly", log_errors)


def check_keyframe_translation_ge_count(translation_bone:XPlaneBone, count:int, exclude_clamping:bool, log_errors:bool=True) -> bool:
    return _check_keyframe_translation_count(translation_bone, count, exclude_clamping, lambda x,y: x>=y, "greater than or equal to", log_errors)

def check_keyframes_rotation_are_orderered(rotation_bone:XPlaneBone, log_errors:bool=True) -> bool:
    rotation_keyframe_table =\
        next(iter(rotation_bone.animations.values()))\
        .asAA()\
        .getRotationKeyframeTable()

    rotation_axis = rotation_keyframe_table[0][0]
    rotation_keyframe_data = rotation_keyframe_table[0][1]
    if not (rotation_keyframe_data == sorted(rotation_keyframe_data) or\
            rotation_keyframe_data == sorted(rotation_keyframe_data[::-1])):
        if log_errors:
            logger.error("Rotation dataref values for the {} manipulator attached to {} are not in ascending or descending order".format(
                get_manip_from_bone(rotation_bone).get_effective_type_name(),
                rotation_bone.getBlenderName()))
        return False
    else:
        return True

def check_manip_has_axis_detent_ranges(manipulator:'XPlaneManipulator', log_errors:bool=True) -> bool:
    assert manipulator.type == MANIP_DRAG_AXIS_DETENT or\
           manipulator.type == MANIP_DRAG_ROTATE_DETENT

    if not manipulator.manip.axis_detent_ranges:
        if log_errors:
            logger.error("{} manipulator attached to {} must have axis detent ranges".format(
                manipulator.type,
                manipulator.xplanePrimative.xplaneBone.getBlenderName()))
        return False
    else:
        return True

def get_lift_at_max(translation_bone: XPlaneBone) -> float:
    translation_values_cleaned = next(iter(translation_bone.animations.values()))\
        .getTranslationKeyframeTableNoClamps()
    return (translation_values_cleaned[1][1] - translation_values_cleaned[0][1]).magnitude


def get_drag_axis_bone(manipulator:'XPlaneManipulator', log_errors:bool=True) -> XPlaneBone:
    '''
    Gets the drag_axis_bone. manip.type must be MANIP_AXIS_DETENT
    '''
    assert manipulator.type == MANIP_DRAG_AXIS_DETENT,\
           "Unimplemented or wrong manipulator type {} used".format(manipulator.type)
    
    '''
    The bone must
        - have exactly 1 dataref
        - be animated for translation
        - have two non-clamping location keyframes
        - not be animated for rotation
    '''
    
    drag_axis_bone = manipulator.xplanePrimative.xplaneBone.parent

    # This awesome clean code relies on short circuting to stop checking for problems
    # when a less specific error is detected
    if check_bone_has_n_datarefs(drag_axis_bone,1,"location",log_errors) and\
       check_bone_is_animated_for_translation(drag_axis_bone, log_errors)  and\
       check_keyframe_translation_eq_count(drag_axis_bone, count=2, exclude_clamping=True) and\
       check_bone_is_not_animated_for_rotation(drag_axis_bone, log_errors):
        return drag_axis_bone
    else:
        return None


def get_rotation_bone(manipulator: 'XPlaneManipulator',log_errors:bool=True) -> XPlaneBone:
    '''
    Gets the rotation bone. The bone must be animated for rotation. manipulator.type must be
    MANIP_DRAG_ROTATE or MANIP_DRAG_ROTATE_DETENT
    '''
    if manipulator.type == MANIP_DRAG_ROTATE:
        bone = manipulator.xplanePrimative.xplaneBone
        # This is guaranteed to be true by isDataRefAnimatedForRotation\
        # check_keyframe_rotation_ge_count(bone, 2, True, True), so it won't be checked
        # before _on_n_axes
        if check_bone_is_animated_for_rotation(bone, log_errors) and\
           check_bone_has_n_datarefs(bone, 1, "rotation", log_errors) and\
           check_bone_is_animated_on_n_axes(bone,1,True)  and\
           check_keyframes_rotation_are_orderered(bone, True):
            return bone
        else:
            return None
        
    if manipulator.type == MANIP_DRAG_ROTATE_DETENT:
        bone = manipulator.xplanePrimative.xplaneBone
        if check_bone_has_parent(bone,log_errors) and\
           check_bone_parent_is_animated_for_rotation(bone, log_errors) and\
           check_bone_has_n_datarefs(bone.parent, 1, "rotation", log_errors) and\
           check_bone_is_animated_on_n_axes(bone.parent,1,True)  and\
           check_keyframes_rotation_are_orderered(bone.parent, True):
            return bone.parent
        else:
            return None
    
    assert False, "Unimplemented or wrong manipulator type {} used".format(manipulator.type)


def get_translation_bone(manipulator: 'XPlaneManipulator',log_errors:bool=True) -> XPlaneBone:
    '''
    Gets the detent_bone or translation bone. manip.type must be MANIP_AXIS_DETENT or MANIP_DRAG_ROTATE_DETENT
    
    The bone must
        - have an animated translation/rotation_bone for a parent
        - have exactly 1 dataref
        - be animated for translation
        - have two non-clamping location keyframes
        - not be animated for rotation
    '''
    
    bone = manipulator.xplanePrimative.xplaneBone
    if manipulator.type == MANIP_DRAG_AXIS_DETENT:
        if not check_bone_has_parent(bone,log_errors):
            return None

    if manipulator.type == MANIP_DRAG_ROTATE_DETENT:
        if not get_rotation_bone(manipulator, log_errors):
            return None

    if manipulator.type == MANIP_DRAG_AXIS_DETENT or\
       manipulator.type == MANIP_DRAG_ROTATE_DETENT:
        # This awesome clean code relies on short circuting to stop checking for problems
        # when a less specific error is detected
        if check_bone_has_n_datarefs(bone,1,"location",log_errors) and\
           check_bone_is_animated_for_translation(bone, log_errors)  and\
           check_keyframe_translation_eq_count(bone,count=2, exclude_clamping=True) and\
           check_bone_is_not_animated_for_rotation(bone, log_errors) and\
           check_manip_has_axis_detent_ranges(manipulator,log_errors):
            return bone
        else:
            return None

    assert False, "Unimplemented or wrong manipulator type {} used".format(manipulator.type)


# This is a pseudo-XPlaneObject that only has a collect method
# It's refrenced xplanePrimative provides the rest of the XPlaneObject
class XPlaneManipulator():
    def __init__(self, xplanePrimative):
        assert xplanePrimative is not None

        self.manip = xplanePrimative.blenderObject.xplane.manip
        self.type = self.manip.get_effective_type_id()
        self.xplanePrimative = xplanePrimative

    def collect(self):
        attr = 'ATTR_manip_'
        value = True

        if self.manip.enabled:
            attr += self.type

            if self.type == MANIP_DRAG_XY:
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
            elif self.type == MANIP_DRAG_AXIS:
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
            elif self.type == MANIP_DRAG_AXIS_PIX:
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
            elif self.type == MANIP_DRAG_AXIS_DETENT:
                # Semantically speaking we don't have a new manipulator type. The magic is in ATTR_axis_detented
                attr = "ATTR_manip_" + MANIP_DRAG_AXIS
                '''
                Drag Axis/Drag Axis With Detents
                Empty/Bone -> Main drag axis animation and (optionally) v1_min/max for validating axis_detent_ranges
                |_Child mesh -> Manipulator settings and (optionally) detent axis animation

                Common Rules:
                - *Animations must only be driven by only 1 dataref
                - *Animations must have exactly 2 (non-clamping) keyframes

                Special rules for the Detent Bone:
                - Must be a leaf bone (checked in XPlanePrimative.write)
                - * Must have a parent with translation
                - * The positions at each keyframe must not be the same, including both being 0
                - The parent and translation animations are orthogonal

                * (guarenteed by get_tranlation_bone)
                '''
                drag_axis_bone = get_drag_axis_bone(self,log_errors=True)
                detent_axis_bone = None

                if drag_axis_bone:
                    detent_axis_bone = get_translation_bone(self, log_errors=True)

                if drag_axis_bone is None or detent_axis_bone is None:
                    logger.error("{} is invalid: {} manipulators have specific parent-child relationships and animation requirements."
                                 " See online manipulator documentation for examples.".format(
                                      self.xplanePrimative.blenderObject.name,
                                      self.manip.get_effective_type_name()))
                    return

                #bone.animations - <DataRef,List<KeyframeCollection>>
                drag_axis_dataref = next(iter(drag_axis_bone.animations))
                drag_axis_frames_cleaned = next(iter(drag_axis_bone.animations.values())).getTranslationKeyframeTableNoClamps()
                drag_axis_b = drag_axis_frames_cleaned[1].location - drag_axis_frames_cleaned[0].location
                drag_axis_xp = xplane_helpers.vec_b_to_x(drag_axis_b)
                drag_axis_dataref_values = (drag_axis_frames_cleaned[0].value, drag_axis_frames_cleaned[1].value)

                lift_at_max = get_lift_at_max(detent_axis_bone)
                if round(lift_at_max,5) == 0.0:
                    logger.error("{}'s detent animation has keyframes but no change between them".format(
                        detent_axis_bone.getBlenderName()))
                    return
                if not check_bones_drag_detent_are_orthogonal(drag_axis_bone, detent_axis_bone):
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
            elif self.type == MANIP_DRAG_ROTATE or self.type == MANIP_DRAG_ROTATE_DETENT:
                attr = "ATTR_manip_" + MANIP_DRAG_ROTATE
                '''
                Drag rotate manipulators must follow either one of two patterns
                1. The manipulator is attached to a translating XPlaneBone which has a rotating parent bone (MANIP_DRAG_ROTATE_DETENT)
                2. The manipulator is attached to a rotation bone (MANIP_DRAG_ROTATE)

                Common (and guaranteed by get_rotation_bone and get_translation_bone)
                - *If a bone is used, it must be animated
                - *Animations must be driven by exactly 1 dataref

                Special rules for the Rotation Bone:
                - Can only be rotated around one axis, no matter the rotation mode
                - Rotation keyframe tables must be sorted in ascending or decending order
                - Rotation keyframe table must have at least 2 non-clamping rotation keyframes
                - 0 degree rotation not allowed (taken care of by isDataRefAnimatedForRotation)
                - Clockwise and counterclockwise rotations are supported

                Special rules for Translation Bone:
                - Must be a leaf bone (checked in XPlanePrimative.write)
                - *Must have a parent with rotation 
                - *Cannot have rotation keyframes
                - *Must have exactly 2 (non-clamping) keyframes
                - Must not animate along rotation bone's axis
                - The positions at each keyframe must not be the same, including both being 0
                - Axis Detent ranges are mandatory (see validate_axis_detent_ranges)

                 * (guaranteed by get_translation_bone)
                '''
                rotation_bone = get_rotation_bone(self,log_errors=True)
                translation_bone = None
                lift_at_max = 0.0

                if self.type == MANIP_DRAG_ROTATE_DETENT and rotation_bone:
                    translation_bone = get_translation_bone(self,log_errors=True)

                    if translation_bone:
                        lift_at_max = get_lift_at_max(translation_bone)
                        if round(lift_at_max,5) == 0.0:
                            logger.error("{}'s detent animation has keyframes but no change between them".format(
                                translation_bone.getBlenderName()))
                            return
                elif self.type == MANIP_DRAG_ROTATE and rotation_bone:
                    pass
                
                if (self.type == MANIP_DRAG_ROTATE and not rotation_bone) or\
                   (self.type == MANIP_DRAG_ROTATE_DETENT and not translation_bone):

                    logger.error("{} is invalid: {} manipulators have specific parent-child relationships and animation requirements."
                                 " See online manipulator documentation for examples.".format(
                                      self.xplanePrimative.blenderObject.name,
                                      self.manip.get_effective_type_name()))
                    return

                if translation_bone is None:
                    v2_min = 0.0
                    v2_max = 0.0
                else:
                    if not check_bones_rotation_translation_animations_are_orthogonal(rotation_bone,translation_bone):
                        return
                    v2_min = 0.0
                    v2_max = lift_at_max

                if self.manip.autodetect_datarefs:
                    self.manip.dataref1 = next(iter(rotation_bone.datarefs))
                    if translation_bone is not None:
                        self.manip.dataref2 = next(iter(translation_bone.datarefs))
                    else:
                        self.manip.dataref2 = "none"

                rotation_origin = rotation_bone.getBlenderWorldMatrix().to_translation()

                rotation_keyframe_table_cleaned =\
                    next(iter(rotation_bone.animations.values()))\
                    .asAA()\
                    .getRotationKeyframeTableNoClamps()

                rotation_axis = rotation_keyframe_table_cleaned[0][0]

                rotation_origin_xp = xplane_helpers.vec_b_to_x(rotation_origin)
                rotation_axis_xp   = xplane_helpers.vec_b_to_x(rotation_axis)

                v1_min, angle1 = rotation_keyframe_table_cleaned[0][1][0]
                v1_max, angle2 = rotation_keyframe_table_cleaned[0][1][-1]

                if round(angle1,5) == round(angle2,5):
                    # Because of the previous guarantees that
                    # - Keyframes must be different
                    # - Keyframes must be in ascending and decending order
                    # this is impossible to reach, but is included as a guard against regression
                    # logger.error("0 degree rotation on {} not allowed".format(
                    #    rotation_bone.getBlenderName()))
                    assert False, "How did we get here?"
                    return

                if v1_min == v1_max:
                    logger.error("{}'s Dataref 1's minimum cannot equal Dataref 1's maximum".format(
                        rotation_bone.getBlenderName()))
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
            elif self.type == MANIP_COMMAND:
                value = (self.manip.cursor, self.manip.command, self.manip.tooltip)
            elif self.type == MANIP_COMMAND_AXIS:
                value = (
                    self.manip.cursor,
                    self.manip.dx,
                    self.manip.dy,
                    self.manip.dz,
                    self.manip.positive_command,
                    self.manip.negative_command,
                    self.manip.tooltip
                )
            elif self.type in (MANIP_COMMAND_KNOB, MANIP_COMMAND_SWITCH_UP_DOWN, MANIP_COMMAND_SWITCH_LEFT_RIGHT):
                value = (
                    self.manip.cursor,
                    self.manip.positive_command,
                    self.manip.negative_command,
                    self.manip.tooltip
                )
            elif self.type in (MANIP_COMMAND_KNOB2, MANIP_COMMAND_SWITCH_UP_DOWN2, MANIP_COMMAND_SWITCH_LEFT_RIGHT2):
                value = (
                    self.manip.cursor,
                    self.manip.command,
                    self.manip.tooltip
                )
            elif self.type == MANIP_PUSH:
                value = (
                    self.manip.cursor,
                    self.manip.v_down,
                    self.manip.v_up,
                    self.manip.dataref1,
                    self.manip.tooltip
                )
            elif self.type == MANIP_RADIO:
                value = (
                    self.manip.cursor,
                    self.manip.v_down,
                    self.manip.dataref1,
                    self.manip.tooltip
                )
            elif self.type == MANIP_TOGGLE:
                value = (
                    self.manip.cursor,
                    self.manip.v_on,
                    self.manip.v_off,
                    self.manip.dataref1,
                    self.manip.tooltip
                )
            elif self.type in (MANIP_DELTA, MANIP_WRAP):
                value = (
                    self.manip.cursor,
                    self.manip.v_down,
                    self.manip.v_hold,
                    self.manip.v1_min,
                    self.manip.v1_max,
                    self.manip.dataref1,
                    self.manip.tooltip
                )
            elif self.type in (MANIP_AXIS_SWITCH_UP_DOWN, MANIP_AXIS_SWITCH_LEFT_RIGHT):
                value = (
                    self.manip.cursor,
                    self.manip.v1,
                    self.manip.v2,
                    self.manip.click_step,
                    self.manip.hold_step,
                    self.manip.dataref1,
                    self.manip.tooltip
                )
            elif self.type == MANIP_NOOP:
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
            if (self.type == MANIP_DRAG_AXIS_DETENT) and ver_ge_1100:
                if self.manip.autodetect_datarefs:
                    detent_axis_dataref = self.manip.dataref2
                else:
                    detent_axis_dataref = next(iter(detent_axis_bone.animations))

                detent_axis_frames_cleaned = next(iter(detent_axis_bone.animations.values())).getTranslationKeyframeTableNoClamps()
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
            if (self.type == MANIP_DRAG_AXIS_DETENT or MANIP_DRAG_ROTATE_DETENT) and ver_ge_1100:
                
                #List[AxisDetentRange] -> bool
                def validate_axis_detent_ranges(axis_detent_ranges, translation_bone, v1_min, v1_max, lift_at_max):
                    '''
                    Rules for Axis Detent Ranges

                    Basic rules
                    - Manip type must be *_DETENT
                    - Translation bone must not be none (covered by get_translation_bone), len(axis_detent_ranges) > 0
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
                    if not len(axis_detent_ranges) > 0:
                        logger.error("Must {} have axis detent range if manipulator type is {}".format(
                            translation_bone.getBlenderName(),
                            self.manip.get_effective_type_name()))
                        return False

                    if not axis_detent_ranges[0].start == v1_min:
                        logger.error("Axis detent range list for {} must start at Dataref 1's minimum value {}".format(
                            translation_bone.getBlenderName(),
                            v1_min))
                        return False

                    if not axis_detent_ranges[-1].end == v1_max:
                        logger.error("Axis detent range list for {} must end at Dataref 1's maximum value {}".format(
                            translation_bone.getBlenderName(),
                            v1_max))
                        return False

                    if len({range.height for range in axis_detent_ranges}) == 1:
                        logger.warn("All axis detent ranges for {} have the same height. Check your entered data".format(
                            translation_bone.getBlenderName()))

                    for i in range(len(axis_detent_ranges)):
                        detent_range = axis_detent_ranges[i]
                        if not detent_range.start <= detent_range.end:
                            logger.error(
                                "The start of axis detent range {} on {} must be less than or equal to its end".format(
                                    detent_range,
                                    translation_bone.getBlenderName())
                                )
                            return False

                        if not 0.0 <= detent_range.height <= lift_at_max:
                            logger.error(
                                "Height in axis detent range {} on {} must be between 0.0 and the maximum lift height ({})".format(
                                    detent_range,
                                    translation_bone.getBlenderName(),
                                    lift_at_max))
                            return False

                        # Pit detection portion
                        if len(axis_detent_ranges) == 1 and detent_range.start == detent_range.end:
                            logger.error("Axis detent range on {} cannot have stop pit with only one detent".format(
                                         translation_bone.getBlenderName()))
                            return False

                        AxisDetentStruct = collections.namedtuple("AxisDetentStruct", ['start','end','height'])
                        try:
                            detent_range_next = axis_detent_ranges[i+1]
                        except:
                            detent_range_next = AxisDetentStruct(detent_range.end, v1_max, float('inf'))


                        if not detent_range.end == detent_range_next.start:
                            logger.error("In {}'s axis detent range list, the start of a detent range must be the end of the previous detent range {},{}".format(
                                translation_bone.getBlenderName(),
                                detent_range,
                                (detent_range_next.start,detent_range_next.end,detent_range.height)))
                            return False

                        try:
                            detent_range_prev = axis_detent_ranges[i-1]
                        except:
                            detent_range_prev = AxisDetentStruct(v1_min, detent_range.start, float('inf'))

                        if detent_range.start == detent_range.end and\
                           not detent_range_prev.height > detent_range.height < detent_range_next.height:
                            logger.error("Stop pit created by {}'s detent range {} must be lower than"
                                         " previous {} and next detent ranges {}".format(
                                             translation_bone.getBlenderName(),
                                            (detent_range),
                                            (detent_range_prev.start,detent_range_prev.end,detent_range.height),
                                            (detent_range_next.start,detent_range_next.end,detent_range_next.height))
                                         )
                            return False

                    return True

                if len(self.manip.axis_detent_ranges) > 0:
                    if self.type == MANIP_DRAG_AXIS_DETENT:
                        translation_bone = detent_axis_bone
                    if not validate_axis_detent_ranges(self.manip.axis_detent_ranges, translation_bone, v1_min, v1_max, lift_at_max):
                        return

                for axis_detent_range in self.manip.axis_detent_ranges:
                    self.xplanePrimative.cockpitAttributes.add(XPlaneAttribute('ATTR_axis_detent_range',
                        (axis_detent_range.start, axis_detent_range.end, axis_detent_range.height)))

            # 4. All ATTR_manip_keyframes (DRAG_ROTATE)
            if self.type == MANIP_DRAG_ROTATE or self.type == MANIP_DRAG_ROTATE_DETENT:
                if len(rotation_keyframe_table_cleaned[0][1]) > 2:
                    for rot_keyframe in rotation_keyframe_table_cleaned[0][1][1:-1]:
                        self.xplanePrimative.cockpitAttributes.add(
                            XPlaneAttribute('ATTR_manip_keyframe', (rot_keyframe.value,rot_keyframe.degrees))
                        )
            # add mouse wheel delta
            if self.type in MOUSE_WHEEL_MANIPULATORS and bpy.context.scene.xplane.version >= VERSION_1050 and self.manip.wheel_delta != 0:
                self.xplanePrimative.cockpitAttributes.add(XPlaneAttribute('ATTR_manip_wheel', self.manip.wheel_delta))
