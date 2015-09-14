# File: xplane_config.py
# Holds config variables that are used throughout the addon.

from . import bl_info

# Variable: debug
# Set to True for debugging output using <debugger>. Default is True, as we are still dealing with a development release.
debug = False

# Variable: log
# Set to True, to log debug output in a file. This is still experimental.
log = False

# Variable: version
# Integer containing the version number of the addon.
version = bl_info['version']

MAX_LODS = 4
MAX_COCKPIT_REGIONS = 4

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

def getVersion():
    global version
    return version

def setDebug(d):
    global debug
    debug = d
