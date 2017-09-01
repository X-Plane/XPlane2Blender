# File: xplane_updater.py
# Automagically updates blend data created with older XPlane2Blender Versions

import bpy
from .xplane_config import *
from .xplane_constants import *
from bpy.app.handlers import persistent
import io_xplane2blender
import io_xplane2blender.xplane_props

'''
 #####     ##   ##  ##   ####  ####  ####  #    ### ##  ####  ####  ####    ####  ####    #####   ####    ##    ####   ###   ##  ##   ###  # 
  #   #   # #    #  #   ##  #  ## #  #  #  #     #  #   ## #  #  #  ## #    #  #  ## #     #   #  #  #   # #   ##  #  #   #   #  #   #  #  # 
 ##   #   # #   # # #  ##      ###   ###   #    #####   ###   ###   ###     ###   ###     ##   #  ###    # #  ##     ##   #  # # #   ##    # 
 ##   #  ####   # # #  #  ###  #     # #   #    #  ##   #     # #   #       # #   #       ##   #  # #   ####  #  ### #    #  # # #    ##   # 
 #   #   #  #   #  ##  ##  #   # #   # #        #  #    # #   # #   # #     # ##  # #     #   #   # #   #  #  ##  #  #   #   #  ##  #  #     
#####   ##  ## ##  #    ####  ####  ## ## #    ## ###  ####  ## ## ####    ####  ####    #####   ## ## ##  ##  ####   ###   ##  #   ####  #  

BEFORE CHANGING THIS FILE have you:
1. Fully understood what parts of the data model you are changing?
2. Written a spec and documented it?
3. Reviewed existing unit tests for correctness?
4. Created unit tests __before__ you start?
5. Quadruple checked every character, even the ones you didn't write?
6. Tested it with all versions of Blender people could be using?
7. Cross tested loading and unloading between different versions of XPlane2Blender?
8. Immediately went into a beta cycle?

Put this in your mind:
    A poor defenseless .blend file, with big watery wobbly eyes is lying on the operating table, eyeing the sharp text editors and esoteric command line commands
    about to be used on the codebase that supports it. It says
            
            Will it hurt to change the update function? Is it necessary?
            Is it deterministic and fulfills the "Only update what's needed, when needed" contract?
            Do you remember the 3.4.0 loc/rot/locrot fiasco of Aug. 2017?
    
    You hold the anesthesia mask in one hand, and a terminal prompt in the other. Are you ready to take responsibility for this data model and
    the artists who depend on it? Are you ready to make a change to this file? Or are you another wanna-be console cowboy who is poking their mouse
    in the wrong part of the codebase again?
    ...
    ...
    ...
    
You may now proceed to the rest of the file.
'''

def __updateLocRot(object):
    
    #In int
    #Out string enum
    def convert_old_to_new(old_anim_type):
        #Recreate the pre_34 animation types enum
        ANIM_TYPE_TRANSLATE = "translate"
        ANIM_TYPE_ROTATE = "rotate"
        
        conversion_table = [
                #pre_34_anim_types  : post_34_anim_types
                (ANIM_TYPE_TRANSFORM, ANIM_TYPE_TRANSFORM),
                (ANIM_TYPE_TRANSLATE, ANIM_TYPE_TRANSFORM),
                (ANIM_TYPE_ROTATE,    ANIM_TYPE_TRANSFORM),
                (ANIM_TYPE_SHOW,      ANIM_TYPE_SHOW),
                (ANIM_TYPE_HIDE,      ANIM_TYPE_HIDE)
            ]

        if old_anim_type >= 0 and old_anim_type < len(conversion_table):
            return conversion_table[old_anim_type][1]
        else:
            raise Exception("%s was not found in conversion table" % old_anim_type)

    for d in obj.xplane.datarefs:
        old_anim_type = d.get('anim_type')
        if old_anim_type is None:
           old_anim_type = 0 #something about Blender properties requires this
        
        d.anim_type = convert_old_to_new(old_anim_type)

# Function: update
# Updates parts of the data model to ensure forward
# compatability between versions of XPlane2Blender.
# 
# Important: Running the updater on an already updated file
# should result in no changes to it
#
# Parameters:
#     fromVersion - The old version of the blender file
def update(fromVersion):
    if fromVersion < XPlane2BlenderVersion.parseVersion('3.3.0'):
        for scene in bpy.data.scenes:
            # set compositeTextures to False
            scene.xplane.compositeTextures = False

            if scene.xplane and scene.xplane.layers and len(scene.xplane.layers) > 0:
                for layer in scene.xplane.layers:
                    # set autodetectTextures to False
                    layer.autodetectTextures = False

                    # set export mode to cockpit, if cockpit was previously enabled
                    # TODO: Have users actually exported scenery objects before?
                    # Do we need to care about non-aircraft export types?
                    if layer.cockpit:
                        layer.export_type = 'cockpit'
                    else:
                        layer.export_type = 'aircraft'

    if fromVersion < XPlane2BlenderVersion.parseVersion('3.4.0'):
        for arm in bpy.data.armatures:
            for bone in arm.bones:
                #Thanks to Python's duck typing and Blender's PointerProperties, this works
                __updateLocRot(bone)

        for obj in bpy.data.objects:
            __updateLocRot(obj)

@persistent
def load_handler(dummy):
    filepath = bpy.context.blend_data.filepath

    # do not update newly created files
    if not filepath:
        return

    # Before we do anything to the blend file,
    # save what version of the code we're doing it
    bpy.data.scenes[0]['xplane2blender_build_number'] = XPLANE2BLENDER_VER.getBuildNumberStr()

    # "3.2.0 was the last version without an updater, so default to that."
    # Best guess as to this decision -Ted 08/02/2017
    fileVersion = XPlane2BlenderVersion.parseVersion(bpy.data.scenes[0].get('xplane2blender_version','3.2.0'))
    if fileVersion < XPLANE2BLENDER_VER:
        print('This file was created with an older XPlane2Blender version less than or equal to (%s) and will now automatically be updated to %s' % (fileVersion,XPLANE2BLENDER_VER.fullVersionStr()))
        update(fileVersion)
        bpy.data.scenes[0]['xplane2blender_version'] = str(XPLANE2BLENDER_VER)
        print('Your file was successfully updated to XPlane2Blender %s' % XPLANE2BLENDER_VER.fullVersionStr())

bpy.app.handlers.load_post.append(load_handler)

@persistent
def save_handler(dummy):
    pass

bpy.app.handlers.save_pre.append(save_handler)
