import math
import typing
from typing import *

import bpy

from io_xplane2blender.xplane_props import XPlaneManipulatorSettings
from io_xplane2blender.xplane_helpers import logger, XPlaneLogger
from mathutils import Vector, Euler, Quaternion
'''
test_creation_tools

These allow the quick automated setup of test cases

- enable_ Enable a setting
- disable_ Disable a setting or feature

- get_ get's a Blender datablock or piece of data
- set_
- create_ creates a Blender datablock
- delete_ and delete_all

API decisions:
    - Does get_ also have the power to create?

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

# Rotations are in angles, and get transformed when they need to.

# Constants
_ARMATURE = "ARMATURE"
_BONE     = "BONE"
_OBJECT   = "OBJECT"

class DatablockInfo():
    def __init__(self,
            datablock_type:str,
            name:Optional[str]=None,
            layers:Tuple[int]=tuple([True] + [False] * 19),
            location:Vector=Vector((0,0,0)),
            rotation_mode:str="XYZ",
            rotation:Optional[Union[bpy.types.bpy_prop_array,Euler,Quaternion]]=None,
            scale:Vector=Vector((1,1,1))):
        '''
        datablock_type: Must be 'MESH', 'ARMATURE', 'EMPTY', or 'LAMP' 
        default for layers will be layer 1
        '''
        self.datablock_type = datablock_type
        self.name = name
        self.layers = layers
        self.location = location
        self.rotation_mode = rotation_mode
        if rotation is None:
            if set(self.rotation_mode) == {'X','Y','Z'}:
                self.rotation = Vector()
            elif self.rotation_mode == "AXIS_ANGLE":
                self.rotation = [0,0,0,0]
        self.scale = scale

class KeyframeInfo():
    def __init__(self,
            idx:int,
            dataref_path:str,
            dataref_value:float,
            dataref_anim_type:str="transform",
            location:Optional[Vector]=None,
            rotation_mode:str="XYZ",
            rotation:Optional[Tuple[Union[bpy.types.bpy_prop_array,Euler,Quaternion]]]=None):
        self.idx           = idx
        self.dataref_path  = dataref_path
        self.dataref_value = dataref_value
        self.dataref_anim_type = dataref_anim_type
        self.location      = location
        self.rotation_mode = rotation_mode
        self.rotation = rotation

        if {self.rotation_mode} == {'X','Y','Z'}:
            assert len(self.rotation) == 3
        else:
            assert len(self.rotation) == 4

def create_animation_data(blender_object:bpy.types.Object,
        keyframe_infos:List[KeyframeInfo])->None:
    '''
    - blender_object - A Blender lamp, mesh, armature, or bone to attach keyframes to
    - keyframe_infos - A list of keyframe info which will be used to apply keyframes
    '''
    assert len({kf_info.dataref_path for kf_info in keyframe_infos}) == 1
    assert len({kf_info.dataref_anim_type for kf_info in keyframe_infos}) == 1

    if not keyframe_infos[0].dataref_path in [dref.path for dref in blender_object.xplane.datarefs]:
        dataref_prop = blender_object.xplane.datarefs.add()
        dataref_prop.path = keyframe_infos[0].dataref_path
        dataref_prop.anim_type = keyframe_infos[0].dataref_anim_type
    else:
        dataref_prop = next(filter(lambda dref: dref.path == kf_info.dataref_path, blender_object.xplane.datarefs))

    for kf_info in keyframe_infos:
        bpy.context.scene.frame_current = kf_info.idx
        dataref_prop.value = kf_info.dataref_value

        if blender_object.type == 'BONE':
            #TODO: Must ensure bone is set to         bpy.ops.object.mode_set(mode='POSE')

            bpy.ops.bone.add_xplane_dataref_keyframe(index=blender_object.xplane.datarefs.index(dataref_prop))
        else:
            bpy.ops.object.add_xplane_dataref_keyframe(index=blender_object.xplane.datarefs.index(dataref_prop))
        if kf_info.location:
            blender_object.location = kf_info.location
            bpy.ops.anim.keyframe_insert_menu(type='Location')
        if kf_info.rotation:
            blender_object.rotation_mode = kf_info.rotation_mode
            if kf_info.rotation_mode == "AXIS_ANGLE":
                blender_object.rotation_axis_angle = kf_info.rotation[:]
            elif kf_info.rotation_mode == "QUATERNION":
                blender_object.rotation_quaternion = kf_info.rotation[:]
            else:
                blender_object.rotation_euler = [math.radians(r) for r in kf_info.rotation[:]]
                bpy.ops.anim.keyframe_insert_menu(type='Rotation')

def create_datablock_armature(info:DatablockInfo)->bpy.types.Object:
    assert info.datablock_type == "ARMATURE"
    bpy.ops.object.armature_add(
        enter_editmode=False,
        location=info.location,
        rotation=info.rotation,
        layers=info.layers)
    ob = bpy.context.object
    bpy.ops.object.mode_set(mode='POSE')

    ob = bpy.context.object
    ob.name = info.name if info.name is not None else ob.name
    ob.rotation_mode = info.rotation_mode
    ob.scale = info.scale
    
    return ob

def create_datablock_empty(info:DatablockInfo)->bpy.types.Object:
    assert info.datablock_type == "EMPTY"
    bpy.ops.object.empty_add(
        type='PLAIN_AXES',
        location=info.location,
        rotation=info.rotation,
        layers=info.layers
        )
    ob = bpy.context.object
    ob.name = info.name if info.name is not None else ob.name
    ob.rotation_mode = info.rotation_mode
    ob.scale = info.scale
    
    return ob

def create_datablock_mesh(info:DatablockInfo,
                primitive_shape="cube", #Must be "cube" or "cylinder" 
                parent:Optional[bpy.types.Object]=None,
                parent_type:str=_OBJECT, #Must be "ARMATURE", "BONE", or "OBJECT"
                parent_bone:Optional[str]=None,
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
    set_parent(ob,parent,parent_type,parent_bone)
    set_material(ob,material_name)

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.uv.smart_project()
    bpy.ops.object.mode_set(mode='OBJECT')

#Do not include .png. It is only for the source path
def get_image(name:str,
              create_missing:bool=True):
    '''
    New images will be created in //tex and will be a .png
    '''
    assert isinstance(name,str)
    if bpy.data.images.get(name) != None:
        return bpy.data.textures.get(name)
    else:
        # Load image file. Change here if the snippet folder is 
        # not located in you home directory.
        realpath = bpy.path.abspath("//tex/%s.png" % (name))
        try:
            img = bpy.data.images.load(realpath)
            img.filepath = bpy.path.relpath(realpath)
        except:
            raise NameError("Cannot load image %s" % realpath)
                    
#def get_texture(name:str,
        #create_missing:bool=True)->bpy.types.ImageTexture:
    #tex_name = name
    #if bpy.data.textures.get(tex_name) != None:
        #return bpy.data.textures.get(tex_name)
    #else:
        #tex = bpy.data.textures.new(tex_name, type='IMAGE')
        #tex.image = bpy.data.images[tex_name+".png"]
        #
        #
#def create_textures(material:Union[bpy.types.Material,str],
        #name:str):
    #mat = get_material
    ##Albedo texture
    #mat_tex_slot = mat.texture_slots.add()
    #mat_tex_slot.texture = get_texture()
    #mat_tex_slot.texture_coords = "UV"
    #
    ##NML texture
    #mat_tex_slot = mat.texture_slots.add()
    #mat_tex_slot.texture = get_texture()
    #mat_tex_slot.texture_coords = "UV"
    #mat_tex_slot.use_map_color_diffuse = False
    #mat_tex_slot.use_map_normal = True
    #return

def create_material(material_name:str):
    try:
        return bpy.data.materials[material_name]
    except:
        return bpy.data.materials.new(material_name)

def create_material_default()->bpy.types.Material:
    '''
    Creates the default 'Material' if it doesn't already exist
    '''
    return create_material('Material')

#Returns the bpy.types.Material or creates it as needed
def get_material(material_name:str,
                 create_missing:bool=True)->bpy.types.Material:
    mat = bpy.data.materials.get(material_name)
    if mat:
        return mat
    elif create_missing:
        return create_material(material_name)
    else:
        return None

def get_material_default()->bpy.types.Material:
    mat = bpy.data.materials.get("Material")
    if mat:
        return mat
    else:
        return create_material_default()

def delete_all_images():
    for image in bpy.data.images:
        image.user_clear()
        bpy.data.images.remove(image,True)

def delete_all_materials():
    for material in bpy.data.materials:
        material.user_clear()
        bpy.data.materials.remove(material,True)

def delete_all_objects():
    for obj in bpy.data.objects:
        obj.user_clear()
        bpy.data.objects.remove(obj,True)

def delete_all_other_scenes():
    '''
    Note: We can't actually delete all the scenes since there has to be one
    '''
    for scene in bpy.data.scenes[1:]:
        scene.user_clear()
        bpy.data.scenes.remove(scene,True)

def delete_all_text_files():
    for text in bpy.data.texts:
        text.user_clear()
        bpy.data.texts.remove(text, do_unlink=True)
    
def delete_all_textures():
    for texture in bpy.data.textures:
        texture.user_clear()
        bpy.data.textures.remove(texture,True)

def delete_everything():
    delete_all_images()
    delete_all_materials()
    delete_all_objects()
    delete_all_text_files()
    delete_all_textures()
    delete_all_other_scenes()


def set_layer_visibility(layers:Iterable[int],visible:bool):
    assert len([idx for idx in layers if 0 <= idx >= 20]) == 0

    for idx in layers:
        bpy.context.scene.layers[idx] = visible

def set_manipulator_settings(object_datablock:bpy.types.Object,
        manip_type:str,
        manip_enabled:bool=True,
        manip_other_props:Optional[Dict[str,Any]]=None):
    '''
    manip_type and manip_enabled, since they're the most common.
    if manip_other_props is left none, defaults for Cursor and Tooltip will be filled in
    using the object's name
    '''
    assert object_datablock.type == "MESH"

    object_datablock.xplane.manip.enabled = manip_enabled
    if manip_enabled is False:
        return

    if manip_other_props is None:
        manip_other_props = {'cursor':'hand','tooltip':'{} type manipulator on {}'.format(
            manip_type,
            object_datablock.name)}

    for prop,value in manip_other_props:
        setattr(object_datablock.xplane.manip,prop,value)

def set_material(blender_object:bpy.types.Object,
                 material_name:str="Material",
                 material_props:Optional[Dict[str,Any]]=None,
                 create_missing:bool=True):
    
    if len(blender_object.material_slots) == 0:
        bpy.ops.object.mode_set(mode='OBJECT')
        blender_object.data.materials.append(None)
    mat = get_material(material_name,create_missing)

    if material_props:
        for prop,value in material_props.items():
            setattr(mat.xplane.manip,prop,value)

def set_parent(blender_object:bpy.types.Object,
        parent_object:bpy.types.Object,
        parent_type:str,
        parent_bone:Optional[Union[bpy.types.Bone,int,str]]=None)->None:
    assert parent_bone is not None
    assert parent_type == _ARMATURE or parent_type == _BONE or parent_type == _OBJECT
    assert isinstance(blender_object,bpy.types.Object)
    assert isinstance(parent_object.data,bpy.types.Object)
    assert isinstance(parent_bone,int) or isinstance(parent_bone,str) or isinstance(parent_bone,bpy.types.Bone)

    blender_object.parent = parent_object
    blender_object.parent_type = parent_type

    if parent_type == _BONE:
        assert parent_object.type is _ARMATURE and\
               parent_object.data.bones.get(parent_bone) is not None

        if isinstance(parent_bone,bpy.types.Bone):
            pass
        elif isinstance(parent_bone,int) or isinstance(parent_bone,str):
            parent_bone = parent_object.data.bones[parent_bone]
        else:
            raise NotImplemented
        blender_object.parent_bone = parent_bone

def create_initial_test_setup():
    bpy.ops.wm.read_homefile()
    delete_everything()
    bpy.context.scene.layers = [False] * 20
    create_material_default() 

    # Create text file
    header_str = "Unit Test Overview"
    if bpy.data.texts.find(header_str) == -1:
        unit_test_overview = bpy.data.texts.new(header_str)
    else:
        unit_test_overview = bpy.data.texts[header_str]
    
    unit_test_overview.write(header_str + '\n\n')

    #bpy.ops.console.insert(text="bpy.ops.export.xplane_obj()")
    
    
    #TODO: set debug and optimize to true
#This will create the objects, layers, and materials. You will still have to set up the materials and textures for the blend file
#You will need to also create the no draped and no non-draped objects by making an empty with a light in it.
#def create_partial_test_setup():
#
    ##Reset the scene, delete the objects
    #bpy.context.scene.layers = [False] * 20
    #bpy.context.scene.layers[:9] = [True] * 9
    #
    #delete_scene_data()
    #create_images()
    #create_textures()
    #create_materials()
    #create_object_names()
#
    ##create the test names, which are the basis naming scheme for everything
    #object_names = create_object_names()
#
    #layer_idx = 0  
    #for name in object_names:
        #layers_array = [False] * 20
        #layers_array[layer_idx] = True
    #
        #bpy.ops.object.empty_add(type='PLAIN_AXES',layers=layers_array,location=(0,0,0))
        #empty_parent = bpy.context.object
        #bpy.context.object.name = name
    #
        #needs_draped     = name.find("D_none") != 0
        #needs_non_draped = not "NON_D_none" in name
        #
        ##Material_norm_met_off
        ##Material_norm_met_off_drap
        ##Material_norm_met_on
        ##Material_norm_met_on_drap
        #material_str = "Material_norm_met_%s%s"
        #if needs_draped:
            #bpy.ops.mesh.primitive_plane_add(layers=layers_array,location=(0,0,0))
            #bpy.context.object.name = name + "_D"
            #bpy.context.object.parent = empty_parent
            #bpy.context.object.scale = (2,2,2)
            #
            #is_metal = name.find("D_metal") == 0
            #bpy.context.object.data.materials.append(get_material(is_metal,is_draped=True))
            #bpy.ops.object.mode_set(mode='EDIT')
            #bpy.ops.uv.smart_project()
            #bpy.ops.object.mode_set(mode='OBJECT')
                                    #
        #if needs_non_draped:
            #bpy.ops.mesh.primitive_cube_add(layers=layers_array,location=(0,0,1))
            #bpy.context.object.name = name + "_ND"
            #bpy.context.object.parent = empty_parent
            #
#
            #is_metal = "NON_D_metal" in name
            #bpy.context.object.data.materials.append(get_material(is_metal,is_draped=False))
            #
            #bpy.ops.object.mode_set(mode='EDIT')
            #bpy.ops.uv.smart_project()
            #bpy.ops.object.mode_set(mode='OBJECT')
                    #
        #layer_idx += 1            

#create_partial_test_setup()
#create_partial_test_setup()s
