"""
  #####     ##   ##  ##   ####  ####  ####    #####   ####    ##    ####   ###   ##  ##   ###  #
   #   #   # #    #  #   ##  #  ## #  #  #     #   #  #  #   # #   ##  #  #   #   #  #   #  #  #
  ##   #   # #   # # #  ##      ###   ###     ##   #  ###    # #  ##     ##   #  # # #   ##    #
  ##   #  ####   # # #  #  ###  #     # #     ##   #  # #   ####  #  ### #    #  # # #    ##   #
  #   #   #  #   #  ##  ##  #   # #   # #     #   #   # #   #  #  ##  #  #   #   #  ##  #  #
 #####   ##  ## ##  #    ####  ####  ## ##   #####   ## ## ##  ##  ####   ###   ##  #   ####  #

This file is also an important file for the data model! See the special care
instructions in xplane_updater.py before changing, especially for changing or removing constants!

Please sort this file's sections alphabetically
"""


def _get_addon_folder() -> str:
    import os

    return os.path.dirname(os.path.abspath(__file__))


ADDON_FOLDER = _get_addon_folder()


def _get_resources_folder() -> str:
    import os

    return os.path.join(_get_addon_folder(), "resources")


ADDON_RESOURCES_FOLDER = _get_resources_folder()

# Section: Build Types
# Names for builds types stages we have in
# our software life cycle
BUILD_TYPE_ALPHA = "alpha"
BUILD_TYPE_BETA = "beta"
BUILD_TYPE_DEV = "dev"  # Our pre-alpha stage, generally the most unstable build type
BUILD_TYPE_LEGACY = (
    "leg"  # Any build before the XPlane2BlenderVersion property (< 3.4.0-beta.5)
)
BUILD_TYPE_RC = "rc"

# Types of builds available, ordered in tuple in ascending precedence
BUILD_TYPES = (
    BUILD_TYPE_LEGACY,
    BUILD_TYPE_DEV,
    BUILD_TYPE_ALPHA,
    BUILD_TYPE_BETA,
    BUILD_TYPE_RC,
)

# The string for having no build number, chosen for being descriptive,
# same length as YYYYMMDDHHMMSS, and having no numbers
BUILD_NUMBER_NONE = "NO_BUILD_NUMBR"

# The string found in scene.xplane2blender after 3.4.0-beta.5
DEPRECATED_XP2B_VER = "DEPRECATED"

# Used in determining whether the difference between values
# is large enough to warrant emitting an animation
# or an animation is worth caring about.
PRECISION_KEYFRAME = 5

# Level of rounding before a float is written
# to an OBJ file
PRECISION_OBJ_FLOAT = 8

# none, 1, 2, 3, 4
MAX_LODS = 5
MAX_COCKPIT_REGIONS = 4

EMPTY_USAGE_NONE = "none"
EMPTY_USAGE_EMITTER_PARTICLE = "emitter_particle"
EMPTY_USAGE_EMITTER_SOUND = "emitter_sound"
EMPTY_USAGE_MAGNET = "magnet"

# Kept for historical reasons for the updater
EXPORT_MODE_LAYERS = "layers"
EXPORT_MODE_ROOT_OBJECTS = "root_objects"

EXPORT_TYPE_AIRCRAFT = "aircraft"
EXPORT_TYPE_COCKPIT = "cockpit"
EXPORT_TYPE_SCENERY = "scenery"
EXPORT_TYPE_INSTANCED_SCENERY = "instanced_scenery"

ANIM_TYPE_TRANSFORM = "transform"
ANIM_TYPE_SHOW = "show"
ANIM_TYPE_HIDE = "hide"

CONDITION_GLOBAL_LIGHTING = "GLOBAL_LIGHTING"
CONDITION_GLOBAL_SHADOWS = "GLOBAL_SHADOWS"
CONDITION_VERSION10 = "VERSION10"

COCKPIT_FEATURE_NONE = "none"
# See panel modes as well
COCKPIT_FEATURE_PANEL = "panel"
COCKPIT_FEATURE_DEVICE = "device"

DEVICE_GNS430_1 = "GNS430_1"
DEVICE_GNS430_2 = "GNS430_2"
DEVICE_GNS530_1 = "GNS530_1"
DEVICE_GNS530_2 = "GNS530_2"
DEVICE_CDU739_1 = "CDU739_1"
DEVICE_CDU739_2 = "CDU739_2"
DEVICE_G1000_PFD1 = "G1000_PFD1"
DEVICE_G1000_MFD = "G1000_MFD"
DEVICE_G1000_PFD2 = "G1000_PFD2"

MANIP_DRAG_XY = "drag_xy"
MANIP_DRAG_AXIS = "drag_axis"
MANIP_COMMAND = "command"
MANIP_COMMAND_AXIS = "command_axis"
MANIP_PUSH = "push"
MANIP_RADIO = "radio"
MANIP_DELTA = "delta"
MANIP_WRAP = "wrap"
MANIP_TOGGLE = "toggle"
MANIP_NOOP = "noop"

# 10.10 and greater manips
MANIP_DRAG_AXIS_PIX = "drag_axis_pix"

# 10.50 and greater manips
MANIP_AXIS_KNOB = "axis_knob"
MANIP_AXIS_SWITCH_LEFT_RIGHT = "axis_switch_left_right"
MANIP_AXIS_SWITCH_UP_DOWN = "axis_switch_up_down"
MANIP_COMMAND_KNOB = "command_knob"
MANIP_COMMAND_SWITCH_LEFT_RIGHT = "command_switch_left_right"
MANIP_COMMAND_SWITCH_UP_DOWN = "command_switch_up_down"

# 11.10 and greater manips
# Note: these are not new manips in the OBJ spec, we are reusing manip_drag_axis + using ATTR_axis_detented
# What makes them special is their data is automatically detected as much as possible
MANIP_DRAG_AXIS_DETENT = "drag_axis_detent"

MANIP_DRAG_ROTATE = "drag_rotate"

# This is also a fake manip. This simply allows detents to be used
MANIP_DRAG_ROTATE_DETENT = "drag_rotate_detent"
MANIP_COMMAND_KNOB2 = "command_knob2"
MANIP_COMMAND_SWITCH_LEFT_RIGHT2 = "command_switch_left_right2"
MANIP_COMMAND_SWITCH_UP_DOWN2 = "command_switch_up_down2"

MANIPULATORS_MOUSE_WHEEL = (
    MANIP_DRAG_XY,
    MANIP_DRAG_AXIS,
    MANIP_PUSH,
    MANIP_RADIO,
    MANIP_DELTA,
    MANIP_WRAP,
    MANIP_TOGGLE,
    MANIP_DRAG_AXIS_PIX,
)

MANIPULATORS_OPT_IN = MANIP_DRAG_AXIS


def _get_all_manipulators():
    import inspect

    current_frame = inspect.currentframe()
    return {
        global_name: current_frame.f_globals[global_name]
        for global_name in current_frame.f_globals
        if global_name.startswith("MANIP_") and "CURSOR" not in global_name
    }


MANIPULATORS_ALL = {*_get_all_manipulators().values()}

MANIP_CURSOR_FOUR_ARROWS = "four_arrows"
MANIP_CURSOR_HAND = "hand"
MANIP_CURSOR_BUTTON = "button"
MANIP_CURSOR_ROTATE_SMALL = "rotate_small"
MANIP_CURSOR_ROTATE_SMALL_LEFT = "rotate_small_left"
MANIP_CURSOR_ROTATE_SMALL_RIGHT = "rotate_small_right"
MANIP_CURSOR_ROTATE_MEDIUM = "rotate_medium"
MANIP_CURSOR_ROTATE_MEDIUM_LEFT = "rotate_medium_left"
MANIP_CURSOR_ROTATE_MEDIUM_RIGHT = "rotate_medium_right"
MANIP_CURSOR_ROTATE_LARGE = "rotate_large"
MANIP_CURSOR_ROTATE_LARGE_LEFT = "rotate_large_left"
MANIP_CURSOR_ROTATE_LARGE_RIGHT = "rotate_large_right"
MANIP_CURSOR_UP_DOWN = "up_down"
MANIP_CURSOR_UP = "up"
MANIP_CURSOR_DOWN = "down"
MANIP_CURSOR_LEFT_RIGHT = "left_right"
MANIP_CURSOR_LEFT = "left"
MANIP_CURSOR_RIGHT = "right"
MANIP_CURSOR_ARROW = "arrow"

REQUIRE_SURFACE_NONE = "none"
REQUIRE_SURFACE_DRY = "dry"
REQUIRE_SURFACE_WET = "wet"

LAYER_GROUP_NONE = "none"
LAYER_GROUP_TERRAIN = "terrain"
LAYER_GROUP_BEACHES = "beaches"
LAYER_GROUP_SHOULDERS = "shoulders"
LAYER_GROUP_TAXIWAYS = "taxiways"
LAYER_GROUP_RUNWAYS = "runways"
LAYER_GROUP_MARKINGS = "markings"
LAYER_GROUP_AIRPORTS = "airports"
LAYER_GROUP_ROADS = "roads"
LAYER_GROUP_OBJECTS = "objects"
LAYER_GROUP_LIGHT_OBJECTS = "light_objects"
LAYER_GROUP_CARS = "cars"

VERSION_900 = "900"
VERSION_1000 = "1000"
VERSION_1010 = "1010"
VERSION_1040 = "1040"
VERSION_1050 = "1050"
VERSION_1100 = "1100"
VERSION_1110 = "1110"
VERSION_1130 = "1130"

SURFACE_TYPE_NONE = "none"
SURFACE_TYPE_WATER = "water"
SURFACE_TYPE_CONCRETE = "concrete"
SURFACE_TYPE_ASPHALT = "asphalt"
SURFACE_TYPE_GRASS = "grass"
SURFACE_TYPE_DIRT = "dirt"
SURFACE_TYPE_GRAVEL = "gravel"
SURFACE_TYPE_LAKEBED = "lakebed"
SURFACE_TYPE_SNOW = "snow"
SURFACE_TYPE_SHOULDER = "shoulder"
SURFACE_TYPE_BLASTPAD = "blastpad"

BLEND_OFF = "off"
BLEND_ON = "on"
BLEND_SHADOW = "shadow"
BLEND_GLASS = "glass"

LIGHT_DEFAULT = "default"
LIGHT_FLASHING = "flashing"
LIGHT_PULSING = "pulsing"
LIGHT_STROBE = "strobe"
LIGHT_TRAFFIC = "traffic"
LIGHT_NAMED = "named"
LIGHT_CUSTOM = "custom"
LIGHT_PARAM = "param"
LIGHT_AUTOMATIC = "automatic"
LIGHT_SPILL_CUSTOM = "light_spill_custom"
LIGHT_NON_EXPORTING = "nonexporting"

LIGHTS_OLD_TYPES = {
    LIGHT_DEFAULT,
    LIGHT_FLASHING,
    LIGHT_PULSING,
    LIGHT_STROBE,
    LIGHT_TRAFFIC,
}

LIGHT_PARAM_SIZE_MIN = 0.001

LOGGER_LEVEL_ERROR = "error"
LOGGER_LEVEL_INFO = "info"
LOGGER_LEVEL_SUCCESS = "success"
LOGGER_LEVEL_WARN = "warn"

LOGGER_LEVELS_ALL = (
    LOGGER_LEVEL_ERROR,
    LOGGER_LEVEL_INFO,
    LOGGER_LEVEL_SUCCESS,
    LOGGER_LEVEL_WARN,
)

PANEL_COCKPIT = "cockpit"
PANEL_COCKPIT_LIT_ONLY = "cockpit_lit_only"
PANEL_COCKPIT_REGION = "cockpit_region"
