"""The starting point for the export process, the start of the addon"""
import collections
import itertools
import math
import pathlib
import re
from dataclasses import dataclass, field
from pprint import pprint
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import bmesh
import bpy
from mathutils import Euler, Vector

from io_xplane2blender.tests import test_creation_helpers
from io_xplane2blender.xplane_constants import (
    ANIM_TYPE_HIDE,
    ANIM_TYPE_SHOW,
    ANIM_TYPE_TRANSFORM,
)
from io_xplane2blender.xplane_helpers import (
    ExportableRoot,
    floatToStr,
    logger,
    vec_b_to_x,
    vec_x_to_b,
)


class UnrecoverableParserError(Exception):
    pass


# TODO: These names are terrible!
# They should be related to transitions or something
@dataclass
class IntermediateDataref:
    """
    Matches xplane_props.XPlaneDataref.

    Made since dataclasses are more flexible then bpy.types.PropertyGroups.
    """

    anim_type: str  # Of ANIM_TYPE_*
    loop: float
    path: str
    show_hide_v1: float
    show_hide_v2: float
    values: List[float]


@dataclass
class IntermediateAnimation:
    """
    All things that define the contents of an ANIM_began_* OBJ block
    """

    locations: List[Vector]
    rotations: Dict[Vector, List[float]]
    xp_datarefs: List[IntermediateDataref]

    def set_action(self, bl_object: bpy.types.Object):
        def recompose_rotation(i) -> Vector:
            """Recomposes the OBJ's split form into one Vector"""

            tot_rot = Vector()
            # print("Pre-combine rotations")
            # pprint(self.rotations)
            for axis, degrees in [
                (axis, degrees_list[i]) for axis, degrees_list in self.rotations.items()
            ]:
                if axis == Vector((1, 0, 0)):
                    tot_rot.x = degrees
                elif axis == Vector((0, 1, 0)):
                    tot_rot.y = degrees
                elif axis == Vector((0, 0, 1)):
                    tot_rot.z = degrees
                else:
                    assert False, f"problem axis: {axis}"
            # print("Recombined Rotation", tot_rot)
            return tot_rot

        current_frame = 1
        for xplane_dataref in self.xp_datarefs:
            if xplane_dataref.anim_type == ANIM_TYPE_TRANSFORM:
                keyframe_infos = []
                for i, value in enumerate(xplane_dataref.values):
                    keyframe_infos.append(
                        test_creation_helpers.KeyframeInfo(
                            idx=current_frame,
                            dataref_path=xplane_dataref.path,
                            dataref_value=value,
                            dataref_anim_type=xplane_dataref.anim_type,
                            location=self.locations[i] if self.locations else None,
                            rotation=recompose_rotation(i) if self.rotations else None,
                        )
                    )
                    current_frame += 1
            else:
                keyframe_infos = [
                    test_creation_helpers.KeyframeInfo(
                        idx=1,
                        dataref_path=xplane_dataref.path,
                        dataref_show_hide_v1=xplane_dataref.show_hide_v1,
                        dataref_show_hide_v2=xplane_dataref.show_hide_v2,
                        dataref_anim_type=xplane_dataref.anim_type,
                    )
                ]

            test_creation_helpers.set_animation_data(bl_object, keyframe_infos)
            current_frame = 1


@dataclass
class _VT:
    """Where xyz, nxyz are in Blender coords"""

    x: float
    y: float
    z: float
    nx: float
    ny: float
    nz: float
    s: float
    t: float

    def __post_init__(self):
        for attr, factory in type(self).__annotations__.items():
            try:
                setattr(self, attr, factory(getattr(self, attr)))
            except ValueError:
                print(
                    f"Couldn't convert '{attr}''s value ({getattr(self, attr)}) with {factory}"
                )

    def __str__(self) -> str:
        def fmt(s):
            try:
                return floatToStr(float(s))
            except (TypeError, ValueError):
                return s

        return "\t".join(
            fmt(value)
            for attr, value in vars(self).items()
            if not attr.startswith("__")
        )


def _build_mesh(
    root_collection: ExportableRoot,
    vertices: List[_VT],
    faces: List[Tuple[int, int, int]],
) -> bpy.types.Mesh:
    me = bpy.data.meshes.new(f"Mesh.{len(bpy.data.meshes):03}")
    ob = bpy.data.objects.new(me.name, me)
    ob.location = [0, 0, 0]
    root_collection.objects.link(ob)
    me.from_pydata([(v.x, v.y, v.z) for v in vertices], [], faces)
    me.update(calc_edges=True)
    uv_layer = me.uv_layers.new()

    if not me.validate(verbose=True):
        for idx in set(itertools.chain.from_iterable(faces)):
            me.vertices[idx].normal = (
                vertices[idx].nx,
                vertices[idx].ny,
                vertices[idx].nz,
            )
            uv_layer.data[idx].uv = vertices[idx].s, vertices[idx].t
    else:
        logger.error("Mesh was not valid, check stdout for more")

    test_creation_helpers.set_material(ob, "Material")
    return ob


def import_obj(filepath: Union[pathlib.Path, str]) -> str:
    """
    Attempts to import an OBJ, mutating the blender data of the current scene.
    The importer may
    - finish the whole import, returning "FINISHED"
    - stop early with partial results, returning "CANCELLED".
    - Raise an UnrecoverableParserError showing no results can be trusted
    """
    filepath = pathlib.Path(filepath)
    try:
        lines = pathlib.Path(filepath).read_text().splitlines()
    except OSError:
        raise OSError
    else:
        # pprint(lines)
        pass

    if lines[0:3] != ["I", "800", "OBJ"]:
        logger.error(
            ".obj file must start with exactly the OBJ header. Check filetype and content"
        )
        raise UnrecoverableParserError

    directives_white = {
        "VT",
        "IDX",
        "IDX10",
        "TRIS",
        "ANIM_begin",
        "ANIM_end",
        "ANIM_trans_begin",
        "ANIM_trans_key",
        "ANIM_trans_end",
        "ANIM_rotate_begin",
        "ANIM_rotate_key",
        "ANIM_rotate_end",
        "ANIM_keyframe_loop",
    }
    vt_table = []
    idxs = []

    # TODO: This should be made later. We should start with our tree of intermediate structures then eventually make that into bpy structs when we know what is valid.
    # Otherwise, consider this a hack
    root_col = test_creation_helpers.create_datablock_collection(
        pathlib.Path(filepath).stem
    )
    root_col.xplane.is_exportable_collection = True
    pattern = re.compile("([^#]*)(#.*)?")

    current_animation: Optional[IntermediateAnimation] = None
    # Cases:
    #   Empty after ANIM_end
    #   ANIM_trans/rot_end, ANIM_trans/rot_key after ANIM_trans/rotate key or being
    # TODO: Need FSM for what ANIM type we're expecting next
    current_expected_animation = {""}
    last_axis = None
    for lineno, line in enumerate(map(str.strip, lines[3:]), start=1):
        to_parse, comment = re.match(pattern, line).groups()[0:2]
        if not to_parse:
            continue
        else:
            directive, *components = to_parse.split()
            # print(lineno, directive, components)

        # TODO: Rewrite using giant switch-ish table and functions so it is more neat
        # Need scanf solution
        # scan_int, scan_float, scan_vec2, scan_vec3tobl, scan_str, scan_enum (where it scans a limited number of choices and has a mapping of strings for it)
        # if fails we can fallback to default value and print warning or just print a logger warning that it is skipping
        # itr = enumerate()
        # def scan_(last=False, msg_missing=f"Could not convert parameter {lineno} _true, default=None)->value:
        # Throws parser error if needed
        # def _try to swallow all exceptions if the only thing that should happen is the line getting ignored on bad data. Otherwise we can go into more crazy exception hanlding cases
        if directive == "VT":
            components[:3] = vec_x_to_b(list(map(float, components[:3])))
            components[3:6] = vec_x_to_b(list(map(float, components[3:6])))
            components[6:8] = list(map(float, components[6:8]))
            vt_table.append(_VT(*components[:8]))
        elif directive == "IDX":
            try:
                idx = int(*components[:1])
                if idx < -1:
                    raise ValueError(
                        f"IDX on line {lineno}'s is less than 0"
                    )  # Also, must be less than POINT_COUNTS reports?  # TODO yes?
            except ValueError:
                logger.warn(f"IDX table messed up, {idx} is not an int")
                print("what")
            except IndexError:
                # should have been at least 1
                print("index error")
                pass
            else:
                idxs.append(idx)
        elif directive == "IDX10":
            # idx error etc
            idxs.extend(map(int, components[:11]))
        elif directive == "TRIS":
            # TODO: idx error, can't convert error, idx doesn't have that many error, wrong index error
            start_idx = int(components[0])
            count = int(components[1])
            mesh_idxs = idxs[start_idx : start_idx + count]
            ob = _build_mesh(
                root_collection=root_col,
                vertices=vt_table[start_idx : start_idx + count],
                # We reverse the faces to reverse the winding order
                faces=[
                    [*map(lambda i: i - start_idx, mesh_idxs[i : i + 3][::-1])]
                    for i in range(0, len(mesh_idxs), 3)
                ],
            )
            if current_animation:
                current_animation.set_action(ob)
        elif directive == "ANIM_begin":
            current_animation = IntermediateAnimation(
                [], collections.defaultdict(list), []
            )
        elif directive == "ANIM_end":
            current_animation = None
        elif directive == "ANIM_trans_begin":
            dataref_path = components[0]
            current_animation.xp_datarefs.append(
                IntermediateDataref(
                    anim_type=ANIM_TYPE_TRANSFORM,
                    loop=0,
                    path=dataref_path,
                    show_hide_v1=0,
                    show_hide_v2=0,
                    values=[],
                )
            )
        elif directive == "ANIM_trans_key":
            value = float(components[0])
            location = vec_x_to_b(list(map(float, components[1:4])))
            current_animation.locations.append(location)
            current_animation.xp_datarefs[-1].values.append(value)
        elif directive == "ANIM_trans_end":
            pass
        elif directive == "ANIM_rotate_begin":
            axis = vec_x_to_b(list(map(float, components[0:3])))
            last_axis = axis
            dataref_path = components[3]
            current_animation.xp_datarefs.append(
                IntermediateDataref(
                    anim_type=ANIM_TYPE_TRANSFORM,
                    loop=0,
                    path=dataref_path,
                    show_hide_v1=0,
                    show_hide_v2=0,
                    values=[],
                )
            )
        elif directive == "ANIM_rotate_key":
            value = float(components[0])
            degrees = float(components[1])
            current_animation.rotations[last_axis.freeze()].append(degrees)
            current_animation.xp_datarefs[-1].values.append(value)
        elif directive == "ANIM_rotate_end":
            last_axis = None
        elif directive == "ANIM_keyframe_loop":
            loop = float(components[0])
            current_animation.xp_datarefs[-1].loop = loop
        else:
            # print("SKIPPING directive", directive)
            pass

    return "FINISHED"
