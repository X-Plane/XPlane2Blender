"""
Utilities for generating scene reports as CSV data.

Collects animation datarefs and manipulator/command information from all
objects and bones in a Blender scene and serializes them to CSV strings.
"""

import csv
import io
from typing import Dict, List, Optional, Tuple

import bpy
from io_xplane2blender.xplane_constants import (
    MANIP_DELTA,
    MANIP_DRAG_AXIS,
    MANIP_DRAG_AXIS_DETENT,
    MANIP_DRAG_AXIS_PIX,
    MANIP_DRAG_ROTATE,
    MANIP_DRAG_ROTATE_DETENT,
    MANIP_DRAG_XY,
    MANIP_PUSH,
    MANIP_RADIO,
    MANIP_TOGGLE,
    MANIP_WRAP,
)
from io_xplane2blender.xplane_helpers import get_action_fcurves

# --- Field name constants ---

DATAREF_FIELDS = [
    "Object Name",
    "Object Type",
    "Dataref Path",
    "Animation Type",
    "Value 1",
    "Value 2",
    "Loop",
]

MANIPULATOR_FIELDS = [
    "Object Name",
    "Manipulator Type",
    "Tooltip",
    "Cursor",
    "Dataref 1",
    "Dataref 1 Min",
    "Dataref 1 Max",
    "Dataref 2",
    "Dataref 2 Min",
    "Dataref 2 Max",
    "Value On",
    "Value Off",
    "Value Down",
    "Value Up",
    "Value Hold",
    "Command",
    "Positive Command",
    "Negative Command",
]


def collect_datarefs(
    scene: bpy.types.Scene, view_layer: bpy.types.ViewLayer
) -> List[Dict]:
    """
    Walk all visible objects and bones in the scene, returning one dict per
    animation dataref. Transform datarefs report their keyframe value range;
    show/hide datarefs report their threshold values.
    """
    rows = []

    for obj in scene.objects:
        if not obj.visible_get(view_layer=view_layer):
            continue
        # Datarefs on the object itself
        for i, dr in enumerate(obj.xplane.datarefs):
            if not dr.path:
                continue
            v1, v2 = _get_transform_range(obj.animation_data, i, dr)
            rows.append({
                "Object Name": obj.name,
                "Object Type": "OBJECT",
                "Dataref Path": dr.path,
                "Animation Type": dr.anim_type,
                "Value 1": v1,
                "Value 2": v2,
                "Loop": dr.loop if dr.loop != 0.0 else "",
            })

        # Datarefs on bones inside armature objects
        if obj.type == "ARMATURE" and obj.data:
            for bone in obj.data.bones:
                for i, dr in enumerate(bone.xplane.datarefs):
                    if not dr.path:
                        continue
                    # Bone keyframes live on the armature's animation_data,
                    # with a data path that includes the bone name.
                    v1, v2 = _get_transform_range(
                        obj.data.animation_data, i, dr, bone_name=bone.name
                    )
                    rows.append({
                        "Object Name": f"{obj.name} / {bone.name}",
                        "Object Type": "BONE",
                        "Dataref Path": dr.path,
                        "Animation Type": dr.anim_type,
                        "Value 1": v1,
                        "Value 2": v2,
                        "Loop": dr.loop if dr.loop != 0.0 else "",
                    })

    return rows


def _get_transform_range(
    anim_data: Optional[bpy.types.AnimData],
    index: int,
    dr,
    bone_name: Optional[str] = None,
) -> Tuple:
    """
    Return (value_1, value_2) for a dataref.

    For show/hide types these are the stored threshold values.
    For transform types these are the min/max keyframe values on the
    dataref's value FCurve, or empty strings if no keyframes exist.
    """
    if dr.anim_type in ("show", "hide"):
        return dr.show_hide_v1, dr.show_hide_v2

    # Build the FCurve data path used when keyframing this dataref's value
    if bone_name:
        data_path = f'bones["{bone_name}"].xplane.datarefs[{index}].value'
    else:
        data_path = f"xplane.datarefs[{index}].value"

    if anim_data and anim_data.action:
        for fcurve in get_action_fcurves(anim_data):
            if fcurve.data_path == data_path:
                values = [kp.co[1] for kp in fcurve.keyframe_points]
                if values:
                    return min(values), max(values)

    return "", ""


def collect_manipulators(
    scene: bpy.types.Scene, view_layer: bpy.types.ViewLayer
) -> List[Dict]:
    """
    Walk all visible objects in the scene, returning one dict per enabled
    manipulator. Each row includes whatever datarefs or commands the
    manipulator references.
    """
    rows = []

    for obj in scene.objects:
        if not obj.visible_get(view_layer=view_layer):
            continue
        manip = obj.xplane.manip
        if not manip.enabled:
            continue

        t = manip.type
        row = {
            "Object Name": obj.name,
            "Manipulator Type": t,
            "Tooltip": manip.tooltip,
            "Cursor": manip.cursor,
            "Dataref 1": "",
            "Dataref 1 Min": "",
            "Dataref 1 Max": "",
            "Dataref 2": "",
            "Dataref 2 Min": "",
            "Dataref 2 Max": "",
            "Value On": "",
            "Value Off": "",
            "Value Down": "",
            "Value Up": "",
            "Value Hold": "",
            "Command": "",
            "Positive Command": "",
            "Negative Command": "",
        }

        if t in (
            MANIP_DRAG_XY,
            MANIP_DRAG_AXIS,
            MANIP_DRAG_AXIS_PIX,
            MANIP_DRAG_AXIS_DETENT,
            MANIP_DRAG_ROTATE,
            MANIP_DRAG_ROTATE_DETENT,
        ):
            row["Dataref 1"] = manip.dataref1
            row["Dataref 1 Min"] = manip.v1_min
            row["Dataref 1 Max"] = manip.v1_max
            if t == MANIP_DRAG_XY:
                row["Dataref 2"] = manip.dataref2
                row["Dataref 2 Min"] = manip.v2_min
                row["Dataref 2 Max"] = manip.v2_max
        elif t == MANIP_TOGGLE:
            row["Dataref 1"] = manip.dataref1
            row["Value On"] = manip.v_on
            row["Value Off"] = manip.v_off
        elif t == MANIP_PUSH:
            row["Dataref 1"] = manip.dataref1
            row["Value Down"] = manip.v_down
            row["Value Up"] = manip.v_up
        elif t == MANIP_RADIO:
            row["Dataref 1"] = manip.dataref1
            row["Value Down"] = manip.v_down
        elif t in (MANIP_DELTA, MANIP_WRAP):
            row["Dataref 1"] = manip.dataref1
            row["Value Down"] = manip.v_down
            row["Value Hold"] = manip.v_hold
            row["Dataref 1 Min"] = manip.v1_min
            row["Dataref 1 Max"] = manip.v1_max
        else:
            # Command-based types
            row["Command"] = manip.command
            row["Positive Command"] = manip.positive_command
            row["Negative Command"] = manip.negative_command

        rows.append(row)

    return rows


def write_csv(rows: List[Dict], fieldnames: List[str]) -> str:
    """Serialize a list of row dicts to a CSV string."""
    output = io.StringIO()
    writer = csv.DictWriter(
        output, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def write_combined_report(dr_rows: List[Dict], manip_rows: List[Dict]) -> str:
    """
    Serialize datarefs and manipulators into a single CSV string.

    Each non-empty section gets its own header row. Sections are separated by
    a blank line. Sections with no rows are omitted entirely.
    """
    sections = []
    if dr_rows:
        sections.append(write_csv(dr_rows, DATAREF_FIELDS))
    if manip_rows:
        sections.append(write_csv(manip_rows, MANIPULATOR_FIELDS))
    return "\n".join(sections)
