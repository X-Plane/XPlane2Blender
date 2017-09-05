# File: xplane_config.py
# Holds config variables that are used throughout the addon.

from . import bl_info
from .xplane_props import XPlane2BlenderVersion
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
# The current build type version, must be > 0
CURRENT_BUILD_TYPE_VERSION = 4

# Constant: CURRENT_DATA_MODEL_VERSION
#
# The current data model version, incrementing every time xplane_constants, xplane_props, or xplane_updater
# 3.3.9 and earlier have a version of 0 
CURRENT_DATA_MODEL_VERSION = 0

# Constant: CURRENT_BUILD_NUMBER
#
# The build number, hardcoded by the build script when there is one, other wise it is left "" for "NONE"
CURRENT_BUILD_NUMBER = ""

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
