# File: xplane_updater.py
# Automagically updates blend data created with older XPlane2Blender Versions

import bpy
from io_xplane2blender.xplane_config import *
from bpy.app.handlers import persistent

@persistent
def load_handler(dummy):
    currentVersion = '.'.join(map(str,version))
    fileVersion = bpy.data.worlds[0].xplane2blender_version

    if fileVersion < currentVersion:
        if len(fileVersion) == 0:
            fileVersion = '<3.3.0'

        print('This file was created with an older XPlane2Blender version (%s) and will now automaticly be updated' % fileVersion)

        # TODO: update blend data

        # store currentVersion
        bpy.data.worlds[0].xplane2blender_version = currentVersion
        print('Your file was successfully updated to XPlane2Blender %s' % currentVersion)

bpy.app.handlers.load_post.append(load_handler)
