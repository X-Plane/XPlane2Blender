# File: xplane_config.py
# Holds config variables that are used throughout the addon.

from .xplane_helpers import XPlaneDebugger, XPlaneProfiler
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

# Variable: debugger
# An instance of <XPlaneDebugger> which is used to output debug information.
debugger = XPlaneDebugger()

errors = []

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


def getDebugger():
    global debugger
    return debugger

def getDebug():
    global debug
    return debug

def getLog():
    global log
    return log

def getVersion():
    global version
    return version

def hasErrors():
    global errors
    return len(errors) > 0

def getErrors():
    global errors
    return errors

def getErrorsAsString():
    global errors
    o = ''
    for i in range(0, len(errors)):
        o += errors[i] + '\n'
    return o

def clearErrors():
    global errors
    del errors[:]

def addError(err):
    global errors
    errors.append(err)
    if debug:
        debugger.debug(err)

def setDebug(d):
    global debug
    debug = d
