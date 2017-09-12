# File: xplane_config.py
# Holds config variables that are used throughout the addon.

from io_xplane2blender import bl_info
from io_xplane2blender import xplane_constants
from .xplane_constants import BUILD_TYPE_ALPHA,BUILD_TYPE_BETA,BUILD_TYPE_DEV
from .xplane_constants import BUILD_TYPE_LEGACY,BUILD_TYPE_RC     


# Variable: debug
# Set to True for debugging output using <debugger>. Default is True, as we are still dealing with a development release.
# TODO: This is a duplicate for bpy.context.scene.xplane.debug, no matter what you set here it won't matter. In addition,
# at most of it's call sites, it is an unused variable. This really aught to be cleaned one day 
debug = False

# Variable: log
# Set to True, to log debug output in a file.
# TODO: This is a duplicate for bpy.context.scene.xplane.log, no matter what you set here it won't matter. In addition,
# at most of it's call sites, it is a barely used variable. This redundent global state variable really aught to be cleaned
log = False

# We make a copy here so as not to cause a circular dependency in xplane_props and other places
CURRENT_ADDON_VERSION = bl_info["version"]

# Constant: CURRENT_BUILD_TYPE
#
# The current build type, must be a member of XPlane2BlenderVersion.BUILD_TYPE 
CURRENT_BUILD_TYPE = xplane_constants.BUILD_TYPE_BETA

# Constant: CURRENT_BUILD_TYPE_VERSION
#
# The current build type version, must be > 0
CURRENT_BUILD_TYPE_VERSION = 4

# Constant: CURRENT_DATA_MODEL_VERSION
#
# The current data model version, incrementing every time xplane_constants, xplane_props, or xplane_updater
# changes. Builds earlier than 3.4.0-beta.5 have and a version of 0 
CURRENT_DATA_MODEL_VERSION = 1

# Constant: CURRENT_BUILD_NUMBER
#
# The build number, hardcoded by the build script when there is one, other wise it is left "" for "NONE"
CURRENT_BUILD_NUMBER = xplane_constants.BUILD_NUMBER_NONE

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
