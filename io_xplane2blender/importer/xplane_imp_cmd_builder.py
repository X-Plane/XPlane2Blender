"""
Statefully builds OBJ commands, including animations and materials.

Takes in OBJ directives and their parameters and outputs at the end Blender datablocks
"""
import collections
import copy
import itertools
import math
import pathlib
import random
import re
from dataclasses import dataclass, field
from itertools import islice, tee
from pathlib import Path
from pprint import pprint
from typing import (
    Any,
    Callable,
    Deque,
    Dict,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
)

import bmesh
import bpy
from mathutils import Euler, Matrix, Quaternion, Vector

from io_xplane2blender.tests import test_creation_helpers
from io_xplane2blender.tests.test_creation_helpers import DatablockInfo, ParentInfo
from io_xplane2blender.xplane_constants import (
    ANIM_TYPE_HIDE,
    ANIM_TYPE_SHOW,
    ANIM_TYPE_TRANSFORM,
    PRECISION_KEYFRAME,
)
from io_xplane2blender.xplane_helpers import (
    ExportableRoot,
    floatToStr,
    logger,
    round_vec,
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

    def __hash__(self):
        return hash(
            (
                self.anim_type,
                self.loop,
                self.path,
                self.show_hide_v1,
                self.show_hide_v2,
                tuple(self.values),
            )
        )


@dataclass
class IntermediateAnimation:
    """
    An animation is everything generated by one pair of ANIM_trans/rotate pair (or
    the static version). An IntermediateDatablock may have 0 or more of these.
    """

    # Always
    # - You will have one of (type == "TRANSFORM" and (locations xor rotations) or (type == "SHOW"/"HIDE")
    # - locations cannot be "merged" for the same set of values, they are replaced instead
    # - rotations axis will be unit length Vector of the co-ordinate axis
    # TODO: Support AxisAngle representation, must have test_Creation_helper use AxisAngle since we kind of already have AxisAngle?......
    # Prior to any optimization
    # - rotations will have a length of 0 or 1
    # After optimization
    # - rotations dict may have 0-3 entries

    # Locations and rotations will have only one entry unless
    # they are being gathered together as part of the minimization process
    # locations and each axis's degrees list must equal the dataref's values list
    locations: List[Vector] = field(default_factory=list)
    # A dictionary of rotations along an axis (usually X, Y, Z), and their degrees
    rotations: Dict[Vector, List[float]] = field(
        default_factory=lambda: collections.defaultdict(list)
    )
    xp_dataref: IntermediateDataref = field(
        default_factory=lambda: IntermediateDataref()
    )

    def apply_animation(self, bl_object: bpy.types.Object):
        def recompose_rotation(value_idx: int):
            tot_rot = Vector((0, 0, 0))
            for axis, degrees in self.rotations.items():
                tot_rot += axis * math.radians(degrees[value_idx])
            return tot_rot

        current_frame = 1
        if self.xp_dataref.anim_type == ANIM_TYPE_TRANSFORM:
            keyframe_infos = []
            for value_idx, value in enumerate(self.xp_dataref.values):
                keyframe_infos.append(
                    test_creation_helpers.KeyframeInfo(
                        idx=current_frame,
                        dataref_path=self.xp_dataref.path,
                        dataref_value=value,
                        dataref_anim_type=self.xp_dataref.anim_type,
                        location=self.locations[value_idx] + bl_object.location
                        if self.locations
                        else None,
                        rotation=recompose_rotation(value_idx)
                        if self.rotations
                        else None,
                    )
                )
                current_frame += 1
        else:
            keyframe_infos = [
                test_creation_helpers.KeyframeInfo(
                    idx=1,
                    dataref_path=self.xp_dataref.path,
                    dataref_show_hide_v1=self.xp_dataref.show_hide_v1,
                    dataref_show_hide_v2=self.xp_dataref.show_hide_v2,
                    dataref_anim_type=self.xp_dataref.anim_type,
                )
            ]

        test_creation_helpers.set_animation_data(bl_object, keyframe_infos)
        current_frame = 1

    def is_valid(self) -> bool:
        if self.xp_dataref.anim_type == ANIM_TYPE_TRANSFORM:
            exclusive_use = (self.locations and not self.rotations) or (
                not self.locations and self.rotations
            )
            # TODO: Support AngleAxis
            axis_orthogonal = next(self.rotations.keys()).freeze() in {
                Vector((1, 0, 0)).freeze(),
                Vector((0, 1, 0)).freeze(),
                Vector((0, 0, 1)).freeze(),
            }
            return exclusive_use and axis_orthogonal
        else:
            return not self.locations and not self.rotations


@dataclass
class IntermediateDatablock:
    datablock_info: DatablockInfo
    # If Datablock is a MESH, these will correspond to (hopefully valid) entries in the idx table and _VT table
    start_idx: Optional[int]
    count: Optional[int]
    # In general, 1st animation represents locations or rotations, Empty if not animated, the 1st animation will
    # represent locations or rotations, 2nd and on are SHOW/HIDEs
    # During finalization as much of these are combined
    animations_to_apply: List[IntermediateAnimation]
    bake_matrix: Matrix

    # Why here? DatablockInfos are meant to be isolated structs as much as possible
    # and we're interested in the relationship between IntermediateDatablocks
    # and their animations which isn't data a DatablockInfo has
    children: List["IntermediateDatablock"] = field(default_factory=list)

    def build_mesh(self, vt_table: "VTTable") -> bpy.types.Mesh:
        mesh_idxes = vt_table.idxes[self.start_idx : self.start_idx + self.count]
        idx_mapping: Dict[int, int] = {}
        vertices: List[VT] = []

        for mesh_idx in mesh_idxes:
            if mesh_idx not in idx_mapping:
                idx_mapping[mesh_idx] = len(idx_mapping)
                vertices.append(vt_table.vertices[mesh_idx])

        # Thanks senderle, https://stackoverflow.com/a/22045226
        def chunk(it, size):
            it = iter(it)
            return iter(lambda: tuple(itertools.islice(it, size)), ())

        py_vertices = [(v.x, v.y, v.z) for v in vertices]
        py_faces: List[Tuple[int, int, int]] = [
            # We reverse the winding order to reverse the faces
            [idx_mapping[idx] for idx in face][::-1]
            for i, face in enumerate(chunk(mesh_idxes, 3))
        ]

        ob = test_creation_helpers.create_datablock_mesh(
            self.datablock_info,
            mesh_src=test_creation_helpers.From_PyData(
                py_vertices,
                [],
                py_faces,
            ),
        )
        me = ob.data
        me.update(calc_edges=True)
        uv_layer = me.uv_layers[0]  # .new()

        i = 0
        if not me.validate(verbose=True):
            for face in py_faces:
                for idx in face:
                    me.vertices[idx].normal = (
                        vertices[idx].nx,
                        vertices[idx].ny,
                        vertices[idx].nz,
                    )
                    uv_layer.data[idx].uv = vertices[idx].s, vertices[idx].t
                    if "body" in ob.name:
                        # print(i, "uv", uv_layer.data[idx].uv)
                        pass
                    i += 1
        else:
            logger.error("Mesh was not valid, check console for more")

        test_creation_helpers.set_material(ob, "Material")
        return ob

    @property
    def name(self) -> str:
        return self.datablock_info.name

    @property
    def parent(self) -> Optional[str]:
        try:
            return self.datablock_info.parent_info.parent
        except AttributeError:
            return None

    @parent.setter
    def parent(self, value: str) -> None:
        self.datablock_info.parent_info.parent = value


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


@dataclass
class _AnimIntermediateStackEntry:
    animation: IntermediateAnimation
    intermediate_datablock: Optional[IntermediateDatablock]


class ImpCommandBuilder:
    def __init__(self, filepath: Path):
        self.root_collection = test_creation_helpers.create_datablock_collection(
            pathlib.Path(filepath).stem
        )

        self.root_collection.xplane.is_exportable_collection = True
        self.vt_table = VTTable([], [])

        # Although we don't end up making this, it is useful for tree problems
        self.root_intermediate_datablock = IntermediateDatablock(
            datablock_info=DatablockInfo(
                datablock_type="EMPTY",
                name="INTER_ROOT",
                collection=self.root_collection,
            ),
            start_idx=None,
            count=None,
            animations_to_apply=[],
            bake_matrix=Matrix.Identity(4),
        )

        # --- Animation Builder States ----------------------------------------
        # Instead of build at seperate parent/child relationship in Datablock info, we just save everything we make here
        self._blocks: List[IntermediateDatablock] = [self.root_intermediate_datablock]
        self._last_axis: Optional[Vector] = None
        self._anim_intermediate_stack: Deque[
            _AnimIntermediateStackEntry
        ] = collections.deque()
        self._anim_count: Sequence[int] = collections.deque()
        self._bake_matrix_stack: Deque[Matrix] = collections.deque((Matrix(),))
        # ---------------------------------------------------------------------

    def build_cmd(
        self, directive: str, *args: List[Union[float, int, str]], name_hint: str = ""
    ):
        """
        Given the directive and it's arguments, correctly handle each case.

        args must be every arg, in order, correctly typed, needed to build the command
        """

        def begin_new_frame() -> None:
            if not self._top_intermediate_datablock:
                parent = self.root_intermediate_datablock
            else:
                parent = self._top_intermediate_datablock

            empty = IntermediateDatablock(
                datablock_info=DatablockInfo(
                    "EMPTY",
                    name=self._next_empty_name(),
                    parent_info=ParentInfo(parent.datablock_info.name),
                    collection=self.root_collection,
                ),
                start_idx=None,
                count=None,
                animations_to_apply=[],
                bake_matrix=self._bake_matrix_stack[-1].copy(),
            )
            self._blocks.append(empty)
            parent.children.append(empty)

            self._anim_intermediate_stack.append(
                _AnimIntermediateStackEntry(IntermediateAnimation(), empty)
            )
            self._anim_count[-1] += 1
            empty.animations_to_apply.append(self._top_animation)
            self._bake_matrix_stack[-1].identity()

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
            if not self._anim_intermediate_stack:
                parent: IntermediateDatablock = self.root_intermediate_datablock
            else:
                parent: IntermediateDatablock = self._anim_intermediate_stack[
                    -1
                ].intermediate_datablock

            intermediate_datablock = IntermediateDatablock(
                datablock_info=DatablockInfo(
                    datablock_type="MESH",
                    name=name_hint or self._next_object_name(),
                    # How do we keep track of this
                    parent_info=ParentInfo(parent.datablock_info.name),
                    collection=self.root_collection,
                ),
                start_idx=start_idx,
                count=count,
                animations_to_apply=[],
                bake_matrix=self._bake_matrix_stack[-1].copy(),
            )
            self._blocks.append(intermediate_datablock)
            parent.children.append(intermediate_datablock)

        elif directive == "ANIM_begin":
            self._anim_count.append(0)
            self._bake_matrix_stack.append(self._bake_matrix_stack[-1].copy())
        elif directive == "ANIM_end":
            for i in range(self._anim_count.pop()):
                self._anim_intermediate_stack.pop()
            self._bake_matrix_stack.pop()
        elif directive == "ANIM_trans_begin":
            dataref_path = args[0]

            begin_new_frame()
            self._top_animation.xp_dataref = IntermediateDataref(
                anim_type=ANIM_TYPE_TRANSFORM,
                loop=0,
                path=dataref_path,
                show_hide_v1=0,
                show_hide_v2=0,
                values=[],
            )
        elif directive == "ANIM_trans_key":
            value = args[0]
            location = args[1]
            self._top_animation.locations.append(location)
            self._top_dataref.values.append(value)
        elif directive == "ANIM_trans_end":
            # TODO: With a normal implementation, we'd be baking locations as we go and clearing to identity here
            # but with out implementation it happens at ANIM_*_begin, and the adjustment happens way later
            pass
        elif directive in {"ANIM_show", "ANIM_hide"}:
            v1, v2 = args[:2]
            dataref_path = args[2]
            begin_new_frame()
            self._top_dataref.anim_type = directive.replace("ANIM_", "")
            self._top_dataref.path = dataref_path
            self._top_dataref.show_hide_v1 = v1
            self._top_dataref.show_hide_v2 = v2
        elif directive == "ANIM_rotate_begin":
            axis = args[0]
            dataref_path = args[1]
            self._last_axis = Vector(map(abs, axis))
            begin_new_frame()
            self._top_animation.xp_dataref = IntermediateDataref(
                anim_type=ANIM_TYPE_TRANSFORM,
                loop=0,
                path=dataref_path,
                show_hide_v1=0,
                show_hide_v2=0,
                values=[],
            )
        elif directive == "ANIM_rotate_key":
            value = args[0]
            degrees = args[1]
            self._top_animation.rotations[self._last_axis.freeze()].append(degrees)
            self._top_dataref.values.append(value)
        elif directive == "ANIM_rotate_end":
            self._last_axis = None
        elif directive == "ANIM_keyframe_loop":
            loop = args[0]
            self._top_dataref.loop = loop
        elif directive == "ANIM_trans":
            xyz1, xyz2 = args[0:2]
            v1, v2 = args[2:4]
            path = args[4]
            r_xyz1, r_xyz2 = (
                round_vec(xyz, PRECISION_KEYFRAME) for xyz in [xyz1, xyz2]
            )
            r_v1, r_v2 = (round(v, PRECISION_KEYFRAME) for v in [v1, v2])

            def add_as_dynamic():
                begin_new_frame()
                self._top_animation.locations.append(xyz1)
                self._top_animation.locations.append(xyz2)
                self._top_dataref.values.extend((v1, v2))
                self._top_dataref.path = path

            if r_xyz1 == r_xyz2 and r_v1 == r_v2:
                print("trans, case A - static")
                self._bake_matrix_stack[-1] = self._bake_matrix_stack[
                    -1
                ] @ Matrix.Translation(xyz1)
            elif r_xyz1 == r_xyz2 and r_v1 != r_v2:
                print("trans, case B - as dynamic")
                add_as_dynamic()
            elif r_xyz1 != r_xyz2 and r_v1 == r_v2:
                print("trans, case C - as odd dynamic")
                add_as_dynamic()
                # TODO: make warning
                line = "bleh"
                logger.warn(
                    f"ANIM_trans"
                    f"    {c for c in xyz1}"
                    f"    {c for c in xyz2}"
                    f"    {v1} {v2} {path}`"
                    f"on line {line} has different locations but the same dataref values - it is malformed."
                    f"Fix {self._anim_intermediate_stack[-1].intermediate_datablock}"
                )
            elif r_xyz1 != r_xyz2 and r_v1 != r_v2:
                print("trans, case D - dynamic")
                add_as_dynamic()

        elif directive == "ANIM_rotate":
            dxyz = args[0]
            r1, r2 = args[1:3]
            v1, v2 = args[3:5]
            path = args[5]

            r_r1, r_r2 = (round(r, PRECISION_KEYFRAME) for r in [r1, r2])
            r_v1, r_v2 = (round(v, PRECISION_KEYFRAME) for v in [v1, v2])

            def add_as_dynamic():
                begin_new_frame()
                self._top_animation.rotations[dxyz.freeze()].append(r1)
                self._top_animation.rotations[dxyz.freeze()].append(r2)
                self._top_dataref.values.extend((v1, v2))
                self._top_dataref.path = path

            if r_r1 == r_r2 and r_v1 == r_v2:
                print("rot case A")
                self._bake_matrix_stack[-1] = (
                    self._bake_matrix_stack[-1]
                    @ Quaternion(dxyz, math.radians(r1)).to_matrix().to_4x4()
                )
                print(
                    "to euler in ANIM_rotate",
                    [math.degrees(c) for c in self._bake_matrix_stack[-1].to_euler()],
                )
            elif r_r1 == r_r2 and r_v1 != r_v2:
                print("rot case B")
                add_as_dynamic()
            elif r_r1 != r_r2 and r_v1 == r_v2:
                print("rot case C")
                add_as_dynamic()
                # TODO: make warning
                line = "bleh"
                logger.warn(
                    f"ANIM_rotate"
                    f"    {Vector(c for c in dxyz)}"
                    f"    {r1} {r2}"
                    f"    {v1} {v2}"
                    f"    {path}"
                    f"\nnon line {line} has different rotation but the same dataref values - it is malformed."
                    f"Fix {self._anim_intermediate_stack[-1].intermediate_datablock}"
                )
            elif r_r1 != r_r2 and r_v1 != r_v2:
                print("rot case D")
                add_as_dynamic()
        else:
            assert False, f"{directive} is not supported yet"

    def finalize_intermediate_blocks(self) -> Set[str]:
        """The last step after parsing, converting
        data to intermediate structures, clean up and error checking.

        Returns a set with FINISHED or CANCELLED, matching the returns of bpy
        operators
        """

        def reparent_children_to_new_block(
            current_parent_block: IntermediateDatablock,
            new_parent_block: IntermediateDatablock,
        ):
            for child in current_parent_block.children:
                print(
                    f"{child.datablock_info.name}'s Parent before: {child.datablock_info.parent_info.parent}"
                )
                child.datablock_info.parent_info.parent = (
                    new_parent_block.datablock_info.name
                )
                print(
                    f"{child.datablock_info.name}'s Parent after: {child.datablock_info.parent_info.parent}"
                )
            current_parent_block.children.clear()

        # Since we're using root collections mode, our INTER_ROOT empty datablock isn't made
        # and we pretend its a collection.
        blocks_rem_itr = islice(self._blocks, 1, len(self._blocks))
        while True:
            try:
                intermediate_block = next(blocks_rem_itr)
            except StopIteration:
                break
            else:
                intermediate_name = intermediate_block.datablock_info.name
                intermediate_block_type = (
                    intermediate_block.datablock_info.datablock_type
                )
                intermediate_parent = intermediate_block.parent
                if intermediate_block.parent == "INTER_ROOT":
                    intermediate_block.datablock_info.parent_info = None
                intermediate_parent_info = intermediate_block.datablock_info.parent_info

            print(
                f"Deciding {intermediate_block.name}" f", parent {intermediate_parent}"
            )

            if intermediate_block_type == "EMPTY":
                # Remember, we only make empties to store animations so no try needed here
                intermediate_animation = intermediate_block.animations_to_apply[0]
                intermediate_dataref = intermediate_animation.xp_dataref
                intermediate_path = intermediate_dataref.path
                is_interm_loc_anim = bool(intermediate_animation.locations)
                is_interm_rot_anim = bool(intermediate_animation.rotations)

                def optimize_empty_chain(
                    in_block: IntermediateDatablock,
                    searching_itr: Iterator[IntermediateDatablock],
                ) -> Tuple[IntermediateDatablock, Iterator[IntermediateDatablock]]:
                    """
                    Cleans and optimizes IntermediateDatablocks to produce the final blocks to be created.

                    Returns next block to be created and an iterator to keep searching.

                    Current optimizations
                    - For the same dataref path and values, 3 orthogonal axis in a row are merged
                    - Duplicate location lists, rotations, and show/hides overwrite previous values
                    - Sequential ANIM_show/hides are merged
                    - TRIS take animations from parent empties, reducing parents

                    Arbitrary rotation axis are not supported (anywhere), locations and rotations even for the same dataref path and values are not skipped

                    Not Optimized
                    - Optimize out duplicate Show/Hide

                    TODO Algorithms
                    - Don't reduce locations when locations are different but dataref values are same.
                    This requires user attention to fix
                    """
                    i = -1
                    while True:
                        i += 1
                        searching_itr, peek_next_block_itr = itertools.tee(
                            searching_itr
                        )

                        try:
                            next_block = next(peek_next_block_itr)
                        except StopIteration:
                            # TODO: Wait! What about self optimizations!
                            # No next block, nothing to accumulate
                            break
                        else:
                            next_name = next_block.name
                            next_block_type = next_block.datablock_info.datablock_type
                            breakpoint()
                            if next_block_type == "MESH":
                                # TODO: Needs unit test showing replacement happens only with 1 child mesh
                                # multiple child meshes or mixed child meshes and empties doesn't work
                                def replace_intermediate_with_child_mesh():
                                    next_block.animations_to_apply = copy.copy(
                                        intermediate_block.animations_to_apply
                                    )
                                    next_block.datablock_info.parent_info = copy.copy(
                                        intermediate_parent_info
                                    )

                                if len(intermediate_block.children) == 1:
                                    replace_intermediate_with_child_mesh()
                                return next_block, peek_next_block_itr
                            elif next_block_type == "EMPTY":
                                assert (
                                    next_block.animations_to_apply
                                ), f"{next_name} is EMPTY and must have animations"
                                next_animations = next_block.animations_to_apply
                                next_animation = next_animations[0]
                                # This is not to say it is a __valid__ animation
                                is_loc_anim = bool(next_animation.locations)
                                is_rot_anim = bool(next_animation.rotations)
                                next_dataref = next_animation.xp_dataref
                                next_path = next_dataref.path
                                next_block_parent = next_block.parent

                                def merge_orthogonal_rotation_axis():
                                    for (
                                        axis,
                                        degrees,
                                    ) in next_animation.rotations.items():
                                        if round_vec(
                                            axis, PRECISION_KEYFRAME
                                        ).freeze() in {
                                            Vector((1, 0, 0)).freeze(),
                                            Vector((0, 1, 0)).freeze(),
                                            Vector((0, 0, 1)).freeze(),
                                        }:
                                            intermediate_animation.rotations[
                                                axis
                                            ] = degrees
                                    # We don't know actually what optimizations to apply yet and what the effects should be
                                    reparent_children_to_new_block(
                                        next_block,
                                        intermediate_block,
                                    )

                                    return intermediate_block

                                if is_interm_rot_anim:
                                    in_block = merge_orthogonal_rotation_axis()

                                # Merge Show/Hides
                                def merge_show_hide_animations():
                                    """
                                    If the next EMPTY is simply a show/hide,
                                    absorb it's animations
                                    """
                                    for next_anim in (
                                        next_anim
                                        for next_anim in next_animations
                                        if next_anim.anim_type
                                        in {ANIM_TYPE_SHOW, ANIM_TYPE_HIDE}
                                    ):
                                        print(
                                            f"{intermediate_name} from show/hide from {next_name}"
                                        )
                                        intermediate_block.animations_to_apply.append(
                                            next_anim
                                        )
                                    reparent_children_to_new_block(
                                        next_block,
                                        intermediate_block,
                                    )

                                if not (is_loc_anim or is_rot_anim):
                                    merge_show_hide_animations()

                            searching_itr = peek_next_block_itr
                            # What we need: Big if statement to collect optimizations to run, in what order, what should be done to the intermediate block, if you're getting rid of it who to reparent to, what shuold happen to the next block. We need a big ordered table.

                            # TODO: We only stop optimizing when we get to a TRIS.
                            # If we somehow made empties and didn't get to a TRIS we've either corrupted the TREE
                            # or made empties for no animation which should be gotten rid of
                            if False:
                                assert {intermediate_block_type, next_block_type} == {
                                    "EMPTY"
                                }, f"{intermediate_name}'s and {next_name}'s type are {intermediate_block_type, next_block_type}, should be 'EMPTY'"
                                if intermediate_dataref == next_dataref:
                                    if next_animation.locations:
                                        logger.warn(
                                            f"{intermediate_name} and {next_name} have different locations for the same dataref value range. Overwriting"
                                        )
                                        intermediate_animation.locations.append(
                                            next_animation.locations
                                        )
                                    # TODO: Change to if to combine locations and all rotations!
                                    elif next_animation.rotations:
                                        if (
                                            intermediate_animation.rotations.keys()
                                            & next_animation.rotations.keys()
                                        ):
                                            logger.warn(
                                                f"{intermediate_name} and {next_name} have overlapping axis for the same dataref range. Using {next_name}'s values"
                                            )
                                        intermediate_animation.rotations.update(
                                            next_animation.rotations
                                        )
                                    else:
                                        logger.warn(
                                            f"{intermediate_name} and {next_name} have duplicate show/hide animations, skipping block"
                                        )
                                elif all(
                                    dref.anim_type in {ANIM_TYPE_SHOW, ANIM_TYPE_HIDE}
                                    for dref in [intermediate_dataref, next_dataref]
                                ):
                                    intermediate_block.animations_to_apply.append(
                                        next_animation
                                    )

                                # With next_block being made irrelevant, adjust the parentage of any
                                # future blocks to be next_block's parent
                                for future_block in copy.copy(peek_next_block_itr):
                                    future_parent = getattr(
                                        future_block.datablock_info.parent_info,
                                        "parent",
                                        None,
                                    )
                                    if future_parent == next_name:
                                        future_block.datablock_info.parent_info = (
                                            next_block.datablock_info.parent_info
                                        )

                                searching_itr = peek_next_block_itr
                            # end elif next_block_type == "EMPTY":
                    # end while

                    return (intermediate_block, searching_itr)

                print(f"IN {intermediate_block.name}")
                out_block, blocks_rem_itr = optimize_empty_chain(
                    intermediate_block, blocks_rem_itr
                )
                print(
                    f"OUT {out_block.name}, parent: {out_block.parent}, type: {out_block.datablock_info.datablock_type}"
                )
                if out_block.datablock_info.datablock_type == "EMPTY":
                    ob = test_creation_helpers.create_datablock_empty(
                        out_block.datablock_info
                    )
                elif out_block.datablock_info.datablock_type == "MESH":
                    ob = out_block.build_mesh(self.vt_table)
            elif intermediate_block_type == "MESH":
                ob = intermediate_block.build_mesh(self.vt_table)

            ob.matrix_local = intermediate_block.bake_matrix.copy()
            for animation in intermediate_block.animations_to_apply:
                animation.apply_animation(ob)

        # TODO: Unit test, and what about a bunch of animations that get optimized out with not TRIS blocks?
        # Put this later
        if not bpy.data.objects:
            logger.warn(".obj had no real blocks to create")
            return {"CANCELLED"}

        bpy.context.scene.frame_set(1)
        return {"FINISHED"}

    @property
    def _top_animation(self) -> Optional[IntermediateAnimation]:
        try:
            return self._anim_intermediate_stack[-1].animation
        except IndexError:
            return None

    @_top_animation.setter
    def _top_animation(self, value: IntermediateAnimation) -> None:
        self._anim_intermediate_stack[-1].animation = value

    @property
    def _top_intermediate_datablock(self) -> Optional[IntermediateDatablock]:
        try:
            return self._anim_intermediate_stack[-1].intermediate_datablock
        except IndexError:
            return None

    @_top_intermediate_datablock.setter
    def _top_intermediate_datablock(self, value: IntermediateDatablock) -> None:
        self._anim_intermediate_stack[-1].intermediate_datablock = value

    @property
    def _top_dataref(self) -> Optional[IntermediateDataref]:
        return self._top_animation.xp_dataref

    @_top_dataref.setter
    def _top_dataref(self, value: IntermediateDataref) -> None:
        self._top_animation.xp_dataref = value

    def _next_empty_name(self) -> str:
        return (
            f"ImpEmpty."
            f"{sum(1 for block in self._blocks if block.datablock_info.datablock_type == 'EMPTY'):03}"
            f"_{hex(hash(self.root_collection.name))[2:6]}"
            f"_{random.randint(0,100000)}"
        )

    def _next_object_name(self) -> str:
        return (
            f"ImpMesh."
            f"{sum(1 for block in self._blocks if block.datablock_info.datablock_type == 'MESH'):03}"
            f"_{hex(hash(self.root_collection.name))[2:6]}"
            f"_{random.randint(0,100000)}"
        )