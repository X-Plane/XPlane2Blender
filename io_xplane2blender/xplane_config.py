# File: xplane_config.py
# Holds config variables that are used throughout the addon.

from . import bl_info
from .xplane_helpers import XPlane2BlenderVersion
# Variable: debug
# Set to True for debugging output using <debugger>. Default is True, as we are still dealing with a development release.
debug = False

# Variable: log
# Set to True, to log debug output in a file.
log = False

# Constant: CURRENT_BUILD_TYPE
#
# The current build type, must be a member of XPlane2BlenderVersion.BUILD_TYPES 
CURRENT_BUILD_TYPE = XPlane2BlenderVersion.BUILD_TYPES_BETA 

# Constant: CURRENT_BUILD_TYPE_VERSION
#
# The current build type version, must be 0 for RELEASE, > 0 for all others 
CURRENT_BUILD_TYPE_VERSION = 4

# Variable: version
# An <XPlane2Blender> containing the current version of the addon.
XPLANE2BLENDER_VER = XPlane2BlenderVersion(tuple([int(v) for v in bl_info["version"]]),CURRENT_BUILD_TYPE,CURRENT_BUILD_TYPE_VERSION)

def initConfig():
    global debug
    global log
    import bpy

    if hasattr(bpy.context.scene, "xplane") and bpy.context.scene.xplane.debug:
        debug = True

        if bpy.context.scene.xplane.log:
            log = True
        else:
            log = False
    else:
        debug = False
        log = False

def getDebug():
    global debug
    return debug

def getLog():
    global log
    return log

def setDebug(d):
    global debug
    debug = d
