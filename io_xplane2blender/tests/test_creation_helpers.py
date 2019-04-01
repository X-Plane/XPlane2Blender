import math
import os.path
from collections import namedtuple

import typing
from typing import *

import bpy
import mathutils
from bpy.types import Armature, Bone, ImageTexture, Material, Object, PoseBone
from mathutils import Euler, Quaternion, Vector

import io_xplane2blender
from io_xplane2blender import xplane_constants
from io_xplane2blender.xplane_constants import (ANIM_TYPE_HIDE, ANIM_TYPE_SHOW,
                                                ANIM_TYPE_TRANSFORM)
from io_xplane2blender.xplane_helpers import XPlaneLogger, logger
from io_xplane2blender.xplane_props import XPlaneManipulatorSettings

'''
test_creation_tools

These allow the quick automated setup of test cases

- get_ get's a Blender datablock or piece of data or None
- set_ set's some data, possibly creating data as needed.
- create_ creates and returns exist Blender data, or returns existing data with the same name
- delete_ deletes all of a certain type from the scene

This also is a wrapper around Blender's more confusing aspects of it's API and datamodel.
https://blender.stackexchange.com/questions/6101/poll-failed-context-incorrect-example-bpy-ops-view3d-background-image-add
'''

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
_BONE     = "BONE"
_OBJECT   = "OBJECT"

class AxisDetentRangeInfo():
    def __init__(self,start:float,end:float,height:float):
        self.start = start
        self.end = end
        self.height = height

class BoneInfo():
    def __init__(self, name:str, head:Vector, tail:Vector, parent:str):
        assert len(head) == 3 and len(tail) == 3
        self.name = name
        self.head = head
        self.tail = tail
        def round_vec(vec):
            return Vector([round(comp,5) for comp in vec])
        assert (round_vec(self.tail) - round_vec(self.head)) != Vector((0,0,0))
        self.parent = parent

class DatablockInfo():
    def __init__(self,
            datablock_type:str,
            name:Optional[str]=None,
            layers:Tuple[int]=tuple([True] + [False] * 19),
            parent_info:'ParentInfo'=None,
            location:Vector=Vector((0,0,0)),
            rotation_mode:str="XYZ",
            rotation:Optional[Union[bpy.types.bpy_prop_array,Euler,Quaternion]]=None,
            scale:Vector=Vector((1,1,1))):
        '''
        datablock_type: Must be 'MESH', 'ARMATURE', 'EMPTY', or 'LAMP'
        default for layers will be layer 1
        '''
        assert datablock_type in {"MESH", "ARMATURE", "EMPTY", "LAMP"}
        self.datablock_type = datablock_type
        self.name = name
        self.layers = layers
        self.parent_info = parent_info
        self.location = location
        self.rotation_mode = rotation_mode
        if rotation is None:
            if self.rotation_mode == "AXIS_ANGLE":
                self.rotation = (0.0,Vector((0,0,0,0)))
            elif self.rotation_mode == "QUATERNION":
                self.rotation = Quaternion((0.0, 0.0, 0.0, 0.0))
            elif set(self.rotation_mode) == {'X','Y','Z'}:
                self.rotation = mathutils.Euler()
        else:
            self.rotation = rotation

        self.scale = scale

class KeyframeInfo():
    def __init__(self,
            dataref_path:Optional[str],
            dataref_anim_type:Optional[str],
            location:Optional[Vector]=None,
            rotation_mode:Optional[str]="XYZ",
            rotation:Optional[Union[Tuple[float,Vector],Euler,Quaternion]]=None):
        '''
        KeyframeInfo that represents all the information needed to create Blender and/or
        XPlane2Blender keyframnes. Usually used to specify animations concisely.

        For Dataref Keyframe Values you must use only
        frame_number, dataref_path, dataref_value, ANIM_TYPE_TRANSFORM, and optionally a location and rotation (with mode)

        For Looping Keyframe Values you must use only dataref_path, dataref_value, ANIM_TYPE_TRANSFORM

        default parameters of None represents "no data set", not (0,0,0) or 0.0 or other common default
        '''
        if dataref_path:
            assert dataref_path != "", "Dataref Path cannot be empty"
        if dataref_anim_type:
            assert dataref_path is not None, "Cannot use dataref_anim_type {} without dataref".format(dataref_anim_type)

        assert dataref_anim_type in {ANIM_TYPE_HIDE, ANIM_TYPE_SHOW, ANIM_TYPE_TRANSFORM}

        if rotation:
            assert rotation_mode in {"QUATERNION", "AXIS_ANGLE"} or set(rotation_mode) == {'X','Y','Z'}, "rotation_mode {} for {} must a known rotation mode".format(rotation_mode,dataref_path)
            if rotation_mode == "AXIS_ANGLE":
                assert len(rotation[1]) == 3
            elif rotation_mode == "QUATERNION":
                assert len(rotation) == 4
            elif {*rotation_mode} == {'X','Y','Z'}:
                assert len(rotation) == 3
            else:
                assert False, "Unsupported rotation mode: " + rotation_mode

        self.dataref_path  = dataref_path
        self.dataref_anim_type = dataref_anim_type
        self.location      = location
        self.rotation_mode = rotation_mode
        self.rotation = rotation


class KeyframeInfoDatarefKeyframe(KeyframeInfo):
    def __init__(self,
            dataref_path:str,
            location:Optional[Vector]=None,
            rotation_mode:Optional[str]="XYZ",
            rotation:Optional[Union[Tuple[float,Vector],Euler,Quaternion]]=None,
            *,
            frame_number:int,
            dataref_value:float):
        super().__init__(dataref_path, ANIM_TYPE_TRANSFORM, location, rotation_mode, rotation)
        assert frame_number >= 0, "Frame number {} for {} must >= 0".format(frame_number, dataref_value)
        self.frame_number = frame_number
        self.dataref_value = dataref_value


class KeyframeInfoLoop(KeyframeInfo):
    def __init__(self,
            dataref_path:str,
            location:Optional[Vector]=None,
            rotation_mode:Optional[str]="XYZ",
            rotation:Optional[Union[Tuple[float,Vector],Euler,Quaternion]]=None,
            *,
            dataref_loop:float
        ):
        super().__init__(dataref_path, ANIM_TYPE_TRANSFORM, location, rotation_mode, rotation)

        self.dataref_loop = dataref_loop


class KeyframeInfoShowHide(KeyframeInfo):
    def __init__(self,
            dataref_path:str,
            location:Optional[Vector]=None,
            rotation_mode:Optional[str]="XYZ",
            rotation:Optional[Union[Tuple[float,Vector],Euler,Quaternion]]=None,
            *,
            dataref_anim_type:str,
            dataref_show_hide_v1:float,
            dataref_show_hide_v2:float
        ):
        '''
        Must be ANIM_TYPE_SHOW or ANIM_TYPE_HIDE
        '''
        assert dataref_anim_type in {ANIM_TYPE_SHOW, ANIM_TYPE_HIDE}, "KeyframeInfoShowHide keyframe must have the anim type be {} or {}".format(ANIM_TYPE_SHOW, ANIM_TYPE_HIDE)

        super().__init__(dataref_path, dataref_anim_type, location, rotation_mode, rotation)
        self.dataref_show_hide_v1 = dataref_show_hide_v1
        self.dataref_show_hide_v2 = dataref_show_hide_v2


# Common presets for animations
R_2_FRAMES_45_Y_AXIS = (
        KeyframeInfoDatarefKeyframe(
            dataref_path="sim/cockpit2/engine/actuators/throttle_ratio_all",
            rotation=(0,0,0),
            frame_number=1,
            dataref_value=0.0,
            ),
        KeyframeInfoDatarefKeyframe(
            dataref_path="sim/cockpit2/engine/actuators/throttle_ratio_all",
            rotation=(0,45,0),
            frame_number=2,
            dataref_value=1.0,
        )
    )

T_2_FRAMES_1_X = (
        KeyframeInfoDatarefKeyframe(
            dataref_path="sim/graphics/animation/sin_wave_2",
            location=(0,0,0),
            frame_number=1,
            dataref_value=0.0,
        ),
        KeyframeInfoDatarefKeyframe(
            dataref_path="sim/graphics/animation/sin_wave_2",
            location=(1,0,0),
            frame_number=2,
            dataref_value=1.0,
        )
    )

T_2_FRAMES_1_Y = (
        KeyframeInfoDatarefKeyframe(
            dataref_value=0.0,
            location=(0,0,0),
            frame_number=1,
            dataref_path="sim/graphics/animation/sin_wave_2",
        ),
        KeyframeInfoDatarefKeyframe(
            dataref_value=1.0,
            location=(0,1,0),
            frame_number=2,
            dataref_path="sim/graphics/animation/sin_wave_2",
        )
    )

SHOW_ANIM_S = (
        KeyframeInfoShowHide(
            dataref_path="show_hide_dataref_show",
            dataref_anim_type=ANIM_TYPE_SHOW,
            dataref_show_hide_v1=0.0,
            dataref_show_hide_v2=100.0,
        ),
    )

SHOW_ANIM_H = (
        KeyframeInfoShowHide(
            dataref_path="show_hide_dataref_hide",
            dataref_anim_type=ANIM_TYPE_HIDE,
            dataref_show_hide_v1=100.0,
            dataref_show_hide_v2=200.0,
        ),
    )

#SHOW_ANIM_FAKE_T = (
#        KeyframeInfo(
#            dataref_path="none",
#            dataref_show_hide_v1=0.0),
#        KeyframeInfo(
#            dataref_path="none",
#            dataref_show_hide_v2=1.0),
#        )

class ParentInfo():
    def __init__(self,
            parent:Optional[bpy.types.Object]=None,
            parent_type:str=_OBJECT, #Must be "ARMATURE", "BONE", or "OBJECT"
            parent_bone:Optional[str]=None)->None:
        assert parent_type == _ARMATURE or parent_type == _BONE or parent_type == _OBJECT
        if parent:
            assert isinstance(parent,bpy.types.Object)

        if parent_bone:
            assert isinstance(parent_bone,int) or isinstance(parent_bone,str) or isinstance(parent_bone,bpy.types.Bone)
        self.parent = parent
        self.parent_type = parent_type
        self.parent_bone = parent_bone

def create_bone(armature:bpy.types.Object,bone_info:BoneInfo)->str:
    '''
    Since, in Blender, Bones have a number of representations, here we pass back the final name of the new bone
    which can be used with data.edit_bones,data.bones,and pose.bones. The final name may not be the name inside
    new_bone.name
    '''
    assert armature.type =="ARMATURE"
    bpy.context.scene.objects.active = armature
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
    bpy.ops.object.mode_set(mode='OBJECT')

    return final_name


def create_datablock_armature(info:DatablockInfo,extra_bones:Optional[Union[List[BoneInfo],int]]=None,bone_direction:Optional[Vector]=None)->bpy.types.Object:
    '''
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
    '''
    assert info.datablock_type == "ARMATURE"
    bpy.ops.object.armature_add(
        enter_editmode=False,
        location=info.location,
        rotation=info.rotation,
        layers=info.layers)
    arm = bpy.context.object
    arm.name = info.name if info.name is not None else arm.name
    arm.rotation_mode = info.rotation_mode
    arm.scale = info.scale

    if info.parent_info:
        set_parent(arm,info.parent_info)

    parent_name = ""
    if extra_bones:
        bpy.ops.object.mode_set(mode="EDIT", toggle=False)
        arm.data.edit_bones.remove(arm.data.edit_bones[0])
        bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

    if extra_bones and bone_direction:
        assert isinstance(extra_bones,int) and\
               isinstance(bone_direction,Vector) and\
               bone_direction != Vector()

        head = Vector((0,0,0))
        for extra_bone_counter in range(extra_bones):
            tail = head + bone_direction
            parent_name = create_bone(arm,BoneInfo("bone_{}".format(extra_bone_counter),head,tail,parent_name))
            head += bone_direction

    if extra_bones and not bone_direction:
        assert isinstance(extra_bones,list) and\
               isinstance(extra_bones[0],BoneInfo)
        for extra_bone in extra_bones:
            create_bone(arm,extra_bone)

    return arm

def create_datablock_empty(info:DatablockInfo, special_type: str=xplane_constants.EMPTY_USAGE_NONE)->bpy.types.Object:
    assert info.datablock_type == "EMPTY"
    ob = bpy.data.objects.new(info.name, None)
    bpy.context.scene.objects.link(ob)

    ob.location = info.location
    if info.rotation_mode == "AXIS_ANGLE":
        ob.rotation_axis_angle = info.rotation
    elif info.rotation_mode == "QUATERNION":
        ob.rotation_quaternion = info.rotation
    else:
        ob.rotation_euler = info.rotation

    ob.layers = info.layers
    ob.name = info.name if info.name is not None else ob.name
    ob.rotation_mode = info.rotation_mode
    ob.scale = info.scale

    if info.parent_info:
        set_parent(ob, info.parent_info)

    ob.xplane.special_empty_props.special_type = special_type
    return ob

def create_datablock_lamp(info: DatablockInfo,
                          blender_light_type: str="POINT")->bpy.types.Object:
    assert info.datablock_type == "LAMP"
    assert blender_light_type in {"POINT", "SUN", "SPOT", "HEMI", "AREA"}
    lamp = bpy.data.lamps.new(info.name, blender_light_type)
    ob = bpy.data.objects.new(info.name, lamp)
    bpy.context.scene.objects.link(ob)
    if info.parent_info:
        set_parent(ob, info.parent_info)
    ob.location = info.location
    ob.rotation_mode = info.rotation_mode
    if info.rotation_mode == "AXIS_ANGLE":
        ob.rotation_axis_angle = info.rotation
    elif info.rotation_mode == "QUATERNION":
        ob.rotation_quaternion = info.rotation
    else:
        ob.rotation_euler = info.rotation

    ob.scale = info.scale

    return ob


def create_datablock_mesh(info:DatablockInfo,
                primitive_shape="cube", #Must be "cube" or "cylinder"
                material_name:str="Material")->bpy.types.Object:

    assert info.datablock_type == "MESH"
    if primitive_shape == "cube":
        bpy.ops.mesh.primitive_cube_add(
            enter_editmode=False,
            location=info.location,
            rotation=info.rotation,
            layers=info.layers)
    elif primitive_shape == "cylinder":
        bpy.ops.mesh.primitive_cylinder_add(
            enter_editmode=False,
            location=info.location,
            rotation=info.rotation,
            layers=info.layers)

    ob = bpy.context.object
    ob.name = info.name if info.name is not None else ob.name
    if info.parent_info:
        set_parent(ob,info.parent_info)
    set_material(ob,material_name)

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.uv.smart_project()
    bpy.ops.object.mode_set(mode='OBJECT')

    return ob

def create_image_from_disk(filename:str,#Must end in .png
        filepath:str="//tex/{}")->Optional[bpy.types.Image]:
    assert os.path.splitext(filename)[1] == ".png"
    # Load image file. Change here if the snippet folder is
    # not located in you home directory.
    realpath = bpy.path.abspath(filepath.format(filename))
    try:
        img = bpy.data.images.load(realpath)
        img.filepath = bpy.path.relpath(realpath)
        return img
    except:
        raise NameError("Cannot load image %s" % realpath)
        return None

def create_texture(name:str,
                    tex_type:str)->bpy.types.ImageTexture:
    if not get_texture(name):
        if tex_type == "tex":
            tex = bpy.data.textures.new(name, type='IMAGE')
            tex.image = create_image_from_disk(name + ".png")
    else:
        return get_texture(name)

def create_textures(material_name:str,
                    name:str,
                    image_name:List[str], #Will be paired with xp2b_tex_types
                    xp2b_tex_types:List[str]=["tex"])->List[bpy.types.ImageTexture]: #must be "tex", "lit", "normal", or "specular"

    if isinstance(material_name,str):
        material = get_material(material_name)

    #mat = get_material
    for tex_type in xp2b_tex_types:
        if tex_type == "tex":
    ##Albedo texture
            mat_tex_slot = material.texture_slots.add()
            mat_tex_slot.texture = create_texture(name,tex_type)
            mat_tex_slot.texture_coords = "UV"

    ##NML texture
    #mat_tex_slot = mat.texture_slots.add()
    #mat_tex_slot.texture = get_texture()
    #mat_tex_slot.texture_coords = "UV"
    #mat_tex_slot.use_map_color_diffuse = False
    #mat_tex_slot.use_map_normal = True
    #return

def create_material(material_name:str)->bpy.types.Material:
    try:
        return bpy.data.materials[material_name]
    except:
        return bpy.data.materials.new(material_name)


def create_material_default()->bpy.types.Material:
    '''
    Creates the default 'Material' if it doesn't already exist
    '''
    return create_material('Material')

#Do not include .png. It is only for the source path
def get_image(name:str)->Optional[bpy.types.Image]:
    '''
    New images will be created in //tex and will be a .png
    '''
    return bpy.data.images.get(name)

#Returns the bpy.types.Material or creates it as needed
def get_material(material_name:str)->Optional[bpy.types.Material]:
    return bpy.data.materials.get(material_name)

def get_material_default()->bpy.types.Material:
    mat = bpy.data.materials.get("Material")
    if mat:
        return mat
    else:
        return create_material_default()

def get_texture(name:str)->Optional[bpy.types.ImageTexture]:
    return bpy.data.textures.get(name)

def delete_all_images():
    for image in bpy.data.images:
        image.user_clear()
        bpy.data.images.remove(image,do_unlink=True)


def delete_all_materials():
    for material in bpy.data.materials:
        material.user_clear()
        bpy.data.materials.remove(material,do_unlink=True)


def delete_all_objects():
    for obj in bpy.data.objects:
        obj.user_clear()
        bpy.data.objects.remove(obj,do_unlink=True)


def delete_all_other_scenes():
    '''
    Note: We can't actually delete all the scenes since there has to be one
    '''
    for scene in bpy.data.scenes[1:]:
        scene.user_clear()
        bpy.data.scenes.remove(scene,do_unlink=True)


def delete_all_text_files():
    for text in bpy.data.texts:
        text.user_clear()
        bpy.data.texts.remove(text, do_unlink=True)


def delete_all_textures():
    for texture in bpy.data.textures:
        texture.user_clear()
        bpy.data.textures.remove(texture,do_unlink=True)

def delete_datablock(datablock: Any, do_unlink=True)->None:
    '''
    Uses type information to smartly remove datablock from its relavent data catagory
    '''
    if isinstance(datablock, bpy.types.Object):
        bpy.data.objects.remove(datablock, do_unlink)
    else:
        assert False, "Not implemented yet"


def delete_everything():
    delete_all_images()
    delete_all_materials()
    delete_all_objects()
    delete_all_text_files()
    delete_all_textures()
    delete_all_other_scenes()


def set_animation_data(blender_struct: Union[Object,Bone,PoseBone],
        keyframe_infos: List[KeyframeInfo],
        parent_armature: [Armature]=None,
        dataref_per_keyframe_info: bool=False)->None:
    '''
    - blender_struct - A Blender lamp, mesh, armature, or bone to attach keyframes to.
    For a bone set_animation_data will automatically use the correct Bone or PoseBone form.
    - keyframe_infos - A list of keyframe info which will be used to apply keyframes
    - parent_armature - If the blender_struct is a Bone or PoseBone, the parent armature of it is required
    (because Bones do not keep track of who their parent armature is for some reason -Ted, 3/21/2018)
    - dataref_per_keyframe_info - When true a dataref is created for every keyframe info passed in,
    even if there is an existing dataref with that same path already in the blender_struct
    (recommended for Show/Hide)

    keyframe_infos must be all the same dataref and all the same animation type. This was a deliberate choice
    to help catch errors in bad data
    '''

    # Ensure each call to set_animation_data has the same dataref_path and anim_type
    # for each KeyframeInfo
    assert len({kf_info.dataref_path for kf_info in keyframe_infos}) == 1
    assert len({kf_info.dataref_anim_type for kf_info in keyframe_infos}) == 1

    struct_is_bone = False
    if isinstance(blender_struct, (bpy.types.Bone, bpy.types.PoseBone)):
        assert parent_armature is not None
        try:
            blender_bone = parent_armature.data.bones[blender_struct.name]
            blender_pose_bone = parent_armature.pose.bones[blender_struct.name]
            blender_struct = blender_pose_bone
            struct_is_bone = True
        except KeyError:
            assert False, "{} is not a pose bone in parent_armature {}".format(blender_struct.name, parent_armature.name)

    if struct_is_bone:
        datarefs = blender_bone.xplane.datarefs
        bpy.context.scene.objects.active = parent_armature
        bpy.context.scene.objects.active.data.bones.active = blender_bone

        if not parent_armature.animation_data: #"Be explict in your intetions"
            parent_armature.animation_data_create()

        if not parent_armature.animation_data.action:
            #name+Action is the same scheme Blender uses by default
            #We know we won't have a collision because the object name already corrects itself
            parent_armature.animation_data.action = bpy.data.actions.new(name=blender_struct.name+"Action")
    else:
        datarefs = blender_struct.xplane.datarefs
        bpy.context.scene.objects.active = blender_struct

        if not blender_struct.animation_data:
            # This can actually be run over and over without overwriting,
            # explict is better than implict
            blender_struct.animation_data_create()

        if not blender_struct.animation_data.action:
            blender_struct.animation_data.action = bpy.data.actions.new(name=blender_struct.name+"Action")

    for kf_info in keyframe_infos:
        if (not keyframe_infos[0].dataref_path in [dref.path for dref in datarefs]
            or dataref_per_keyframe_info):
            dataref_prop = datarefs.add()
            dataref_prop.path = keyframe_infos[0].dataref_path
            dataref_prop.anim_type = keyframe_infos[0].dataref_anim_type
            dataref_index = len(datarefs)-1
        else:
            dataref_index, dataref_prop = [(index, dref)
                                           for index, dref in enumerate(datarefs)
                                           if dref.path == keyframe_infos[0].dataref_path][0]

        try:
            bpy.context.scene.frame_current = kf_info.frame_number
            dataref_prop.value = kf_info.dataref_value
        except AttributeError:
            pass
        try:
            dataref_prop.loop = kf_info.dataref_loop
        except AttributeError:
            pass

        if kf_info.dataref_anim_type == ANIM_TYPE_SHOW or kf_info.dataref_anim_type == ANIM_TYPE_HIDE:
            # They'd better have show_hide_v1/2! Otherwise, someone forgot an assert!
            dataref_prop.show_hide_v1 = kf_info.dataref_show_hide_v1
            dataref_prop.show_hide_v2 = kf_info.dataref_show_hide_v2

        if kf_info.location:
            blender_struct.location = kf_info.location
            blender_struct.keyframe_insert(data_path="location", group=blender_struct.name if struct_is_bone else "Location")
        if kf_info.rotation:
            blender_struct.rotation_mode = kf_info.rotation_mode
            data_path = 'rotation_{}'.format(kf_info.rotation_mode.lower())

            if kf_info.rotation_mode == "AXIS_ANGLE":
                blender_struct.rotation_axis_angle = (kf_info.rotation[0], *kf_info.rotation[1])
            elif kf_info.rotation_mode == "QUATERNION":
                blender_struct.rotation_quaternion = kf_info.rotation[:]
            else:
                data_path = 'rotation_euler'
                blender_struct.rotation_euler = [math.radians(r) for r in kf_info.rotation[:]]
            blender_struct.keyframe_insert(data_path=data_path,
                                           group=blender_bone.name if struct_is_bone else "Rotation")

        if struct_is_bone:
            bpy.ops.bone.add_xplane_dataref_keyframe(index=dataref_index)
        else:
            bpy.ops.object.add_xplane_dataref_keyframe(index=dataref_index)

#def set_blender_animation_data(blender_struct: Union[bpy.types.Object,bpy.types.Bone,bpy.types.PoseBone],
        #keyframe_infos: List[KeyframeInfo],
        #parent_armature: [bpy.types.Armature]=None)->None:
    #'''
    #Just for blender animation, doesn't set any xplane keyframes
    #'''
    #pass

#def set_layer_visibility(layer_visibility_settings:Iterable[Tuple[int,bool]]):
    #assert len(layer_visibility_settings) == 0
    #assert any([setting[1] for setting in layer_visibility_settings])
#
    #for idx in layers:
        #bpy.context.scene.layers[idx] = visible

def set_manipulator_settings(object_datablock:bpy.types.Object,
        manip_type:str,
        manip_enabled:bool=True,
        manip_props:Optional[Dict[str,Any]]=None):
    '''
    manip_type and manip_enabled, since they're the most common.
    if manip_props is left none, defaults for Cursor and Tooltip will be filled in
    using the object's name
    '''
    assert object_datablock.type == "MESH"
    if manip_props is None:
        manip_props = {}

    object_datablock.xplane.manip.type = manip_type
    object_datablock.xplane.manip.enabled = manip_enabled
    if manip_enabled is False:
        return

    if 'cursor' not in manip_props:
        manip_props['cursor'] = 'hand'
    if 'tooltip' not in manip_props:
        manip_props['tooltip'] = '{} type manipulator on {}'.format(
                manip_type,
                object_datablock.name)

    for prop_name,value in manip_props.items():
        attr = getattr(object_datablock.xplane.manip,prop_name,None)
        assert attr is not None, "{} is not a real manip property!".format(prop_name)

        if prop_name == "axis_detent_ranges":
            for item in value:
                new_axis_detent_range = attr.add()
                new_axis_detent_range.start = item.start
                new_axis_detent_range.end   = item.end
                new_axis_detent_range.height = item.height
        else:
            setattr(object_datablock.xplane.manip,prop_name,value)

def set_material(blender_object:bpy.types.Object,
                 material_name:str="Material",
                 material_props:Optional[Dict[str,Any]]=None,
                 create_missing:bool=True):

    if len(blender_object.material_slots) == 0:
        bpy.ops.object.mode_set(mode='OBJECT')
        blender_object.data.materials.append(None)
    mat = create_material(material_name)
    blender_object.material_slots[0].material = mat

    if material_props:
        for prop,value in material_props.items():
            setattr(mat.xplane.manip,prop,value)

def set_parent(blender_object:bpy.types.Object,parent_info:ParentInfo)->None:
    assert isinstance(blender_object,bpy.types.Object)

    blender_object.parent = parent_info.parent
    blender_object.parent_type = parent_info.parent_type

    if parent_info.parent_type == _BONE:
        assert parent_info.parent.type == _ARMATURE and\
               parent_info.parent.data.bones.get(parent_info.parent_bone) is not None

        blender_object.parent_bone = parent_info.parent_bone

def set_xplane_layer(layer:Union[int,io_xplane2blender.xplane_props.XPlaneLayer],layer_props:Dict[str,Any]):
    assert isinstance(layer,int) or isinstance(layer, io_xplane2blender.xplane_props.XPlaneLayer)

    if isinstance(layer,int):
       layer = bpy.context.scene.xplane.layers[layer]

    for prop,value in layer_props.items():
        setattr(layer,prop,value)

def create_initial_test_setup():
    bpy.ops.wm.read_homefile()
    delete_everything()
    bpy.context.scene.layers[0] = True
    for i in range(1,20):
        bpy.context.scene.layers[i] = False

    bpy.ops.scene.add_xplane_layers()
    create_material_default()

    # Create text file
    header_str = "Unit Test Overview"
    if bpy.data.texts.find(header_str) == -1:
        unit_test_overview = bpy.data.texts.new(header_str)
    else:
        unit_test_overview = bpy.data.texts[header_str]

    unit_test_overview.write(header_str + '\n\n')

    #bpy.ops.console.insert(text="bpy.ops.export.xplane_obj()")
