"""
Created on Jan 30, 2018

@author: Ted
"""

import collections
import typing
from typing import Callable, List, Optional, Tuple

import bpy
from mathutils import Vector

from io_xplane2blender import xplane_helpers
from io_xplane2blender.xplane_constants import *
from io_xplane2blender.xplane_helpers import logger
from io_xplane2blender.xplane_props import (
    XPlaneAxisDetentRange,
    XPlaneManipulatorSettings,
)
from io_xplane2blender.xplane_types.xplane_attribute import XPlaneAttribute
from io_xplane2blender.xplane_types.xplane_bone import XPlaneBone
from io_xplane2blender.xplane_types.xplane_keyframe import XPlaneKeyframe
from io_xplane2blender.xplane_types.xplane_keyframe_collection import (
    XPlaneKeyframeCollection,
)


def round_vector(vec, ndigits=5) -> Vector:
    return Vector([round(comp, ndigits) for comp in vec])


"""
Some of these check_* methods break the rule of "no side effects in a boolean expression" when log_errors = True
However, without this, the logic must be duplicated, making it, in my opinion, worth it.

In addition, in order to give better error messages, some less used aspects of the data model are used. For instance,
using bone.datarefs instead of bone.animations for check_bone_has_n_datarefs
"""


def check_bone_has_n_datarefs(
    bone: XPlaneBone,
    num_datarefs: int,
    anim_type: str,
    log_errors: bool = True,
    manipulator: "XPlaneManipulator" = None,
) -> bool:
    """
    Checks animations dict, not datarefs dictionary because we're looking for the actual animation
    that will be considered for the OBJ, and the datarefs dictionary is not guaranteed to be semantically
    the same thing.
    """
    if log_errors:
        assert manipulator

    assert bone

    if len(bone.datarefs) != num_datarefs:
        try:
            if log_errors:
                logger.error(
                    "The {} animation for the {} manipulator attached to {} must have exactly {} datarefs for its animation".format(
                        anim_type,
                        manipulator.manip.get_effective_type_name(),
                        bone.getBlenderName(),
                        num_datarefs,
                    )
                )
        except:
            if log_errors:
                logger.error(
                    "The {} animation for {} must have exactly {} datarefs for its animation".format(
                        anim_type, bone.getBlenderName(), num_datarefs
                    )
                )

        return False
    else:
        return True


def check_bone_has_parent(
    bone: XPlaneBone, log_errors: bool = True, manipulator: "XPlaneManipulator" = None
) -> bool:
    if log_errors:
        assert manipulator

    if bone.parent is None:
        if log_errors:
            logger.error(
                "{} manipulator attached to {} must have a parent".format(
                    manipulator.manip.get_effective_type_name(), bone.getblendername()
                )
            )
        return False
    else:
        return True


def check_bone_is_animated_for_rotation(
    bone: XPlaneBone, log_errors: bool = True, manipulator: "XPlaneManipulator" = None
) -> bool:
    """
    Returns true if bone has at least two rotation keyframes that are different
    """
    if log_errors:
        assert manipulator

    assert bone is not None

    # Unfortunately this does not answer if we have one rotation keyframe, which, semantically
    # we are checking for. This makes us never able to really get a good error message for
    # "test_5_must_have_at_least_2_non_clamping_keyframes  See bug #333
    #
    # While it would nice to use the RotationKeyframeTable, we don't know if that can
    # be generated yet, a call to getReferenceAxes could fail if forced
    if not bone.isDataRefAnimatedForRotation():
        if log_errors:
            logger.error(
                "{} manipulator attached to {} must have at least 2 rotation keyframes that are not the same".format(
                    manipulator.manip.get_effective_type_name(), bone.getBlenderName()
                )
            )
        return False
    else:
        return True


def check_bone_is_animated_for_translation(
    bone: XPlaneBone, log_errors: bool = True, manipulator: "XPlaneManipulator" = None
) -> bool:
    """
    Returns true if bone has at least two translation keyframes that are different
    """
    if log_errors:
        assert manipulator

    assert bone is not None
    if not bone.isDataRefAnimatedForTranslation():
        if log_errors:
            logger.error(
                "{} manipulator attached to {} must have at least 2 translation keyframes that are not the same".format(
                    manipulator.manip.get_effective_type_name(), bone.getBlenderName()
                )
            )
        return False
    else:
        return True


def check_bone_is_animated_on_n_axes(
    bone: XPlaneBone,
    num_axis_of_rotation: int,
    log_errors: bool = True,
    manipulator: "XPlaneManipulator" = None,
) -> bool:
    if log_errors:
        assert manipulator

    rotation_keyframe_table = next(
        iter(bone.animations.values())
    ).getRotationKeyframeTables()

    if len(rotation_keyframe_table) == 3:
        deg_per_axis = []
        for axis, table in rotation_keyframe_table:
            deg_per_axis.append(sum([abs(keyframe.degrees) for keyframe in table]))

        real_num_axis_of_rotation = len(
            (
                *filter(
                    lambda total_rotations: round(total_rotations, 8) != 0.0,
                    deg_per_axis,
                ),
            )
        )
    else:
        real_num_axis_of_rotation = len(rotation_keyframe_table)

    # The sum of the degrees rotated along each axis over every keyframe sorted from lowest-to-highest
    # should be 0,0,T. Having a second or all three rotating would mean that at least the second entry would be not 0
    if real_num_axis_of_rotation != num_axis_of_rotation:
        if log_errors:
            logger.error(
                "{} manipulator attached to {} can only rotate around {} axis".format(
                    manipulator.manip.get_effective_type_name(),
                    bone.getBlenderName(),
                    num_axis_of_rotation,
                )
            )
        return False
    else:
        return True


def check_bone_is_leaf(
    bone: XPlaneBone, log_errors: bool = True, manipulator: "XPlaneManipulator" = None
) -> bool:
    if log_errors:
        assert manipulator

    if len(bone.children) > 0:
        if log_errors:
            logger.error(
                "{} manipulator attached to {} must have no children".format(
                    manipulator.manip.get_effective_type_name(), bone.getBlenderName()
                )
            )
        return False
    else:
        return True


def check_bone_is_not_animated_for_rotation(
    bone: XPlaneBone, log_errors: bool = True, manipulator: "XPlaneManipulator" = None
) -> bool:
    if log_errors:
        assert manipulator

    if check_bone_is_animated_for_rotation(bone, log_errors=False):
        if log_errors:
            logger.error(
                "{} manipulator attached to {} must not have rotation keyframes".format(
                    manipulator.manip.get_effective_type_name(), bone.getBlenderName()
                )
            )
        return False
    else:
        return True


def check_bone_is_not_animated_for_translation(
    bone: XPlaneBone, log_errors: bool = True, manipulator: "XPlaneManipulator" = None
) -> bool:
    if log_errors:
        assert manipulator

    if check_bone_is_animated_for_translation(bone, log_errors, manipulator):
        if log_errors:
            logger.error(
                "{} manipulator attached to {} must not have location keyframes".format(
                    manipulator.manip.get_effective_type_name(), bone.getBlenderName()
                )
            )
        return False
    else:
        return True


def check_bone_parent_is_animated_for_rotation(
    bone: XPlaneBone, log_errors: bool = True
) -> bool:
    assert bone.parent
    if not check_bone_is_animated_for_rotation(bone.parent, False):
        if log_errors:
            logger.error(
                "{}'s parent {} must be animated with rotation".format(
                    bone.getBlenderName(), bone.parent.getBlenderName()
                )
            )
        return False
    else:
        return True


def check_bone_parent_is_animated_for_translation(
    bone: XPlaneBone, log_errors: bool = True
) -> bool:
    assert bone.parent
    if not check_bone_is_animated_for_translation(bone.parent, log_errors, manipulator):
        if log_errors:
            logger.error(
                "{}'s parent {} must be animated with location keyframes".format(
                    bone.getBlenderName(), bone.parent.getBlenderName()
                )
            )
        return False
    else:
        return True


def check_bones_drag_detent_are_orthogonal(
    drag_axis_bone: XPlaneBone,
    detent_bone: XPlaneBone,
    log_errors=True,
    manipulator: "XPlaneManipulator" = None,
) -> bool:
    if log_errors:
        assert manipulator

    drag_axis_translation_keyframe_table = next(
        iter(drag_axis_bone.animations.values())
    ).getTranslationKeyframeTable()

    detent_axis_translation_keyframe_table = next(
        iter(detent_bone.animations.values())
    ).getTranslationKeyframeTable()

    # Assuming that these are only rotating on a single axis
    drag_axis = (
        drag_axis_translation_keyframe_table[-1].location
        - drag_axis_translation_keyframe_table[0].location
    )
    detent_axis = (
        detent_axis_translation_keyframe_table[-1].location
        - detent_axis_translation_keyframe_table[0].location
    )

    dot_product = drag_axis.dot(detent_axis)

    if not -0.01 < dot_product < 0.01 and log_errors:
        logger.error(
            "Location animation for the {} manipulator attached to {} must not be along the main drag animation axis".format(
                manipulator.manip.get_effective_type_name(),
                detent_bone.getBlenderName(),
            )
        )
        return False
    else:
        return True


# X-Plane note: X-Plane implements the Drag Rotate manipulator using a system akin to polar co-ordinates.
# If the rotation axis is on Z, the detent can be draged any where in XY space. This will be translated into polar co-ordinates
# as angle, and distance is the distance draged from the origin.
# If the detent animation is animated at al on the Z axis, X-Plane won't drag there and it'll be a broken manipulator
#
# To detect this, we take the dot product between the rotation and detent axis to discover if there is any component along that axis
def check_bones_rotation_translation_animations_are_orthogonal(
    rotation_bone: XPlaneBone,
    child_bone: XPlaneBone,
    log_errors=True,
    manipulator: "XPlaneManipulator" = None,
) -> bool:
    if log_errors:
        assert manipulator

    rotation_keyframe_table = (
        next(iter(rotation_bone.animations.values())).asAA().getRotationKeyframeTables()
    )

    rotation_axis = rotation_keyframe_table[0][0]

    child_values_cleaned = next(
        iter(child_bone.animations.values())
    ).getTranslationKeyframeTableNoClamps()

    child_axis = child_values_cleaned[1][1] - child_values_cleaned[0][1]

    dot_product = child_axis.dot(rotation_axis)
    if not -0.01 < dot_product < 0.01:
        logger.error(
            "Location animation for the {} manipulator attached to {} must not be along the rotation animation axis".format(
                manipulator.manip.get_effective_type_name(), child_bone.getBlenderName()
            )
        )
        return False
    else:
        return True


def _check_keyframe_translation_count(
    translation_bone: XPlaneBone,
    count: int,
    exclude_clamping: bool,
    cmp_func,
    cmp_error_msg: str,
    log_errors: bool = True,
    manipulator: "XPlaneManipulator" = None,
) -> bool:
    if log_errors:
        assert manipulator

    keyframe_col = next(iter(translation_bone.animations.values()))

    if exclude_clamping:
        res = cmp_func(len(keyframe_col.getTranslationKeyframeTableNoClamps()), count)
    else:
        res = cmp_func(len(keyframe_col.getTranslationKeyframeTable()), count)

    if not res:
        try:
            if log_errors:
                logger.error(
                    "{} manipulator attached to {} must have {} {} {}keyframes for its location animation".format(
                        manipulator.manip.get_effective_type_name(),
                        translation_bone.getBlenderName(),
                        cmp_error_msg,
                        count,
                        "non-clamping " if exclude_clamping else "",
                    )
                )
        except:
            if log_errors:
                logger.error(
                    "{} must have {} {} {}keyframes for its location animation".format(
                        translation_bone.getBlenderName(),
                        cmp_error_msg,
                        count,
                        "non-clamping " if exclude_clamping else "",
                    )
                )

        return False
    else:
        return True


def check_keyframe_translation_eq_count(
    translation_bone: XPlaneBone,
    count: int,
    exclude_clamping: bool,
    log_errors: bool = True,
    manipulator: "XPlaneManipulator" = None,
) -> bool:
    return _check_keyframe_translation_count(
        translation_bone,
        count,
        exclude_clamping,
        lambda x, y: x == y,
        "exactly",
        log_errors,
        manipulator,
    )


def check_keyframe_translation_ge_count(
    translation_bone: XPlaneBone,
    count: int,
    exclude_clamping: bool,
    log_errors: bool = True,
    manipulator: "XPlaneManipulator" = None,
) -> bool:
    return _check_keyframe_translation_count(
        translation_bone,
        count,
        exclude_clamping,
        lambda x, y: x >= y,
        "greater than or equal to",
        log_errors,
        manipulator,
    )


def check_keyframes_rotation_are_orderered(
    rotation_bone: XPlaneBone,
    log_errors: bool = True,
    manipulator: "XPlaneManipulator" = None,
) -> bool:
    if log_errors:
        assert manipulator

    rotation_keyframe_table = (
        next(iter(rotation_bone.animations.values())).asAA().getRotationKeyframeTables()
    )

    rotation_axis = rotation_keyframe_table[0][0]
    rotation_keyframe_data = rotation_keyframe_table[0][1]
    if not (
        rotation_keyframe_data == sorted(rotation_keyframe_data)
        or rotation_keyframe_data == sorted(rotation_keyframe_data, reverse=True)
    ):
        if log_errors:
            logger.error(
                "Rotation dataref values for the {} manipulator attached to {} are not in ascending or descending order".format(
                    manipulator.manip.get_effective_type_name(),
                    rotation_bone.getBlenderName(),
                )
            )
        return False
    else:
        return True


def check_manip_has_axis_detent_ranges(
    manipulator: "XPlaneManipulator", log_errors: bool = True
) -> bool:
    assert (
        manipulator.type == MANIP_DRAG_AXIS_DETENT
        or manipulator.type == MANIP_DRAG_ROTATE_DETENT
    )

    if not manipulator.manip.axis_detent_ranges:
        if log_errors:
            logger.error(
                "{} manipulator attached to {} must have axis detent ranges".format(
                    manipulator.type,
                    manipulator.xplanePrimative.xplaneBone.getBlenderName(),
                )
            )
        return False
    else:
        return True


def find_armature_datablock(bone: XPlaneBone) -> Optional[bpy.types.Object]:
    if bone is not None:
        if bone.blenderObject.type == "ARMATURE":
            return bone
        else:
            return find_armature_datablock(bone.parent)
    else:
        return None


def get_lift_at_max(translation_bone: XPlaneBone) -> float:
    translation_values_cleaned = next(
        iter(translation_bone.animations.values())
    ).getTranslationKeyframeTableNoClamps()
    return (
        translation_values_cleaned[1][1] - translation_values_cleaned[0][1]
    ).magnitude


def check_spec_drag_axis_bone(
    drag_axis_bone: XPlaneBone,
    log_errors: bool = True,
    manipulator: "XPlaneManipulator" = None,
) -> bool:
    """
    Checks the drag_axis_bone. manip.type must be MANIP_AXIS_DETENT
    The bone must
        - have exactly 1 dataref
        - be animated for translation
        - have two non-clamping location keyframes
        - not be animated for rotation
    """
    if log_errors:
        assert manipulator

    # This awesome clean code relies on short circuting to stop checking for problems
    # when a less specific error is detected
    if (
        drag_axis_bone
        and check_bone_has_n_datarefs(
            drag_axis_bone, 1, "location", log_errors, manipulator
        )
        and check_bone_is_animated_for_translation(
            drag_axis_bone, log_errors, manipulator
        )
        and check_keyframe_translation_eq_count(
            drag_axis_bone,
            count=2,
            exclude_clamping=True,
            log_errors=True,
            manipulator=manipulator,
        )
        and check_bone_is_not_animated_for_rotation(
            drag_axis_bone, log_errors, manipulator
        )
    ):
        return drag_axis_bone
    else:
        return None


def get_information_sources(
    manipulator: "XPlaneManipulator",
    white_list: Tuple[
        Tuple[
            Callable[[XPlaneBone, Optional[bool], Optional["XPlaneManipulator"]], bool],
            str,
        ]
    ],
    black_list: Tuple[
        Tuple[
            Callable[[XPlaneBone, Optional[bool], Optional["XPlaneManipulator"]], bool],
            str,
        ]
    ],
    log_errors: bool = True,
) -> Optional[List[XPlaneBone]]:
    """
    Starting at the manipulator's bone, walk up the tree of parents, ignoring bones that are completely unanimated,
    and testing animated bones that they're in the right sequence with the right types.

    Bones are checked against white_list and black_list predicates. For each bone, the white_list function and black_list must return True and False.  These functions must match the signature of
        def check_something(bone:XPlaneBone,log_errors:bool,manipulator:'XPlaneManipulator')->bool
    All logger errors will always be surpressed

    The 2nd part of the tuple is the type of animation it is testing. Currently this is just "location" or "rotation"

    Returns a list of collected bones or None if there was an error
    """

    def find_next_animated_bone(bone: XPlaneBone):
        # Note the use of blenderObject.xplane.datarefs, as opposed to bone.datarefs!
        while bone is not None:
            if bone.blenderBone is None:
                if len(bone.animations.values()) > 0 or (
                    bone.blenderObject
                    and list(
                        filter(
                            lambda d: d.anim_type == ANIM_TYPE_TRANSFORM,
                            bone.blenderObject.xplane.datarefs,
                        )
                    )
                ):
                    break
            else:
                if len(bone.animations.values()) > 0 or list(
                    filter(
                        lambda d: d.anim_type == ANIM_TYPE_TRANSFORM,
                        bone.blenderBone.xplane.datarefs,
                    )
                ):
                    break

            bone = bone.parent

        return bone

    def log_error(
        manipulator: "XPlaneManipulator",
        white_list: Tuple[
            Tuple[
                Callable[
                    [XPlaneBone, Optional[bool], Optional["XPlaneManipulator"]], bool
                ],
                str,
            ]
        ],
        black_list: Tuple[
            Tuple[
                Callable[
                    [XPlaneBone, Optional[bool], Optional["XPlaneManipulator"]], bool
                ],
                str,
            ]
        ],
        collected_bones: List[XPlaneBone],
        last_index: int,  # Since we allow gaps in the parent-child chain, idx != last_bone
        last_bone_examined: XPlaneBone,
        last_white_result: bool,
        last_black_result: bool,
    ):

        # Something, anything, has to be wrong in some way or this shouldn't have been called!
        assert (
            len(collected_bones) != len(white_list)
            or last_white_result
            or last_black_result
        )

        error_header = "Requirements for {manip_type} manipulator on '{manipulator_name}' are not met".format(
            manip_type=manipulator.manip.get_effective_type_name(),
            manipulator_name=manipulator.xplanePrimative.xplaneBone.getName(
                ignore_indent_level=True
            ),
        )

        type_requirements = """
Manipulator Type Requirements:
-----------------------------
"""
        type_requirements += "'{manip_type}' manipulators must have a {anim_type_white} animation or be a child of a {anim_type_white} animation".format(
            manip_type=manipulator.manip.get_effective_type_name(),
            anim_type_white=white_list[0][1].title(),
        )

        for i in range(len(white_list)):
            if i > 0:
                type_requirements += (
                    ", which must be a child of a {anim_type_white} animation".format(
                        anim_type_white=white_list[i][1].title()
                    )
                )

        animations_found = """
Matching Animations Found:
-------------------------
"""
        animations_found_strs = []
        for i, bone_and_type in enumerate(
            zip(
                collected_bones,
                [white_list_entry[1] for white_list_entry in white_list],
            )
        ):
            animations_found_strs.append(
                "- {anim_type_white} animation found on {bone_name}".format(
                    anim_type_white=bone_and_type[1].title(),
                    bone_name=bone_and_type[0].getName(ignore_indent_level=True),
                )
            )

        if animations_found_strs:
            animations_found += "\n".join(animations_found_strs)
        else:
            animations_found += "None"

        problems_found = """
Problems Found:
--------------
Stopped searching because
"""
        problems_found_strs = []
        if not white_list_result and last_bone_examined is not None:
            problems_found_strs.append(
                "- {anim_type_white} animation was not found on {name}".format(
                    anim_type_white=white_list[idx][1].title(),
                    name=last_bone_examined.getName(ignore_indent_level=True),
                )
            )

        if black_list_result:
            problems_found_strs.append(
                "- {anim_type_black} animation was found on {name}".format(
                    anim_type_black=black_list[idx][1].title(),
                    name=last_bone_examined.getName(ignore_indent_level=True),
                )
            )

        if last_bone_examined is None:
            problems_found_strs.append(
                "- {anim_count_str} found before exporter ran out of bones to inspect".format(
                    anim_count_str=(
                        "{} animation" + ("" if len(collected_bones) == 1 else "s")
                    ).format(len(collected_bones))
                )
            )

        problems_found += "\n".join(problems_found_strs)

        solutions_found = """
Possible Solutions:
------------------
"""
        solutions_found_strs = []
        if not white_list_result and last_bone_examined is not None:
            solutions_found_strs.append(
                "- Add {anim_type_white} animation to {name}".format(
                    anim_type_white=white_list[idx][1].title(),
                    name=last_bone_examined.getName(ignore_indent_level=True),
                )
            )

        if black_list_result:
            solutions_found_strs.append(
                "- Remove {anim_type_black} animation from {name}".format(
                    anim_type_black=black_list[idx][1].title(),
                    name=last_bone_examined.getName(ignore_indent_level=True),
                )
            )
        if last_bone_examined is None:
            solutions_found_strs.append(
                "- You may have missing animations, not enough objects or bones, or have incorrectly set up your parent-child relationships"
            )

        solutions_found_strs.append(
            "- Check the Manipulator Type Requirements above and online documentation for more details"
        )
        solutions_found += "\n".join(solutions_found_strs)

        logger.error(
            error_header
            + "\n".join(
                [type_requirements, animations_found, problems_found, solutions_found]
            )
        )

    idx = 0
    collected_bones = []
    current_bone = manipulator.xplanePrimative.xplaneBone

    while current_bone is not None and idx < len(white_list):
        current_bone = find_next_animated_bone(current_bone)
        found_error = False
        white_list_result = False
        black_list_result = False
        if current_bone is None:
            found_error = True
            break
        else:
            white_list_result = white_list[idx][0](current_bone, False)
            black_list_result = black_list[idx][0](current_bone, False)

            if not white_list_result or black_list_result:
                found_error = True
                break
            else:
                collected_bones.append(current_bone)
                current_bone = current_bone.parent
                idx += 1

        if found_error and log_errors:
            break

    if (found_error or len(collected_bones) != len(white_list)) and log_errors:
        log_error(
            manipulator,
            white_list,
            black_list,
            collected_bones,
            last_index=idx,
            last_bone_examined=current_bone,
            last_white_result=white_list_result,
            last_black_result=black_list_result,
        )
        return None

    return collected_bones


def check_spec_rotation_bone(
    bone: XPlaneBone, log_errors: bool = True, manipulator=None
) -> bool:
    """
    Checks the rotation bone. bones should come in from leaf towards root:
    - R for Drag Rotate,
    - T->R for Drag Rotate With Detents.
    Bones must not be none and already checked to be animated for rotation.
    manipulator.type must be MANIP_DRAG_ROTATE or MANIP_DRAG_ROTATE_DETENT

    The bone must
        - be animated for rotation
        - have exactly 1 dataref
        - rotate on exactly 1 axis of rotation
        - keyframes are ordered
    """

    if log_errors:
        assert manipulator

    # TODO: Is this still true with new white_list functions?
    # check_keyframe_rotation_ge_count is guaranteed to be true by isDataRefAnimatedForRotation, so we skip it
    if (
        check_bone_has_n_datarefs(bone, 1, "rotation", log_errors, manipulator)
        and check_bone_is_animated_on_n_axes(bone, 1, log_errors, manipulator)
        and check_keyframes_rotation_are_orderered(bone, log_errors, manipulator)
    ):
        return True

    return False


def check_spec_detent_bone(
    detent_bone: Tuple[XPlaneBone],
    log_errors: bool = True,
    manipulator: "XPlaneManipulator" = None,
) -> bool:
    """
    Checks the detent_bone.
    - T for MANIP_AXIS_DETENT
    - T, R for MANIP_DRAG_ROTATE_DETENT
     Bones must not be none and already checked to be animated for translation
     manip.type must be MANIP_AXIS_DETENT or MANIP_DRAG_ROTATE_DETENT

    The bone must
        - have an animated translation/rotation_bone for a parent (take care of by get_information_sources)
        - have exactly 1 dataref
        - be animated for translation
        - have two non-clamping location keyframes
        - not be animated for rotation
    """

    # This awesome clean code relies on short circuting to stop checking for problems
    # when a less specific error is detected
    if (
        check_bone_has_n_datarefs(detent_bone, 1, "location", log_errors, manipulator)
        and check_bone_is_animated_for_translation(detent_bone, log_errors, manipulator)
        and check_keyframe_translation_eq_count(
            detent_bone,
            count=2,
            exclude_clamping=True,
            log_errors=True,
            manipulator=manipulator,
        )
        and check_bone_is_not_animated_for_rotation(
            detent_bone, log_errors, manipulator
        )
        and check_manip_has_axis_detent_ranges(manipulator, log_errors)
    ):
        return True
    else:
        return False


class XPlaneManipulator:
    """
    This psuedo-XPlaneObject only has a collect method,
    which validates the manipulator data and adds it to xplanePrimitive's
    cockpitAttributes list
    """

    def __init__(self, xplanePrimative: "XPlanePrimitive"):
        assert xplanePrimative is not None

        self.manip = xplanePrimative.blenderObject.xplane.manip
        self.type = self.manip.type
        self.xplanePrimative = xplanePrimative

    def collect(self) -> None:
        """
        Collect manipulator attributes. returns early if an error occured
        """
        attr = "ATTR_manip_"
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
                    self.manip.tooltip,
                )
            elif (
                self.type == MANIP_DRAG_AXIS
                and not self.manip.autodetect_settings_opt_in
            ):
                value = (
                    self.manip.cursor,
                    self.manip.dx,
                    self.manip.dy,
                    self.manip.dz,
                    self.manip.v1,
                    self.manip.v2,
                    self.manip.dataref1,
                    self.manip.tooltip,
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
                    self.manip.tooltip,
                )
            elif (
                self.type == MANIP_DRAG_AXIS and self.manip.autodetect_settings_opt_in
            ) or self.type == MANIP_DRAG_AXIS_DETENT:
                # Semantically speaking we don't have a new manipulator type. The magic is in ATTR_axis_detented
                attr = "ATTR_manip_" + MANIP_DRAG_AXIS
                """
                Drag Axis (Opt In)

                Common Rules
                - Parent must be driven by only 1 dataref
                - Parent must have exactly 2 (non-clamping) keyframes

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
                - Must have axis detent ranges

                * (guarenteed by get_tranlation_bone)
                """
                if self.type == MANIP_DRAG_AXIS:
                    white_list = ((check_bone_is_animated_for_translation, "location"),)
                    black_list = ((check_bone_is_animated_for_rotation, "rotation"),)
                elif self.type == MANIP_DRAG_AXIS_DETENT:
                    white_list = (
                        (check_bone_is_animated_for_translation, "location"),
                        (check_bone_is_animated_for_translation, "location"),
                    )
                    black_list = (
                        (check_bone_is_animated_for_rotation, "rotation"),
                        (check_bone_is_animated_for_rotation, "rotation"),
                    )

                info_sources = get_information_sources(self, white_list, black_list)
                if info_sources:
                    if self.type == MANIP_DRAG_AXIS:
                        assert len(info_sources) == 1 and info_sources[0]
                        drag_axis_bone = info_sources[0]
                        detent_axis_bone = None
                    elif self.type == MANIP_DRAG_AXIS_DETENT:
                        assert (
                            len(info_sources) == 2
                            and info_sources[0]
                            and info_sources[1]
                        )
                        detent_axis_bone = info_sources[0]
                        drag_axis_bone = info_sources[1]

                    if not check_spec_drag_axis_bone(
                        drag_axis_bone, log_errors=True, manipulator=self
                    ):
                        return
                else:
                    return

                # TODO: This won't appear anymore thanks to get_information_sources
                if drag_axis_bone is None or (
                    self.type == MANIP_DRAG_AXIS_DETENT and detent_axis_bone is None
                ):
                    # logger.error("{} is invalid: {} manipulators have specific parent-child relationships and animation requirements."
                    # " See online manipulator documentation for examples.".format(
                    #   self.xplanePrimative.blenderObject.name,
                    #   self.manip.get_effective_type_name()))
                    return

                # bone.animations - <DataRef,List<KeyframeCollection>>
                drag_axis_dataref = next(iter(drag_axis_bone.animations))
                drag_axis_frames_cleaned = next(
                    iter(drag_axis_bone.animations.values())
                ).getTranslationKeyframeTableNoClamps()
                drag_axis_b = (
                    drag_axis_frames_cleaned[1].location
                    - drag_axis_frames_cleaned[0].location
                )
                drag_axis_xp = xplane_helpers.vec_b_to_x(drag_axis_b)
                drag_axis_dataref_values = (
                    drag_axis_frames_cleaned[0].value,
                    drag_axis_frames_cleaned[1].value,
                )

                if detent_axis_bone:
                    if check_spec_detent_bone(
                        detent_axis_bone, log_errors=True, manipulator=self
                    ):
                        lift_at_max = get_lift_at_max(detent_axis_bone)
                        if round(lift_at_max, 5) == 0.0:
                            logger.error(
                                "{}'s detent animation has keyframes but no change between them".format(
                                    detent_axis_bone.getBlenderName()
                                )
                            )
                            return
                        if not check_bones_drag_detent_are_orthogonal(
                            drag_axis_bone,
                            detent_axis_bone,
                            log_errors=True,
                            manipulator=self,
                        ):
                            return
                    else:
                        return

                # For use when validating axis detent ranges
                v1_min = drag_axis_dataref_values[0]
                v1_max = drag_axis_dataref_values[1]

                if self.manip.autodetect_datarefs:
                    self.manip.dataref1 = drag_axis_dataref

                value = (
                    self.manip.cursor,
                    drag_axis_xp.x,
                    drag_axis_xp.y,
                    drag_axis_xp.z,
                    v1_min,
                    v1_max,
                    self.manip.dataref1,
                    self.manip.tooltip,
                )
            elif (
                self.type == MANIP_DRAG_ROTATE or self.type == MANIP_DRAG_ROTATE_DETENT
            ):
                attr = "ATTR_manip_" + MANIP_DRAG_ROTATE
                """
                Drag rotate manipulators must follow either one of two patterns
                1. The manipulator is attached to a translating XPlaneBone which has a rotating parent bone (MANIP_DRAG_ROTATE_DETENT)
                2. The manipulator is attached to a rotation bone (MANIP_DRAG_ROTATE)

                Common (and guaranteed by get_information_sources, and check_(rotation|translation)_bone)
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
                - **Cannot have rotation keyframes
                - **Must have exactly 2 (non-clamping) keyframes
                - Must not animate along rotation bone's axis
                - The positions at each keyframe must not be the same, including both being 0
                - Axis Detent ranges are mandatory (see validate_axis_detent_ranges)

                 * (guaranteed by get_information_sources)
                 ** (checked in check_detent_bone)
                """
                if self.type == MANIP_DRAG_ROTATE:
                    white_list = ((check_bone_is_animated_for_rotation, "rotation"),)
                    black_list = ((check_bone_is_animated_for_translation, "location"),)
                elif self.type == MANIP_DRAG_ROTATE_DETENT:
                    white_list = (
                        (check_bone_is_animated_for_translation, "location"),
                        (check_bone_is_animated_for_rotation, "rotation"),
                    )
                    black_list = (
                        (check_bone_is_animated_for_rotation, "rotation"),
                        (check_bone_is_animated_for_translation, "location"),
                    )

                info_sources = get_information_sources(
                    self, white_list, black_list, log_errors=True
                )

                if info_sources is None:
                    # logger.error("{} manipulator on {} is invalid. See online documentation for examples".format(
                    # self.type,
                    # self.xplanePrimative.xplaneBone))
                    return

                if self.type == MANIP_DRAG_ROTATE:
                    assert len(info_sources) == 1 and info_sources[0]
                    rotation_bone = info_sources[0]
                    translation_bone = None
                elif self.type == MANIP_DRAG_ROTATE_DETENT:
                    assert (
                        len(info_sources) == 2 and info_sources[0] and info_sources[1]
                    )
                    translation_bone = info_sources[0]
                    rotation_bone = info_sources[1]

                if not check_spec_rotation_bone(
                    rotation_bone, log_errors=True, manipulator=self
                ):
                    return

                lift_at_max = 0.0

                if self.type == MANIP_DRAG_ROTATE_DETENT and rotation_bone:
                    if check_spec_detent_bone(
                        translation_bone, log_errors=True, manipulator=self
                    ):
                        lift_at_max = get_lift_at_max(translation_bone)
                        if round(lift_at_max, 5) == 0.0:
                            logger.error(
                                "{}'s detent animation has keyframes but no change between them".format(
                                    translation_bone.getBlenderName()
                                )
                            )
                            return
                    else:
                        return

                elif self.type == MANIP_DRAG_ROTATE and rotation_bone:
                    pass

                if (self.type == MANIP_DRAG_ROTATE and not rotation_bone) or (
                    self.type == MANIP_DRAG_ROTATE_DETENT and not translation_bone
                ):

                    # TODO: This won't appear anymore thanks to get_information_sources
                    # logger.error("{} is invalid: {} manipulators have specific parent-child relationships and animation requirements."
                    # " See online manipulator documentation for examples.".format(
                    # self.xplanePrimative.blenderObject.name,
                    # self.manip.get_effective_type_name()))
                    return

                if translation_bone is None:
                    v2_min = 0.0
                    v2_max = 0.0
                else:
                    if not check_bones_rotation_translation_animations_are_orthogonal(
                        rotation_bone,
                        translation_bone,
                        log_errors=True,
                        manipulator=self,
                    ):
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
                rotation_origin_xp = xplane_helpers.vec_b_to_x(rotation_origin)

                kf_collection = next(iter(rotation_bone.animations.values()))

                # If AA, we'll find the 1st table in a list of one
                # if Euler we'll find the only table with entries
                rotation_axis, rotation_table = next(
                    sub_table
                    for sub_table in kf_collection.getRotationKeyframeTablesNoClamps()
                    if sub_table.table
                )
                rotation_axis_xp = xplane_helpers.vec_b_to_x(rotation_axis)

                v1_min, angle1 = rotation_table[0]
                v1_max, angle2 = rotation_table[-1]

                if round(angle1, 5) == round(angle2, 5):
                    # Because of the previous guarantees that
                    # - Keyframes must be different
                    # - Keyframes must be in ascending and decending order
                    # - angle1 = 0, angle2 = 360 is legal! X-Plane does in fact interpolate between them!
                    # this is impossible to reach, but is included as a guard against regression
                    # logger.error("0 degree rotation on {} not allowed".format(
                    #    rotation_bone.getBlenderName()))
                    assert False, "How did we get here?"
                    return

                if v1_min == v1_max:
                    logger.error(
                        "{}'s Dataref 1's minimum cannot equal Dataref 1's maximum".format(
                            rotation_bone.getBlenderName()
                        )
                    )
                    return

                value = (
                    self.manip.cursor,
                    rotation_origin_xp[0],  # x
                    rotation_origin_xp[1],  # y
                    rotation_origin_xp[2],  # z
                    rotation_axis_xp[0],  # dx
                    rotation_axis_xp[1],  # dy
                    rotation_axis_xp[2],  # dz
                    angle1,
                    angle2,
                    lift_at_max,
                    v1_min,
                    v1_max,
                    v2_min,
                    v2_max,
                    self.manip.dataref1,
                    self.manip.dataref2,
                    self.manip.tooltip,
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
                    self.manip.tooltip,
                )
            elif self.type in (
                MANIP_COMMAND_KNOB,
                MANIP_COMMAND_SWITCH_UP_DOWN,
                MANIP_COMMAND_SWITCH_LEFT_RIGHT,
            ):
                value = (
                    self.manip.cursor,
                    self.manip.positive_command,
                    self.manip.negative_command,
                    self.manip.tooltip,
                )
            elif self.type in (
                MANIP_COMMAND_KNOB2,
                MANIP_COMMAND_SWITCH_UP_DOWN2,
                MANIP_COMMAND_SWITCH_LEFT_RIGHT2,
            ):
                value = (self.manip.cursor, self.manip.command, self.manip.tooltip)
            elif self.type == MANIP_PUSH:
                value = (
                    self.manip.cursor,
                    self.manip.v_down,
                    self.manip.v_up,
                    self.manip.dataref1,
                    self.manip.tooltip,
                )
            elif self.type == MANIP_RADIO:
                value = (
                    self.manip.cursor,
                    self.manip.v_down,
                    self.manip.dataref1,
                    self.manip.tooltip,
                )
            elif self.type == MANIP_TOGGLE:
                value = (
                    self.manip.cursor,
                    self.manip.v_on,
                    self.manip.v_off,
                    self.manip.dataref1,
                    self.manip.tooltip,
                )
            elif self.type in (MANIP_DELTA, MANIP_WRAP):
                value = (
                    self.manip.cursor,
                    self.manip.v_down,
                    self.manip.v_hold,
                    self.manip.v1_min,
                    self.manip.v1_max,
                    self.manip.dataref1,
                    self.manip.tooltip,
                )
            elif self.type in (
                MANIP_AXIS_KNOB,
                MANIP_AXIS_SWITCH_UP_DOWN,
                MANIP_AXIS_SWITCH_LEFT_RIGHT,
            ):
                value = (
                    self.manip.cursor,
                    self.manip.v1,
                    self.manip.v2,
                    self.manip.click_step,
                    self.manip.hold_step,
                    self.manip.dataref1,
                    self.manip.tooltip,
                )
            elif self.type == MANIP_NOOP:
                value = (self.manip.dataref1, self.manip.tooltip)
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
                    detent_axis_dataref = next(iter(detent_axis_bone.animations))
                    # A nice little bit of useability for if someone disables autodetect datarefs
                    self.manip.dataref2 = detent_axis_dataref
                else:
                    detent_axis_dataref = self.manip.dataref2

                detent_axis_frames_cleaned = next(
                    iter(detent_axis_bone.animations.values())
                ).getTranslationKeyframeTableNoClamps()
                detent_axis_b = (
                    detent_axis_frames_cleaned[1].location
                    - detent_axis_frames_cleaned[0].location
                )
                detent_axis_xp = xplane_helpers.vec_b_to_x(detent_axis_b)
                self.xplanePrimative.cockpitAttributes.add(
                    XPlaneAttribute(
                        "ATTR_axis_detented",
                        (
                            detent_axis_xp.x,
                            detent_axis_xp.y,
                            detent_axis_xp.z,
                            detent_axis_frames_cleaned[0].value,
                            detent_axis_frames_cleaned[1].value,
                            detent_axis_dataref,
                        ),
                    )
                )

            # 3. All ATTR_axis_detent_range (DRAG_AXIS_DETENT or DRAG_ROTATE)
            if (
                self.type == MANIP_DRAG_AXIS_DETENT
                or self.type == MANIP_DRAG_ROTATE_DETENT
            ) and ver_ge_1100:

                # List[AxisDetentRange] -> bool
                def validate_axis_detent_ranges(
                    axis_detent_ranges, translation_bone, v1_min, v1_max, lift_at_max
                ):
                    """
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
                    """
                    if not len(axis_detent_ranges) > 0:
                        logger.error(
                            "Must {} have axis detent range if manipulator type is {}".format(
                                translation_bone.getBlenderName(),
                                self.manip.get_effective_type_name(),
                            )
                        )
                        return False

                    if not axis_detent_ranges[0].start == v1_min:
                        logger.error(
                            "Axis detent range list for {} must start at Dataref 1's minimum value {}".format(
                                translation_bone.getBlenderName(), v1_min
                            )
                        )
                        return False

                    if not axis_detent_ranges[-1].end == v1_max:
                        logger.error(
                            "Axis detent range list for {} must end at Dataref 1's maximum value {}".format(
                                translation_bone.getBlenderName(), v1_max
                            )
                        )
                        return False

                    if len({range.height for range in axis_detent_ranges}) == 1:
                        logger.warn(
                            "All axis detent ranges for {} have the same height. Check your entered data".format(
                                translation_bone.getBlenderName()
                            )
                        )

                    for i in range(len(axis_detent_ranges)):
                        detent_range = axis_detent_ranges[i]
                        if not detent_range.start <= detent_range.end:
                            logger.error(
                                "The start of axis detent range {} on {} must be less than or equal to its end".format(
                                    detent_range, translation_bone.getBlenderName()
                                )
                            )
                            return False

                        if not 0.0 <= detent_range.height <= lift_at_max:
                            logger.error(
                                "Height in axis detent range {} on {} must be between 0.0 and the maximum lift height ({})".format(
                                    detent_range,
                                    translation_bone.getBlenderName(),
                                    lift_at_max,
                                )
                            )
                            return False

                        # Pit detection portion
                        if (
                            len(axis_detent_ranges) == 1
                            and detent_range.start == detent_range.end
                        ):
                            logger.error(
                                "Axis detent range on {} cannot have stop pit with only one detent".format(
                                    translation_bone.getBlenderName()
                                )
                            )
                            return False

                        AxisDetentStruct = collections.namedtuple(
                            "AxisDetentStruct", ["start", "end", "height"]
                        )
                        try:
                            detent_range_next = axis_detent_ranges[i + 1]
                        except IndexError:
                            detent_range_next = AxisDetentStruct(
                                detent_range.end, v1_max, float("inf")
                            )

                        if not detent_range.end == detent_range_next.start:
                            logger.error(
                                "In {}'s axis detent range list, the start of a detent range must be the end of the previous detent range {},{}".format(
                                    translation_bone.getBlenderName(),
                                    detent_range,
                                    (
                                        detent_range_next.start,
                                        detent_range_next.end,
                                        detent_range.height,
                                    ),
                                )
                            )
                            return False

                        try:
                            detent_range_prev = (
                                axis_detent_ranges[i - 1]
                                if i > 0
                                else AxisDetentStruct(
                                    v1_min, detent_range.start, float("inf")
                                )
                            )
                        except IndexError:
                            detent_range_prev = AxisDetentStruct(
                                v1_min, detent_range.start, float("inf")
                            )

                        if (
                            detent_range.start == detent_range.end
                            and not detent_range_prev.height
                            > detent_range.height
                            < detent_range_next.height
                        ):
                            logger.error(
                                "Stop pit created by {}'s detent range {} must be lower than"
                                " previous {} and next detent ranges {}".format(
                                    translation_bone.getBlenderName(),
                                    (detent_range),
                                    (
                                        detent_range_prev.start,
                                        detent_range_prev.end,
                                        detent_range.height,
                                    ),
                                    (
                                        detent_range_next.start,
                                        detent_range_next.end,
                                        detent_range_next.height,
                                    ),
                                )
                            )
                            return False

                    return True

                if len(self.manip.axis_detent_ranges) > 0:
                    if self.type == MANIP_DRAG_AXIS_DETENT:
                        translation_bone = detent_axis_bone
                    if not validate_axis_detent_ranges(
                        self.manip.axis_detent_ranges,
                        translation_bone,
                        v1_min,
                        v1_max,
                        lift_at_max,
                    ):
                        return

                for axis_detent_range in self.manip.axis_detent_ranges:
                    self.xplanePrimative.cockpitAttributes.add(
                        XPlaneAttribute(
                            "ATTR_axis_detent_range",
                            (
                                axis_detent_range.start,
                                axis_detent_range.end,
                                axis_detent_range.height,
                            ),
                        )
                    )

            # 4. All ATTR_manip_keyframes (DRAG_ROTATE)
            if self.type == MANIP_DRAG_ROTATE or self.type == MANIP_DRAG_ROTATE_DETENT:
                if len(rotation_table) > 2:
                    for rot_keyframe in rotation_table[1:-1]:
                        self.xplanePrimative.cockpitAttributes.add(
                            XPlaneAttribute(
                                "ATTR_manip_keyframe",
                                (rot_keyframe.value, rot_keyframe.degrees),
                            )
                        )
            # add mouse wheel delta
            if (
                self.type in MANIPULATORS_MOUSE_WHEEL
                and bpy.context.scene.xplane.version >= VERSION_1050
                and self.manip.wheel_delta != 0
            ):
                self.xplanePrimative.cockpitAttributes.add(
                    XPlaneAttribute("ATTR_manip_wheel", self.manip.wheel_delta)
                )
