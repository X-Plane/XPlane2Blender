# File: xplane_config.py
# Holds config variables that are used throughout the addon.

from .xplane_helpers import XPlaneDebugger,XPlaneProfiler

# Variable: debug
# Set to True for debugging output using <debugger>. Default is True, as we are still dealing with a development release.
debug = False

# Variable: log
# Set to True, to log debug output in a file. This is still experimental.
log = False

# Variable: profile
# Set to True to use profiling processes using the <profiler>. Profiling results will be printed to the console.
profile = False

# Variable: version
# Integer containing the version number of the addon.
version = (3,3,0)

# Variable: debugger
# An instance of <XPlaneDebugger> which is used to output debug information.
debugger = XPlaneDebugger()

# Variable: profiler
# Instance of <XPlaneProfiler> which is used to profile processes.
profiler = XPlaneProfiler()

FLOAT_PRECISION = 8
FLOAT_PRECISION_STR = "8"

errors = False

def initConfig():
    global debug
    global profile
    global log
    import bpy

    if hasattr(bpy.context.scene,"xplane") and bpy.context.scene.xplane.debug:
        debug = True
        if bpy.context.scene.xplane.profile:
            profile = True
        else:
            profile = False

        if bpy.context.scene.xplane.log:
            log = True
        else:
            log = False
    else:
        debug = False
        profile = False
        log = False


def getDebugger():
    global debugger
    return debugger

def getProfiler():
    global profiler
    return profiler

def getDebug():
    global debug
    return debug

def getLog():
    global log
    return log

def getProfile():
    global profile
    return profile

def getVersion():
    global version
    return version

def getErrors():
    global errors
    return errors

def setErrors(err):
    global errors
    errors = err

def setDebug(d):
    global debug
    debug = d
