# File: xplane_updater.py
# Automagically updates blend data created with older XPlane2Blender Versions

import bpy
from .xplane_config import *
from .xplane_constants import *
from bpy.app.handlers import persistent
import io_xplane2blender
import io_xplane2blender.xplane_props

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

    for d in object.xplane.datarefs:
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
    if fromVersion < '3.3.0':
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

    if fromVersion < '3.4.0':
        for arm in bpy.data.armatures:
            for bone in arm.bones:
                #Thanks to Python's duck typing and Blender's PointerProperties, this works
                __updateLocRot(bone)

        for object in bpy.data.objects:
            __updateLocRot(object)

@persistent
def load_handler(dummy):
    currentVersion = '.'.join(map(str,version))
    filepath = bpy.context.blend_data.filepath

    # do not update newly created files
    if not filepath:
        return

    fileVersion = bpy.data.scenes[0].get('xplane2blender_version','3.2.0')
    if fileVersion < currentVersion:
        #If it is a missing string we'll just call it '3.3.0' for some reason. I really don't get it.
        #-Ted 08/02/2017
        if len(fileVersion) == 0:
            fileVersion = '3.2.0'

        print('This file was created with an older XPlane2Blender version less than or equal to (%s) and will now automatically be updated to %s' % (fileVersion,currentVersion))

        update(fileVersion)

        bpy.data.scenes[0]['xplane2blender_version'] = currentVersion
        print('Your file was successfully updated to XPlane2Blender %s' % currentVersion)

bpy.app.handlers.load_post.append(load_handler)

@persistent
def save_handler(dummy):
    pass

bpy.app.handlers.save_pre.append(save_handler)
