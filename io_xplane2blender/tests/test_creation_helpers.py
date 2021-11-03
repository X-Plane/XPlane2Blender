"""
test_creation_tools

These allow the quick automated setup of test cases

- get_ get's a Blender datablock or piece of data or None
- set_ set's some data, possibly creating data as needed.
- create_ creates and returns exist Blender data, or returns existing data with the same name
- delete_ deletes all of a certain type from the scene

This also is a wrapper around Blender's more confusing aspects of it's API and datamodel.
https://blender.stackexchange.com/questions/6101/poll-failed-context-incorrect-example-bpy-ops-view3d-background-image-add
"""

import math
import os.path
import shutil
import typing
from collections import namedtuple
from dataclasses import dataclass
from pathlib import Path
from typing import *

import bpy
from mathutils import Euler, Quaternion, Vector

import io_xplane2blender
from io_xplane2blender import xplane_constants, xplane_helpers
from io_xplane2blender.xplane_constants import ANIM_TYPE_HIDE, ANIM_TYPE_SHOW
from io_xplane2blender.xplane_helpers import (
    ExportableRoot,
    PotentialRoot,
    XPlaneLogger,
    logger,
)
from io_xplane2blender.xplane_props import XPlaneManipulatorSettings
from io_xplane2blender.xplane_types import xplane_file

# Most used commands:
#
#

# Most used datarefs:
#
# - sim/cockpit2/engine/actuators/throttle_ratio_all    float    y    ratio    Throttle position of the handle itself - this controls all the handles at once.
# - sim/graphics/animation/sin_wave_2    float    n    ratio    -1 to 1

# Most used named/param lights
# area_lt_param_sp
# 0 -1 0    75
# spot_params_bb
# 1 1 1 1.0 2.121 0 2.121 -2
# spot_params_sp
# 0 .2 1    20 30   0 -1  0   1

# Rotations, when in euler's, are in angles, and get transformed when they need to.

# Constants
_ARMATURE = "ARMATURE"
_BONE = "BONE"
_OBJECT = "OBJECT"


@dataclass
class AxisAngle:
    """AA class with named members. angle is in radians"""

    axis: Vector
    angle: float

    def to_object_rotation_axis_angle(self) -> Tuple[float, float, float, float]:
        """For use with an object's rotation_axis_angle member"""
        return (self.angle, *self.axis)

    def to_euler(
        self, order: str = "XYZ", euler_compat: Optional[Euler] = None
    ) -> Euler:
        return self.to_quaternion().to_euler(order, euler_compat)

    def to_quaternion(self) -> Quaternion:
        return Quaternion(self.axis, self.angle)


# This API uses AA, Euler, a tuple of 3 degrees to be converted to Euler, and Quaternion
RotationType = Union[AxisAngle, Euler, Tuple[float, float, float], Quaternion]


class AxisDetentRangeInfo:
    def __init__(self, start: float, end: float, height: float):
        self.start = start
        self.end = end
        self.height = height


class BoneInfo:
    def __init__(self, name: str, head: Vector, tail: Vector, parent: str):
        assert len(head) == 3 and len(tail) == 3
        self.name = name
        self.head = head
        self.tail = tail

        def round_vec(vec):
            return Vector([round(comp, 5) for comp in vec])

        assert (round_vec(self.tail) - round_vec(self.head)) != Vector((0, 0, 0))
        self.parent = parent


class DatablockInfo:
    """
    The POD struct used for creating datablocks.
    If None is given as a parameter, sensible defaults are used:

    parent_info - When None no parent is assigned
    collection - When None, current scene's 'Master Collection' is used
    rotation - When None, the default for rotation_mode is used

    Values for datablock_type must be 'MESH', 'ARMATURE', 'EMPTY', or "LIGHT"
    """

    def __init__(
        self,
        datablock_type: str,
        name: str,
        parent_info: "ParentInfo" = None,
        collection: Optional[Union[str, bpy.types.Collection]] = None,
        location: Vector = Vector((0, 0, 0)),
        rotation_mode: str = "XYZ",
        rotation: Optional[RotationType] = None,
        scale: Vector = Vector((1, 1, 1)),
    ):
        self.datablock_type = datablock_type
        self.name = name
        if collection is None:
            self.collection = bpy.context.scene.collection
        else:
            self.collection = (
                collection
                if isinstance(collection, bpy.types.Collection)
                else create_datablock_collection(collection)
            )

        self.parent_info = parent_info
        self.location = location
        self.rotation_mode = rotation_mode
        self.rotation = rotation
        if self.rotation is None:
            if self.rotation_mode == "AXIS_ANGLE":
                self.rotation = AxisAngle()
            elif self.rotation_mode == "QUATERNION":
                self.rotation = Quaternion()
            elif set(self.rotation_mode) == {"X", "Y", "Z"}:
                self.rotation = Euler()
            else:
                assert False, "Unsupported rotation mode: " + self.rotation_mode
        else:
            if self.rotation_mode == "AXIS_ANGLE":
                assert len(self.rotation[1]) == 3
                self.rotation_axis_angle = rotation
            elif self.rotation_mode == "QUATERNION":
                assert len(self.rotation) == 4
                self.rotation_quaternion = rotation
            elif set(self.rotation_mode) == {"X", "Y", "Z"} and isinstance(
                rotation, Euler
            ):
                assert len(self.rotation) == 3
                self.rotation_euler = rotation
            elif set(self.rotation_mode) == {"X", "Y", "Z"} and isinstance(
                rotation, tuple
            ):
                assert len(self.rotation) == 3
                self.rotation_euler = Euler(map(math.radians, rotation), rotation_mode)
            else:
                assert False, "Unsupported rotation mode: " + self.rotation_mode

        self.scale = scale


class KeyframeInfo:
    def __init__(
        self,
        idx: int,
        dataref_path: str,
        dataref_value: Optional[float] = None,
        dataref_show_hide_v1: Optional[float] = None,
        dataref_show_hide_v2: Optional[float] = None,
        dataref_loop: Optional[float] = None,
        dataref_anim_type: str = xplane_constants.ANIM_TYPE_TRANSFORM,  # Must be xplane_constants.ANIM_TYPE_*
        location: Optional[Vector] = None,
        rotation_mode: str = "XYZ",
        rotation: Optional[RotationType] = None,
    ):
        """
        Everything needed to automate setting Object Location/Rotation and
        XPlane2Blender Dataref props, then making a keyframe.

        When rotation is a tuple, it is converted to radians, then into a Euler
        """
        self.idx = idx
        self.dataref_path = dataref_path
        self.dataref_value = dataref_value
        self.dataref_show_hide_v1 = dataref_show_hide_v1
        self.dataref_show_hide_v2 = dataref_show_hide_v2
        self.dataref_loop = dataref_loop
        self.dataref_anim_type = dataref_anim_type
        self.location = location
        self.rotation_mode = rotation_mode
        self.rotation = (
            Euler(map(math.radians, rotation), rotation_mode)
            if isinstance(rotation, tuple)
            else rotation
        )

        if self.rotation:
            if self.rotation_mode == "AXIS_ANGLE":
                assert len(self.rotation.axis) == 3
            elif self.rotation_mode == "QUATERNION":
                assert len(self.rotation) == 4
            elif {*self.rotation_mode} == {"X", "Y", "Z"}:
                assert len(self.rotation) == 3
            else:
                assert False, "Unsupported rotation mode: " + self.rotation_mode

    def __str__(self) -> str:
        """For ease of debugging, rotation is always converted to degrees"""
        s = f"({self.idx}, {self.dataref_path}, {self.dataref_value}, {self.dataref_show_hide_v1}, {self.dataref_show_hide_v2}, {self.dataref_anim_type}, {self.location}, {self.rotation_mode}, "
        if {*self.rotation_mode} == {"X", "Y", "Z"}:
            s += f"{tuple(map(math.degrees, self.rotation))})"
        else:
            s += f"{self.rotation})"
        return s


# Common presets for animations
R_2_FRAMES_45_Y_AXIS = (
    KeyframeInfo(
        idx=1,
        dataref_path="sim/cockpit2/engine/actuators/throttle_ratio_all",
        dataref_value=0.0,
        rotation=(0, 0, 0),
    ),
    KeyframeInfo(
        idx=2,
        dataref_path="sim/cockpit2/engine/actuators/throttle_ratio_all",
        dataref_value=1.0,
        rotation=(0, 45, 0),
    ),
)

T_2_FRAMES_1_X = (
    KeyframeInfo(
        idx=1,
        dataref_path="sim/graphics/animation/sin_wave_2",
        dataref_value=0.0,
        location=(0, 0, 0),
    ),
    KeyframeInfo(
        idx=2,
        dataref_path="sim/graphics/animation/sin_wave_2",
        dataref_value=1.0,
        location=(1, 0, 0),
    ),
)

T_2_FRAMES_1_Y = (
    KeyframeInfo(
        idx=1,
        dataref_path="sim/graphics/animation/sin_wave_2",
        dataref_value=0.0,
        location=(0, 0, 0),
    ),
    KeyframeInfo(
        idx=2,
        dataref_path="sim/graphics/animation/sin_wave_2",
        dataref_value=1.0,
        location=(0, 1, 0),
    ),
)

SHOW_ANIM_S = (
    KeyframeInfo(
        idx=1,
        dataref_path="show_hide_dataref_show",
        dataref_show_hide_v1=0.0,
        dataref_show_hide_v2=100.0,
        dataref_anim_type=xplane_constants.ANIM_TYPE_SHOW,
    ),
)

SHOW_ANIM_H = (
    KeyframeInfo(
        idx=1,
        dataref_path="show_hide_dataref_hide",
        dataref_show_hide_v1=100.0,
        dataref_show_hide_v2=200.0,
        dataref_anim_type=xplane_constants.ANIM_TYPE_HIDE,
    ),
)

SHOW_ANIM_FAKE_T = (
    KeyframeInfo(idx=1, dataref_path="none", dataref_value=0.0, location=(0, 0, 0)),
    KeyframeInfo(idx=2, dataref_path="none", dataref_value=1.0, location=(0, 0, 0)),
)


class ParentInfo:
    def __init__(
        self,
        parent: Optional[Union[bpy.types.Object, str]] = None,
        parent_type: str = _OBJECT,  # Must be "ARMATURE", "BONE", or "OBJECT"
        parent_bone: Optional[str] = None,
    ):
        assert (
            parent_type == _ARMATURE or parent_type == _BONE or parent_type == _OBJECT
        )
        if parent:
            assert isinstance(parent, (bpy.types.Object, str))

        if parent_bone:
            assert isinstance(parent_bone, str)
        self.parent = parent
        self.parent_type = parent_type
        self.parent_bone = parent_bone

    def __str__(self):
        return f"Parent: {self.parent}, Parent Type: {self.parent_type}, Parent Bone: {self.parent_bone}"


def create_bone(armature: bpy.types.Object, bone_info: BoneInfo) -> str:
    """
    Since, in Blender, Bones have a number of representations, here we pass back the final name of the new bone
    which can be used with data.edit_bones,data.bones,and pose.bones. The final name may not be the name inside
    new_bone.name
    """
    assert armature.type == "ARMATURE"
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode="EDIT", toggle=False)
    edit_bones = armature.data.edit_bones
    new_bone = edit_bones.new(bone_info.name)
    new_bone.head = bone_info.head
    new_bone.tail = bone_info.tail
    if len(armature.data.bones) > 0:
        assert bone_info.parent in edit_bones
        print("bone_info.parent = {}".format(bone_info.parent))
        new_bone.parent = edit_bones[bone_info.parent]
    else:
        new_bone.parent = None

    # Keeping old references around crashing Blender
    final_name = new_bone.name
    bpy.ops.object.mode_set(mode="OBJECT")

    return final_name


def create_datablock_collection(
    name: str,
    scene: Optional[Union[str, bpy.types.Scene]] = None,
    parent: Optional[Union[bpy.types.Collection, str]] = None,
) -> bpy.types.Collection:
    """
    If already existing, return it. If not, creates a collection
    with the name provided. It can be linked to a scene and a parent
    other that that scene's Master Collection. (Parent must be in scene as well.)

    Otherwise, the context's scene and Master Collection is used for linking.
    """
    try:
        coll: bpy.types.Collection = bpy.data.collections[name]
    except (KeyError, TypeError):
        coll: bpy.types.Collection = bpy.data.collections.new(name)
    try:
        scene: bpy.types.Scene = bpy.data.scenes[scene]
    except (KeyError, TypeError):  # scene is str and not found or is None
        scene: bpy.types.Scene = bpy.context.scene
    try:
        parent: bpy.types.Collection = bpy.data.collections[parent]
    except (KeyError, TypeError):  # parent is str and not found or is Collection
        parent: bpy.types.Collection = scene.collection

    if coll.name not in parent.children:
        parent.children.link(coll)

    return coll


def create_datablock_armature(
    info: DatablockInfo,
    extra_bones: Optional[Union[List[BoneInfo], int]] = None,
    bone_direction: Optional[Vector] = None,
) -> bpy.types.Object:
    """
    Creates an armature datablock with (optional) extra bones.
    Extra bones can come in the form of a list of BoneInfos you want created and parented or
    a number of bones and a unit vector in the direction you want them grown in
    When using extra_bones, the intial armature bone's data is replaced by the first bone

    1. extra_bones=None and bone_direction=None
        Armature (uses defaults armature) of bpy.)
        |_Bone
    2. Using extra_bones:List[BoneInfo]
        Armature
        |_extra_bones[0]
            |_extra_bones[1]
                |_extra_bones[2]
                    |_... (parent data given in each bone and can be different than shown)
    3. Using extra_bones:int and bone_direction
        Armature                                                               [Armature]
        |_new_bone_0                                                          / extra_bones = 3
            |_new_bone_1                                                     /  bone_direction = (-1,-1, 0)
                |_new_bone_2                                                /
                    |_new_bone_... (where each bone is in a straight line) v
    """
    assert info.datablock_type == "ARMATURE"
    bpy.ops.object.armature_add(
        enter_editmode=False, location=info.location, rotation=info.rotation
    )
    arm = bpy.context.object
    arm.name = info.name if info.name is not None else arm.name
    arm.rotation_mode = info.rotation_mode
    arm.scale = info.scale

    if info.parent_info:
        set_parent(arm, info.parent_info)

    parent_name = ""
    if extra_bones:
        bpy.ops.object.mode_set(mode="EDIT", toggle=False)
        arm.data.edit_bones.remove(arm.data.edit_bones[0])
        bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

    if extra_bones and bone_direction:
        assert (
            isinstance(extra_bones, int)
            and isinstance(bone_direction, Vector)
            and bone_direction != Vector()
        )

        head = Vector((0, 0, 0))
        for extra_bone_counter in range(extra_bones):
            tail = head + bone_direction
            parent_name = create_bone(
                arm,
                BoneInfo("bone_{}".format(extra_bone_counter), head, tail, parent_name),
            )
            head += bone_direction

    if extra_bones and not bone_direction:
        assert isinstance(extra_bones, list) and isinstance(extra_bones[0], BoneInfo)
        for extra_bone in extra_bones:
            create_bone(arm, extra_bone)

    return arm


def create_datablock_empty(
    info: DatablockInfo,
    scene: Optional[Union[bpy.types.Scene, str]] = None,
    empty_display_type: str = "PLAIN_AXES",
    empty_display_size=1,
) -> bpy.types.Object:
    """
    Creates a datablock empty and links it to a scene and collection.
    If scene is None, the current context's scene is used.
    """
    assert info.datablock_type == "EMPTY"
    ob = bpy.data.objects.new(info.name, object_data=None)
    try:
        scene = bpy.data.scenes[scene]
    except (KeyError, TypeError):
        scene = bpy.context.scene
    set_collection(ob, info.collection)

    ob.empty_display_type = empty_display_type
    ob.empty_display_size = empty_display_size
    ob.location = info.location
    ob.rotation_mode = info.rotation_mode
    set_rotation(ob, info.rotation, info.rotation_mode)
    ob.scale = info.scale

    if info.parent_info:
        set_parent(ob, info.parent_info)

    return ob


@dataclass
class From_PyData:
    vertices: List[Tuple[float, float, float]]
    edges: List[Tuple[int, int]]
    faces: List[Tuple[int, int, int]]


def create_datablock_mesh(
    info: DatablockInfo,
    mesh_src: Union[str, bpy.types.Mesh, From_PyData] = "cube",
    material_name: Union[bpy.types.Material, str] = "Material",
    scene: Optional[Union[bpy.types.Scene, str]] = None,
) -> bpy.types.Object:
    """
    Uses the bpy.ops.mesh.primitive_*_add ops to create an Object with given
    mesh. Location and Rotation given by info.

    mesh_data must be (listed in evaluation order)
    - An existing mesh datablock that will be used instead
    - An existing mesh datablock name
    - "tri" or "eq-tri" which makes a right or equilateral triangle
    - primative op like "cube" or "plane"
    - Data for `from_pydata`
    """

    assert info.datablock_type == "MESH"

    ops = {
        "circle",
        "cone",
        "cube",
        "cylinder",
        "grid",
        "ico_sphere",
        "monkey",
        "plane",
        "torus",
        "uv_sphere",
    }

    def create_object(name, mesh):
        ob = bpy.data.objects.new(name, object_data=mesh)
        return ob

    if isinstance(mesh_src, bpy.types.Mesh):
        me = mesh_src
        ob = create_object(info.name, me)
    elif isinstance(mesh_src, str) and mesh_src in bpy.data.meshes:
        me = bpy.data.meshes[mesh_src]
        ob = create_object(info.name, me)
    elif isinstance(mesh_src, From_PyData) or mesh_src == "eq-tri" or mesh_src == "tri":
        me = bpy.data.meshes.new(f"Mesh.{len(bpy.data.meshes)}:03")
        if mesh_src == "tri":
            verts = [(1.0, -1.0, 0.0), (1.0, 1.0, 0.0), (-1.0, -1.0, 0.0)]
            from_data = [
                verts,
                [],
                [(2, 1, 0)],
            ]
        elif mesh_src == "eq-tri":
            verts = [
                (1, -1, 0),
                (0, 1, 0),
                (-1, -1, 0),
            ]
            from_data = [
                verts,
                [],
                [(2, 1, 0)],
            ]
        else:
            from_data = (mesh_src.vertices, mesh_src.edges, mesh_src.faces)

        me.from_pydata(from_data[0], from_data[1], from_data[2])
        me.validate()
        ob = create_object(info.name, me)

    elif mesh_src in ops:
        primitive_ops: Dict[str, bpy.types.Operator] = {
            "circle": bpy.ops.mesh.primitive_circle_add,
            "cone": bpy.ops.mesh.primitive_cone_add,
            "cube": bpy.ops.mesh.primitive_cube_add,
            "cylinder": bpy.ops.mesh.primitive_cylinder_add,
            "grid": bpy.ops.mesh.primitive_grid_add,
            "ico_sphere": bpy.ops.mesh.primitive_ico_sphere_add,
            "monkey": bpy.ops.mesh.primitive_monkey_add,
            "plane": bpy.ops.mesh.primitive_plane_add,
            "torus": bpy.ops.mesh.primitive_torus_add,
            "uv_sphere": bpy.ops.mesh.primitive_uv_sphere_add,
        }

        try:
            op = primitive_ops[mesh_src]
        except KeyError:
            assert False, f"{mesh_src} is not a known primitive op"
        else:
            op(enter_editmode=False, location=info.location, rotation=info.rotation)
            ob = bpy.context.object

    set_collection(ob, info.collection, unlink_others=True)
    ob.name = info.name if info.name is not None else ob.name
    ob.location = info.location
    set_rotation(ob, info.rotation, info.rotation_mode)
    if info.parent_info:
        set_parent(ob, info.parent_info)
    set_material(ob, material_name)

    if not ob.data.uv_layers:
        ob.data.uv_layers.new()

    return ob


def create_datablock_light(
    info: DatablockInfo,
    light_type: str,
    scene: Optional[Union[bpy.types.Scene, str]] = None,
):
    assert light_type in {"POINT", "SUN", "SPOT", "ARENA"}
    li = bpy.data.lights.new(info.name, light_type)
    ob = bpy.data.objects.new(info.name, li)
    set_collection(ob, info.collection)

    try:
        scene = bpy.data.scenes[scene]
    except (KeyError, TypeError):
        scene = bpy.context.scene
    set_collection(ob, info.collection)

    ob.location = info.location
    ob.rotation_mode = info.rotation_mode
    set_rotation(ob, info.rotation, info.rotation_mode)
    ob.scale = info.scale

    if info.parent_info:
        set_parent(ob, info.parent_info)

    return ob


def create_image_from_disk(filepath: Union[Path, str]) -> bpy.types.Image:
    """
    Create an image from a .png file on disk.

    Returns image or raises OSError
    """
    filepath = str(filepath)
    assert os.path.splitext(filepath)[1] in {".dds", ".png"}
    # Load image file. Change here if the snippet folder is
    # not located in you home directory.
    realpath = bpy.path.abspath(filepath.format(filepath))
    try:
        img = bpy.data.images.load(realpath, check_existing=True)
        img.filepath = bpy.path.relpath(realpath)
        return img
    except (RuntimeError, ValueError):  # Couldn't load or make relative path
        raise OSError("Cannot load image %s" % realpath)


def create_material(
    material_name: str,
    texture_image: Optional[Union[bpy.types.Image, Path, str]] = None,
):
    """
    Create a material and optionally give it a texture
    """
    try:
        mat = get_material(material_name)
    except KeyError:
        mat = bpy.data.materials.new(material_name)

    return mat


def create_material_default() -> bpy.types.Material:
    """
    Creates the default 'Material' if it doesn't already exist
    """
    return create_material("Material")


def create_scene(name: str) -> bpy.types.Scene:
    try:
        return bpy.data.scenes[name]
    except KeyError:
        return bpy.data.scenes.new(name)


# Do not include .png. It is only for the source path
def get_image(name: str) -> Optional[bpy.types.Image]:
    """
    New images will be created in //tex and will be a .png

    TODO: This API is incomplete, what if None found? What should happen?
    Creating a new image is almost never what you want, unlike creating a bland cube
    I vote KeyError which makes this a useless wrapper
    """
    return bpy.data.images.get(name)


def get_light(name: str) -> Optional[bpy.types.Light]:
    """
    Gets, if possible, Light data, not the light object
    """
    return bpy.data.lights.get(name)


# Returns the bpy.types.Material or creates it as needed
def get_material(material_name: str) -> Optional[bpy.types.Material]:
    return bpy.data.materials.get(material_name)


def get_material_default() -> bpy.types.Material:
    mat = bpy.data.materials.get("Material")
    if mat:
        return mat
    else:
        return create_material_default()


def delete_all_collections():
    for coll in bpy.data.collections:
        bpy.data.collections.remove(coll)


def delete_all_images():
    for image in bpy.data.images:
        image.user_clear()
        bpy.data.images.remove(image, do_unlink=True)


def delete_all_lights():
    for light in bpy.data.lights:
        light.user_clear()
        bpy.data.lights.remove(light, do_unlink=True)


def delete_all_materials():
    for material in bpy.data.materials:
        material.user_clear()
        bpy.data.materials.remove(material, do_unlink=True)


def delete_all_objects():
    for obj in bpy.data.objects:
        obj.user_clear()
        bpy.data.objects.remove(obj, do_unlink=True)


def delete_all_other_scenes():
    """
    Note: We can't actually delete all the scenes since there has to be one
    """
    for scene in bpy.data.scenes[1:]:
        scene.user_clear()
        bpy.data.scenes.remove(scene, do_unlink=True)


def delete_all_text_files(preserve_text_files: List[Union[str, bpy.types.Text]] = []):
    """
    Optionally pass in the names of Text Blocks
    to keep (for instance, the name of the script you're working on in app)
    """

    preserve_text_files = [getattr(t, "name", t) for t in preserve_text_files]
    for text in [t for t in bpy.data.texts if t.name not in preserve_text_files]:
        text.user_clear()
        bpy.data.texts.remove(text, do_unlink=True)


def delete_everything(preserve_text_files: List[Union[str, bpy.types.Text]] = []):
    """
    Warning! Don't call this from a Blender script!
    You'll delete the text block you're using!
    """
    delete_all_images()
    delete_all_materials()
    delete_all_objects()
    delete_all_text_files(preserve_text_files)
    delete_all_collections()
    delete_all_other_scenes()


def lookup_potential_root_from_name(name: str) -> PotentialRoot:
    """
    Attempts to find a Potential Root
    using the name of the collection or object

    Asserts that name is in bpy.data
    """
    assert isinstance(name, str), f"name must be a str, is {type(name)}"
    try:
        root_object = bpy.data.collections[name]
    except KeyError:
        try:
            root_object = bpy.data.objects[name]
        except KeyError:
            assert False, f"{name} must be in bpy.data.collections|objects"
    return root_object


def make_root_exportable(
    potential_root: Union[PotentialRoot, str],
    view_layer: Optional[bpy.types.ViewLayer] = None,
) -> ExportableRoot:
    """
    Makes a root, as given or as found by it's name from collections then root objects,
    meet the criteria for exportable - not disabled in viewport, not hidden in viewport, and checked Exportable.

    Returns that changed ExportableRoot
    """
    view_layer = view_layer or bpy.context.scene.view_layers[0]
    if isinstance(potential_root, str):
        potential_root = lookup_potential_root_from_name(potential_root)

    if isinstance(potential_root, bpy.types.Collection):
        potential_root.xplane.is_exportable_collection = True
        # This is actually talking about "Visibile In Viewport" - the little eyeball
        all_layer_collections = {
            lc.name: lc
            for lc in xplane_helpers.get_layer_collections_in_view_layer(view_layer)
        }
        all_layer_collections[potential_root.name].hide_viewport = False
    elif isinstance(potential_root, bpy.types.Object):
        potential_root.xplane.isExportableRoot = True
        # This is actually talking about "Visibile In Viewport" - the little eyeball
        potential_root.hide_set(False, view_layer=view_layer)
    else:
        assert False, "How did we get here?!"

    # This is actually talking about "Disable In Viewport"
    potential_root.hide_viewport = False
    return potential_root


def make_root_unexportable(
    exportable_root: Union[ExportableRoot, str],
    view_layer: Optional[bpy.types.ViewLayer] = None,
    hide_viewport: bool = False,
    disable_viewport: bool = False,
) -> ExportableRoot:
    """
    Makes a root, unexportable, and optionally, some type of
    hidden in the viewport. By default we just do the
    minimum - turning off exportablity
    """
    view_layer = view_layer or bpy.context.scene.view_layers[0]
    if isinstance(exportable_root, str):
        exportable_root = lookup_potential_root_from_name(exportable_root)

    if isinstance(exportable_root, bpy.types.Collection):
        exportable_root.xplane.is_exportable_collection = False
        # This is actually talking about "Visible In Viewport" - the little eyeball
        all_layer_collections = {
            lc.name: lc
            for lc in xplane_helpers.get_layer_collections_in_view_layer(view_layer)
        }
        all_layer_collections[exportable_root.name].hide_viewport = True
    elif isinstance(exportable_root, bpy.types.Object):
        exportable_root.xplane.isExportableRoot = True
        # This is actually talking about "Visible In Viewport" - the little eyeball
        exportable_root.hide_set(disable_viewport)
    else:
        assert False, "How did we get here?!"


def set_animation_data(
    blender_struct: Union[bpy.types.Object, bpy.types.Bone, bpy.types.PoseBone],
    keyframe_infos: List[KeyframeInfo],
    parent_armature: [bpy.types.Armature] = None,
) -> None:
    """
    - blender_struct - A Blender light, mesh, armature, or bone to attach keyframes to. For a bone, pass it
    in (excluding EditBones) and the function will take care of choosing between Bone and EditBone as needed
    - keyframe_infos - A list of keyframe info which will be used to apply keyframes
    - parent_armature - If the blender_struct is a Bone but not a PoseBone, the parent armature of it is required
    (because Bones do not keep track of who their parent armature is for some reason -Ted, 3/21/2018)

    keyframe_infos must be all the same dataref and all the same animation type. This was a deliberate choice
    to help catch errors in bad data
    """

    # Ensure each call to set_animation_data has the same dataref_path and anim_type
    # for each KeyframeInfo
    assert len({kf_info.dataref_path for kf_info in keyframe_infos}) == 1
    assert len({kf_info.dataref_anim_type for kf_info in keyframe_infos}) == 1

    if (
        keyframe_infos[0].dataref_anim_type == xplane_constants.ANIM_TYPE_SHOW
        or keyframe_infos[0].dataref_anim_type == xplane_constants.ANIM_TYPE_HIDE
    ):
        value = keyframe_infos[0].dataref_value
        value_1 = keyframe_infos[0].dataref_show_hide_v1
        value_2 = keyframe_infos[0].dataref_show_hide_v2
        assert value is None and value_1 is not None and value_2 is not None
    if keyframe_infos[0].dataref_anim_type == xplane_constants.ANIM_TYPE_TRANSFORM:
        value = keyframe_infos[0].dataref_value
        value_1 = keyframe_infos[0].dataref_show_hide_v1
        value_2 = keyframe_infos[0].dataref_show_hide_v2
        assert value is not None and value_1 is None and value_2 is None

    struct_is_bone = False
    if isinstance(blender_struct, bpy.types.Bone) or isinstance(
        blender_struct, bpy.types.PoseBone
    ):
        assert parent_armature is not None
        try:
            blender_bone = parent_armature.data.bones[blender_struct.name]
            blender_pose_bone = parent_armature.pose.bones[blender_struct.name]
            blender_struct = blender_pose_bone
            struct_is_bone = True
        except:
            assert False, "{} is not a pose bone in parent_armature {}".format(
                blender_struct.name, parent_armature.name
            )

    if struct_is_bone:
        datarefs = blender_bone.xplane.datarefs
    else:
        datarefs = blender_struct.xplane.datarefs
    # If this dataref has never been added before, add it. Otherwise,
    # find the index in the xplane.datarefs collection
    if not keyframe_infos[0].dataref_path in [dref.path for dref in datarefs]:
        dataref_prop = datarefs.add()
        dataref_prop.path = keyframe_infos[0].dataref_path
        dataref_prop.anim_type = keyframe_infos[0].dataref_anim_type
        dataref_index = len(datarefs) - 1
    else:
        dataref_index = 0
        for dref in datarefs:
            if dref.path == keyframe_infos[0].dataref_path:
                dataref_prop = dref
                break
            dataref_index += 1

    for kf_info in keyframe_infos:
        bpy.context.scene.frame_current = kf_info.idx

        if (
            kf_info.dataref_anim_type == ANIM_TYPE_SHOW
            or kf_info.dataref_anim_type == ANIM_TYPE_HIDE
        ):
            dataref_prop.show_hide_v1 = kf_info.dataref_show_hide_v1
            dataref_prop.show_hide_v2 = kf_info.dataref_show_hide_v2
        else:
            dataref_prop.value = kf_info.dataref_value
            # Multiple assignment isn't harmful
            if kf_info.dataref_loop is not None:
                dataref_prop.loop = kf_info.dataref_loop

        if not kf_info.location and not kf_info.rotation:
            continue

        if kf_info.location:
            blender_struct.location = kf_info.location
            blender_struct.keyframe_insert(
                data_path="location",
                group=blender_struct.name if struct_is_bone else "Location",
            )
        if kf_info.rotation:
            blender_struct.rotation_mode = kf_info.rotation_mode

            if set(kf_info.rotation_mode) == {"X", "Y", "Z"}:
                data_path = "rotation_euler"
            else:
                data_path = "rotation_{}".format(kf_info.rotation_mode.lower())

            set_rotation(blender_struct, kf_info.rotation, kf_info.rotation_mode)

            blender_struct.keyframe_insert(
                data_path=data_path,
                group=blender_bone.name if struct_is_bone else "Rotation",
            )

        if struct_is_bone:
            bpy.context.view_layer.objects.active = parent_armature
            bpy.context.view_layer.objects.active.data.bones.active = blender_bone
            bpy.ops.bone.add_xplane_dataref_keyframe(index=dataref_index)
        else:
            bpy.context.view_layer.objects.active = blender_struct
            bpy.ops.object.add_xplane_dataref_keyframe(
                {"object": blender_struct}, index=dataref_index
            )


def set_collection(
    blender_object: bpy.types.Object,
    collection: Union[bpy.types.Collection, str],
    unlink_others: bool = True,
) -> None:
    """
    Links a datablock in collection. If collection is a string and does not exist, one will be made.

    Use unlink_others unlinks the blender_object from all other collections (including the scene's master collection)
    """
    assert isinstance(
        blender_object, (bpy.types.Object)
    ), "collection was of type " + str(type(blender_object))

    if unlink_others:
        for coll in (
            coll
            for coll in xplane_helpers.get_collections_in_scene(bpy.context.scene)
            if blender_object.name in coll.objects
        ):
            coll.objects.unlink(blender_object)

    if isinstance(collection, bpy.types.Collection):
        coll = collection
    else:
        coll = create_datablock_collection(collection)

    if blender_object.name not in coll.objects:
        coll.objects.link(blender_object)


def set_manipulator_settings(
    object_datablock: bpy.types.Object,
    manip_type: str,
    manip_enabled: bool = True,
    manip_props: Optional[Dict[str, Any]] = None,
):
    """
    manip_type and manip_enabled, since they're the most common.
    if manip_props is left none, defaults for Cursor and Tooltip will be filled in
    using the object's name
    """
    assert object_datablock.type == "MESH"
    if manip_props is None:
        manip_props = {}

    object_datablock.xplane.manip.type = manip_type
    object_datablock.xplane.manip.enabled = manip_enabled
    if manip_enabled is False:
        return

    if "cursor" not in manip_props:
        manip_props["cursor"] = "hand"
    if "tooltip" not in manip_props:
        manip_props["tooltip"] = "{} type manipulator on {}".format(
            manip_type, object_datablock.name
        )

    for prop_name, value in manip_props.items():
        attr = getattr(object_datablock.xplane.manip, prop_name, None)
        assert attr is not None, "{} is not a real manip property!".format(prop_name)

        if prop_name == "axis_detent_ranges":
            for item in value:
                new_axis_detent_range = attr.add()
                new_axis_detent_range.start = item.start
                new_axis_detent_range.end = item.end
                new_axis_detent_range.height = item.height
        else:
            setattr(object_datablock.xplane.manip, prop_name, value)


def set_material(
    blender_object: bpy.types.Object,
    material_name: str = "Material",
    texture_image: Optional[Union[bpy.types.Image, Path, str]] = None,
):
    """
    Sets blender_object's 1st material slot to 'material_name'.

    Optionally a texture_image is used to  set up a basic
    shader with Base Color set to Image Texture

    Raises OSError if texture_image is a path and not a real image
    """

    mat = create_material(material_name)
    try:
        blender_object.material_slots[0].material = mat
    except IndexError:
        blender_object.data.materials.append(mat)

    if texture_image:
        mat.use_nodes = True
        tex_node = mat.node_tree.nodes.new("ShaderNodeTexImage")
        if isinstance(texture_image, bpy.types.Image):
            tex_node.image = texture_image
        elif isinstance(texture_image, Path) or texture_image.endswith(
            (".png", ".dds")
        ):
            tex_node.image = create_image_from_disk(texture_image)
        else:
            tex_node.image = get_image(texture_image)

        bsdf_node = mat.node_tree.nodes["Principled BSDF"]

        # TODO: We should make it nice and move it so it isn't overlapping
        mat.node_tree.links.new(
            tex_node.outputs["Color"], bsdf_node.inputs["Base Color"]
        )


def set_parent(blender_object: bpy.types.Object, parent_info: ParentInfo) -> None:
    assert isinstance(blender_object, bpy.types.Object)

    blender_object.parent = (
        parent_info.parent
        if isinstance(parent_info.parent, bpy.types.Object)
        else bpy.data.objects[parent_info.parent]
    )
    blender_object.parent_type = parent_info.parent_type

    if parent_info.parent_type == _BONE:
        assert (
            parent_info.parent.type == _ARMATURE
            and parent_info.parent.data.bones.get(parent_info.parent_bone) is not None
        )

        blender_object.parent_bone = parent_info.parent_bone


def set_rotation(
    blender_object: bpy.types.Object, rotation: RotationType, rotation_mode: str
) -> None:
    """
    Sets the rotation of a Blender Object and takes care of picking which
    rotation type to give the value to
    """
    if rotation_mode == "AXIS_ANGLE":
        assert isinstance(
            rotation, AxisAngle
        ), f"type is {type(rotation)}, should be AxisAngle"
        blender_object.rotation_axis_angle = rotation.to_object_rotation_axis_angle()
    elif rotation_mode == "QUATERNION":
        assert len(rotation) == 4
        blender_object.rotation_quaternion = rotation
    elif set(rotation_mode) == {"X", "Y", "Z"} and isinstance(rotation, Euler):
        assert len(rotation) == 3
        blender_object.rotation_euler = rotation
    elif set(rotation_mode) == {"X", "Y", "Z"} and isinstance(rotation, tuple):
        assert len(rotation) == 3
        blender_object.rotation_euler = Euler(map(math.radians, rotation))
    else:
        assert False, "Unsupported rotation mode: " + blender_object.rotation_mode
    blender_object.rotation_mode = rotation_mode


def set_xplane_layer(
    layer: Union[int, io_xplane2blender.xplane_props.XPlaneLayer],
    layer_props: Dict[str, Any],
):
    assert isinstance(layer, int) or isinstance(
        layer, io_xplane2blender.xplane_props.XPlaneLayer
    )

    if isinstance(layer, int):
        layer = create_datablock_collection(f"Layer {layer + 1}").xplane.layer

    for prop, value in layer_props.items():
        setattr(layer, prop, value)


class TemporaryStartFile:
    def __init__(self, temporary_startup_path: str):
        self.temporary_startup_path = temporary_startup_path

    def __enter__(self) -> None:
        real_startup_filepath = os.path.join(
            bpy.utils.user_resource("CONFIG"), "startup.blend"
        )
        try:
            os.replace(real_startup_filepath, real_startup_filepath + ".bak")
        except FileNotFoundError as e:
            print(e)
            raise
        else:
            shutil.copyfile(self.temporary_startup_path, real_startup_filepath)
        bpy.ops.wm.read_homefile()

    def __exit__(self, type, value, traceback) -> None:
        real_startup_filepath = os.path.join(
            bpy.utils.user_resource("CONFIG"), "startup.blend"
        )
        os.replace(real_startup_filepath + ".bak", real_startup_filepath)
        return False


def create_initial_test_setup():
    bpy.ops.wm.read_homefile()
    delete_everything()
    xplane_file._all_keyframe_infos.clear()
    logger.clear()
    logger.addTransport(
        xplane_helpers.XPlaneLogger.InternalTextTransport(),
        xplane_constants.LOGGER_LEVELS_ALL,
    )
    logger.addTransport(XPlaneLogger.ConsoleTransport())
    create_material_default()

    # Create text file
    header_str = "Unit Test Overview"
    try:
        unit_test_overview = bpy.data.texts[header_str]
    except KeyError:
        unit_test_overview = bpy.data.texts.new(header_str)
    finally:
        unit_test_overview.write(header_str + "\n\n")

    # bpy.ops.console.insert(text="bpy.ops.export.xplane_obj()")
