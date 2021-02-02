"""
Statefully builds OBJ commands, including animations and materials.

Takes in OBJ directives and their parameters and outputs at the end Blender datablocks
"""
import collections
import itertools
import math
import pathlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from pprint import pprint
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import bmesh
import bpy
from mathutils import Euler, Vector

from io_xplane2blender.tests import test_creation_helpers
from io_xplane2blender.tests.test_creation_helpers import DatablockInfo, ParentInfo
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


@dataclass
class IntermediateDataref:
    """
    Matches xplane_props.XPlaneDataref.

    Made since dataclasses are more flexible then bpy.types.PropertyGroups.
    """

    anim_type: str = ANIM_TYPE_TRANSFORM
    loop: float = 0.0
    path: str = ""
    show_hide_v1: float = 0
    show_hide_v2: float = 0
    values: List[float] = field(default_factory=list)


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
class IntermediateDatablock:
    datablock_info: DatablockInfo
    # If Datablock is a MESH, these will correspond to (hopefully valid) entries in the idx table and _VT table
    start_idx: Optional[int]
    count: Optional[int]
    animations_to_apply: List[IntermediateAnimation]


@dataclass
class VT:
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


@dataclass
class VTTable:
    vertices: List[VT] = field(default_factory=list)
    idxes: List[int] = field(default_factory=list)


def _build_mesh(
    root_collection: ExportableRoot,
    vertices: List[VT],
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


class ImpCommandBuilder:
    def __init__(self, filepath: Path):
        self.root_collection = test_creation_helpers.create_datablock_collection(
            pathlib.Path(filepath).stem
        )
        self.root_collection.xplane.is_exportable_collection = True
        self.vt_table = VTTable([], [])
        self.blocks: List[IntermediateDatablock] = []

        # --- Animation Builder States ----------------------------------------
        self._last_axis: Optional[Vector] = None
        self._animations = collections.deque()
        # ---------------------------------------------------------------------

    def build_cmd(self, directive: str, *args: List[Union[float, int, str]]):
        """
        Given the directive and it's arguments, correctly handle each case.

        args must be every arg, in order, correctly typed, needed to build the command
        """
        if directive == "VT":
            self.vt_table.vertices.append(VT(*args))
        elif directive == "IDX":
            self.vt_table.idxes.append(args[0])
        elif directive == "IDX10":
            # idx error etc
            self.vt_table.idxes.extend(args)
        elif directive == "TRIS":
            start_idx = args[0]
            count = args[1]
            self.blocks.append(
                IntermediateDatablock(
                    datablock_info=DatablockInfo(
                        datablock_type="MESH",
                        name=self._next_object_name(),
                        parent_info=None,
                        collection=self.root_collection,
                    ),
                    start_idx=start_idx,
                    count=count,
                    animations_to_apply=[self._current_animation],
                )
            )

        elif directive == "ANIM_begin":
            self._current_animation = IntermediateAnimation(
                [], collections.defaultdict(list), []
            )
        elif directive == "ANIM_end":
            del self._current_animation
        elif directive == "ANIM_trans_begin":
            dataref_path = args[0]
            self._current_animation.xp_datarefs.append(
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
            value = args[0]
            location = args[1]
            self._current_animation.locations.append(location)
            self._current_animation.xp_datarefs[-1].values.append(value)
        elif directive == "ANIM_trans_end":
            pass
        elif directive in {"ANIM_hide", "ANIM_show"}:
            self._current_animation.xp_datarefs.append(IntermediateDataref())
            self._current_dataref = self._current_animation.xp_datarefs[-1]

            v1, v2 = args[:2]
            dataref_path = args[2]
            self._current_dataref.anim_type = directive.split("_")[1]
            self._current_dataref.path = dataref_path
            self._current_dataref.show_hide_v1 = v1
            self._current_dataref.show_hide_v2 = v2
        elif directive == "ANIM_rotate_begin":
            axis = args[0]
            dataref_path = args[1]
            self._last_axis = axis
            self._current_animation.xp_datarefs.append(
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
            value = args[0]
            degrees = args[1]
            self._current_animation.rotations[self._last_axis.freeze()].append(degrees)
            self._current_dataref.values.append(value)
        elif directive == "ANIM_rotate_end":
            self._last_axis = None
        elif directive == "ANIM_keyframe_loop":
            loop = args[0]
            self._current_dataref.loop = loop
        else:
            # print("SKIPPING directive", directive)
            pass

    def finalize_intermediate_blocks(self) -> Set[str]:
        """The last step after parsing, converting
        data to intermediate structures, clean up and error checking.

        Returns a set with FINISHED or CANCELLED, matching the returns of bpy
        operators
        """
        for block in self.blocks:
            print("Name", block.datablock_info.name)
            if block.datablock_info.datablock_type == "EMPTY":
                # Create empty
                pass
            elif block.datablock_info.datablock_type == "MESH":
                # Create mesh
                start_idx = block.start_idx
                count = block.count
                mesh_idxes = self.vt_table.idxes[start_idx : start_idx + count]
                ob = _build_mesh(
                    root_collection=self.root_collection,
                    vertices=self.vt_table.vertices[start_idx : start_idx + count],
                    # We reverse the faces to reverse the winding order
                    faces=[
                        list(map(lambda i: i - start_idx, mesh_idxes[i : i + 3][::-1]))
                        for i in range(0, len(mesh_idxes), 3)
                    ],
                )
                if self._current_animation:
                    self._current_animation.set_action(ob)
        return {"FINISHED"}

    @property
    def _current_animation(self) -> Optional[IntermediateAnimation]:
        try:
            return self._animations[-1]
        except IndexError:
            return None

    @_current_animation.setter
    def _current_animation(self, value: IntermediateAnimation):
        self._animations.append(value)

    @_current_animation.deleter
    def _current_animation(self):
        self._animations.pop()

    @property
    def _current_dataref(self) -> Optional[IntermediateDataref]:
        """The currenet dataref of the current animation"""
        try:
            return self._current_animation.xp_datarefs[-1]
        except (
            AttributeError,
            IndexError,
        ):  # _current_animation is None or xp_datarefs is empty
            return None

    @_current_dataref.setter
    def _current_dataref(self, value: IntermediateDataref):
        """TODO: This isn't really the API we want..."""
        self._current_animation.xp_datarefs.append(value)

    def _next_object_name(self) -> str:
        return f"Mesh.{sum(1 for block in self.blocks if block.datablock_info.datablock_type == 'MESH'):03}"

    def _next_empty_name(self) -> str:
        return f"Mesh.{sum(1 for block in self.blocks if block.datablock_info.datablock_type == 'EMPTY'):03}"
