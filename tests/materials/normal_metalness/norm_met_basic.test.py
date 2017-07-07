import bpy
import os

C = bpy.context
D = bpy.data

#THE RULES:
#There is a LOT of hardcoded naming in this
#You must have the image names match a pattern
#You must have the images in the folder //tex

material_format_str = "Material_norm_met_%s%s"

#v10_cessna,v10_
texture_albedo_str = "v10_cessna"
texture_draped_str = "v10_cessna_wing_draped"

object_format_str = "D_%s_NON_D_%s"
test_types = ['none','non_metal','metal']
    
#Do not include .png. It is only for the source path
def get_image(name):
    if D.images.get(name) != None:
        return D.textures.get(name)
    else:
        # Load image file. Change here if the snippet folder is 
        # not located in you home directory.
        realpath = bpy.path.abspath("//tex/%s.png" % (name))
        try:
            img = bpy.data.images.load(realpath)
            img.filepath = bpy.path.relpath(realpath)
        except:
            raise NameError("Cannot load image %s" % realpath)
                    
def create_images():
    get_image("v10_cessna")
    get_image("v10_cessna_NML")
    get_image("v10_cessna_wing_draped")
    get_image("v10_cessna_wing_draped_NML")

def get_texture_name(is_draped,is_normal):
    tex_str = ""
    if is_draped:
        tex_str = texture_draped_str
    else:
        tex_str = texture_albedo_str
       
    if is_normal:
        tex_str += "_NML"

    return tex_str

#returns bpy.types.ImageTexture
def get_texture(is_draped,is_normal):
    tex_name = get_texture_name(is_draped,is_normal)
    if D.textures.get(tex_name) != None:
        return D.textures.get(tex_name)
    else:
        tex = D.textures.new(tex_name, type='IMAGE')
        tex.image = D.images[tex_name+".png"]
        
        
def create_textures():
    #Create them all
    get_texture(True,True)
    get_texture(True,False)
    get_texture(False,True)
    get_texture(False,False)

def get_material_name(is_metal,is_draped):
    return material_format_str % (["on","off"][not is_metal],["_drap",""][not is_draped])

#Returns the bpy.types.Material or creates it as needed
def get_material(is_metal,is_draped):
    mat_name = get_material_name(is_metal,is_draped)
    if D.materials.get(mat_name) != None:
        return D.materials.get(mat_name)
    else:
        mat = bpy.data.materials.new(get_material_name(is_metal,is_draped))
        
        #Albedo texture
        mat_tex_slot = mat.texture_slots.add()
        mat_tex_slot.texture = get_texture(is_draped, False)
        mat_tex_slot.texture_coords = "UV"
        
        #NML texture
        mat_tex_slot = mat.texture_slots.add()
        mat_tex_slot.texture = get_texture(is_draped, True)
        mat_tex_slot.texture_coords = "UV"
        mat_tex_slot.use_map_color_diffuse = False
        mat_tex_slot.use_map_normal = True
        
        mat.specular_intensity = 0.25
        
        if is_metal:
            mat.xplane.normal_metalness = True

        if is_draped:
            mat.xplane.draped = True

        return mat

def create_materials():  
    #Create them all
    get_material(True,True)
    get_material(True,False)
    get_material(False,True)
    get_material(False,False)

def create_object_names():
    object_names = []
    for test_type_draped in test_types:
        for test_type_non_draped in test_types:
            object_names.append(object_format_str % (test_type_draped,test_type_non_draped))
            print(object_names[-1])

    object_names.reverse()
    
    return object_names

def delete_scene_data():
    for object in D.objects:
        if not "D_none_NON_D_none" in object.name:
            object.select = True
    bpy.ops.object.delete()

    for material in D.materials:
        material.user_clear()
        D.materials.remove(material)

    for texture in D.textures:
        texture.user_clear()
        D.textures.remove(texture)
    
    for image in D.images:
        image.user_clear()
        D.images.remove(image)
        
#This will create the objects, layers, and materials. You will still have to set up the materials and textures for the blend file
#You will need to also create the no draped and no non-draped objects by making an empty with a light in it.
def create_partial_test_setup():

    #Reset the scene, delete the objects
    C.scene.layers = [False] * 20
    C.scene.layers[:9] = [True] * 9
    
    delete_scene_data()
    create_images()
    create_textures()
    create_materials()
    create_object_names()

    #create the test names, which are the basis naming scheme for everything
    object_names = create_object_names()

    layer_idx = 0  
    for name in object_names:
        layers_array = [False] * 20
        layers_array[layer_idx] = True
    
        bpy.ops.object.empty_add(type='PLAIN_AXES',layers=layers_array,location=(0,0,0))
        empty_parent = C.object
        C.object.name = name
    
        needs_draped     = name.find("D_none") != 0
        needs_non_draped = not "NON_D_none" in name
        
        #Material_norm_met_off
        #Material_norm_met_off_drap
        #Material_norm_met_on
        #Material_norm_met_on_drap
        material_str = "Material_norm_met_%s%s"
        if needs_draped:
            bpy.ops.mesh.primitive_plane_add(layers=layers_array,location=(0,0,0))
            C.object.name = name + "_D"
            C.object.parent = empty_parent
            C.object.scale = (2,2,2)
            
            is_metal = name.find("D_metal") == 0
            C.object.data.materials.append(get_material(is_metal,is_draped=True))
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.uv.smart_project()
            bpy.ops.object.mode_set(mode='OBJECT')
                                    
        if needs_non_draped:
            bpy.ops.mesh.primitive_cube_add(layers=layers_array,location=(0,0,1))
            C.object.name = name + "_ND"
            C.object.parent = empty_parent
            

            is_metal = "NON_D_metal" in name
            C.object.data.materials.append(get_material(is_metal,is_draped=False))
            
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.uv.smart_project()
            bpy.ops.object.mode_set(mode='OBJECT')
                    
        layer_idx += 1            

create_partial_test_setup()
