# File: xplane_props.py
# Defines X-Plane Properties attached to regular Blender data types.

import bpy
import datetime
import re
import io_xplane2blender
from . import xplane_constants
from . import xplane_config
from .xplane_config import CURRENT_BUILD_TYPE, CURRENT_BUILD_TYPE_VERSION
from .xplane_config import CURRENT_DATA_MODEL_VERSION, CURRENT_BUILD_NUMBER
from .xplane_constants import *

from . import xplane_helpers
from .xplane_helpers import getColorAndLitTextureSlots


'''
 #####     ##   ##  ##   ####  ####  ####  #
  #   #   # #    #  #   ##  #  ## #  #  #  #
 ##   #   # #   # # #  ##      ###   ###   #
 ##   #  ####   # # #  #  ###  #     # #   #
 #   #   #  #   #  ##  ##  #   # #   # # 
#####   ##  ## ##  #    ####  ####  ## ## #

 ### ##  ####  ####  ####      ##   ###    ###   ###     ####  ####    #####   ####    ##    ####   ###   ##  ##   ###  #
  #  #   ## #  #  #  ## #     # #    #    #  #  #   #    #  #  ## #     #   #  #  #   # #   ##  #  #   #   #  #   #  #  #
 #####   ###   ###   ###      # #   ##    ##   ##   #    ###   ###     ##   #  ###    # #  ##     ##   #  # # #   ##    #
 #  ##   #     # #   #       ####   #      ##  #    #    # #   #       ##   #  # #   ####  #  ### #    #  # # #    ##   #
 #  #    # #   # #   # #     #  #   #  # #  #  #   #     # ##  # #     #   #   # #   #  #  ##  #  #   #   #  ##  #  # 
## ###  ####  ## ## ####    ##  ## ##### ####   ###     ####  ####    #####   ## ## ##  ##  ####   ###   ##  #   ####  #
                                                                                                                          
BEWARE! This file contains, basically, the whole definition for the XPlane2Blender data model! Whatever you add will last
until it is deprecated and/or updated (more dragons!) Whatever you remove will create backwards compatibility issues!

For wanting to change xplane_props.py, YOU MUST NOW READ THE HEADER OF xplane_updater.py OR YOU'LL RECIEVE AN ANCIENT CURSE:
    
    "Due to an undocumented bad decision during the development of B, all your time and date functions will begin
    randomly choosing different default timezones arguments and changing your OS's timezone at the same time!"
    The curse will only end after 03:14:08 UTC on 19 January 2038 because of another bad decision from the early 1970's"

Actual Practical Notes
======================
- Since Blender saves the **index** the user chose of a drop down menu, not the content, re-ordering the items list member of an EnumProperty
is a great way to RUIN EVERYTHING. Re-arranging the items list requires great care and is backwards-compatibility breaking

- Main documentation: https://docs.blender.org/api/current/bpy.props.html?highlight=bpy%20props%20prop#module-bpy.props

- The attr member does not appear to be necessary or have an effect on the program. Future props should not use it. Otherwise, I'd like to
see them culled over time

- This file contains 99% of the properties. xplane2blender is set in xplane_updater.py and now we're stuck with it there
 
- Name is in the form of "Title Case Always", description is "Sentence case, no period". Don't be lazy and just copy and paste the constant name for all three columns.
A good deal of time was spent making the UI look pretty for 3.4.0 so please don't undo that overtime

- If you've actually read this far, congratulations! You get a cookie!

- For defaults, use the constants, not redundantly copying their values 

- Don't forget to add your new prop to addXPlaneRNA and removeXPlaneRNA!

- If you've invented a new PropertyGroup, you must wrap it in a PointerProperty or use it in a CollectionProperty
'''

# Class: XPlane2Blender 
#
# Contains useful methods for getting information about the
# version and build number of XPlane2Blender 
# 
# Names are usually in the format of
# major.minor.release-(alpha|beta|dev|leg|rc)\.[0-9]+)\+\d+\.(YYYYMMDDHHMMSS)

# Internal variable to enable and disable the ability to update the value of XPlane2Blender's properties
# Do not change outside of safe_set_version_data! 
__version_safety_off = False
class XPlane2BlenderVersion(bpy.types.PropertyGroup):
    
    #Guards against being updated without being validated
    def update_version_property(self,context):
        if __version_safety_off is False:
            raise Exception("Do not modify version property outside of safe_set_version_data!")
        return None

    # Property: addon_version
    # Tuple of Blender addon version, (major, minor, revision)
    addon_version = bpy.props.IntVectorProperty(
        name = "XPlane2Blender Addon Version",
        description = "The version of the addon (also found in it's addons information)",
        default=(0,0,0),
        update=update_version_property,
        size=3)
    
    #Addon string in the form of "m.m.r", no parenthesis
    def addon_version_clean_str(self):
        return '.'.join(map(str,self.addon_version))
    
    # Property: build_type
    # The type of build this is, always a value in BUILD_TYPES
    build_type = bpy.props.StringProperty(
        name="Build Type",
        description="Which iteration in the development cycle of the chosen build type we're at",
        default=xplane_constants.BUILD_TYPE_DEV,
        update=update_version_property
    )

    # Property: build_type_version
    #
    # The iteration in the build cycle, 0 for dev and legacy, > 0 for everything else
    build_type_version = bpy.props.IntProperty(
        name="Build Type Version",
        description="Which iteration in the development cycle of the chosen build type we're at",
        default=0,
        update=update_version_property
    )

    # Property: data_model_version
    #
    # The version of the data model, tracked seperately. Always incrementing.
    data_model_version = bpy.props.IntProperty(
        name="Data Model Version",
        description="Version of the data model (constants,props, and updater functionality) this version of the addon is. Always incrementing on changes",
        default=0,
        update=update_version_property
    )
    

    # Property: build_number
    #
    # If run as a public facing build, this value will be replaced
    # with the YYYYMMSSHHMMSS at build creation date.
    # Otherwise, it defaults to xplane_constants.BUILD_NUMBER_NONE
    build_number = bpy.props.StringProperty(
        name="Build Number",
        description="Build number of XPlane2Blender. If blank, this is a development build!",
        default=xplane_constants.BUILD_NUMBER_NONE,
        update=update_version_property
    )
    
    # Method: safe_set_version_data
    #
    # The only way to change version data! Use responsibly for suffer the Dragons described above!
    # Returns True if it succeeded, or False if it failed due to invalid data.
    def safe_set_version_data(self,addon_version,build_type,build_type_version,data_model_version,build_number):
        if xplane_helpers.VerStruct(addon_version,
                          build_type,
                          build_type_version,
                          data_model_version,
                          build_number).is_valid():
            global __version_safety_off
            __version_safety_off = True
            self.addon_version      = addon_version
            self.build_type         = build_type
            self.build_type_version = build_type_version
            self.data_model_version = data_model_version
            self.build_number       = build_number
            __version_safety_off = False
            return True
        else:
            return False

    # Method: asFileName
    #
    # Gets the version in its filename version (all .'s replaced with version
    def as_file_name(self):
        return str(self).replace('.','_')

    def make_struct(self):
        return xplane_helpers.VerStruct(self.addon_version, self.build_type, self.build_type_version, self.data_model_version, self.build_number)

    #repr and repr of the parsed version return the same thing
    def __repr__(self):    
        return "(%s, %s, %s, %s, %s)" % ('(' + ','.join(map(str,self.addon_version)) + ')',
                                         "'" + str(self.build_type) + "'",
                                               str(self.build_type_version),
                                               str(self.data_model_version),
                                         "'" + str(self.build_number) + "'")
    #str Used for most purposes
    def __str__(self):
        return "%s-%s.%s+%s.%s" % ('(' + '.'.join(map(str,self.addon_version)) + ')',
                                   self.build_type,
                                   self.build_type_version,
                                   self.data_model_version,
                                   self.build_number)
        
    def short_str(self):
        return str(self)[:str(self).index('+')]

# Class: XPlaneCustomAttribute
# A custom attribute.
#
# Properties:
#   string name - Name of the attribute
#   string value - Value of the attribute
#   string reset - Reseter of the attribute
class XPlaneCustomAttribute(bpy.types.PropertyGroup):
    name = bpy.props.StringProperty(
        attr = "name",
        name = "Name",
        description = "Name",
        default = ""
    )

    value = bpy.props.StringProperty(
        attr = "value",
        name = "Value",
        description = "Value",
        default = ""
    )

    reset = bpy.props.StringProperty(
        attr = "reset",
        name = "Reset",
        description = "Reset",
        default = ""
    )

    weight = bpy.props.IntProperty(
        name = "Weight",
        description = "The more weight an attribute has the later it gets written in the OBJ",
        default = 0,
        min = 0
    )

class XPlaneExportPathDirective(bpy.types.PropertyGroup):
    export_path = bpy.props.StringProperty(
        name = "Export Path",
        description="The export path that should be copied into a library.txt",
    )

# Class: XPlaneDataref
# A X-Plane Dataref
#
# Properties:
#   string path - Dataref path
#   float value - Dataref value (can be keyframed)
#   int loop - Loop amount of dataref animation.
class XPlaneDataref(bpy.types.PropertyGroup):
    path = bpy.props.StringProperty(
        attr = "path",
        name = "Dataref Path",
        description = "Dataref Path",
        default = ""
    )

    value = bpy.props.FloatProperty(
        attr = "value",
        name = "Value",
        description = "Value",
        default = 0.0,
        precision = 6
    )

    loop = bpy.props.FloatProperty(
        name = "Loop Animation Every",
        description = "Loop amount of animation, useful for ever increasing Datarefs. A value of 0 will ignore this setting",
        min = 0.0,
        precision = 3
    )

    anim_type = bpy.props.EnumProperty(
        attr = "anim_type",
        name = "Animation Type",
        description = "Type of animation this Dataref will use",
        default = ANIM_TYPE_TRANSFORM,
        items = [
            (ANIM_TYPE_TRANSFORM, "Transformation", "Transformation"),
            (ANIM_TYPE_SHOW, "Show", "Show"),
            (ANIM_TYPE_HIDE, "Hide", "Hide")
        ]
    )

    show_hide_v1 = bpy.props.FloatProperty(
        attr = "show_hide_v1",
        name = "Value 1",
        description = "Show/Hide value 1",
        default = 0.0
    )

    show_hide_v2 = bpy.props.FloatProperty(
        attr = "show_hide_v2",
        name = "Value 2",
        description = "Show/Hide value 2",
        default = 0.0
    )


# Class: XPlaneCondition
# A custom attribute.
#
# Properties:
#   string variable - Condition variable
#   string value - Value of the variable
#   string operator - Conditional operator to use
class XPlaneCondition(bpy.types.PropertyGroup):
    variable = bpy.props.EnumProperty(
        attr = "variable",
        name = "Variable",
        description = "Variable",
        default = CONDITION_GLOBAL_LIGHTING,
        items = [
            (CONDITION_GLOBAL_LIGHTING, 'HDR', 'HDR mode On/Off'),
            (CONDITION_GLOBAL_SHADOWS, 'Global Shadows', 'Global shadows On/Off'),
            (CONDITION_VERSION10, 'Version 10.x', 'Always "On", as V9 does not support conditions')
        ]
    )

    value = bpy.props.BoolProperty(
        attr = "value",
        name = "Must Be On",
        description = "On/Off",
        default = True
    )

# Class: XPlaneDatarefSearch
# Not used right now. Might be used to search for dataref paths.
#class XPlaneDatarefSearch(bpy.types.PropertyGroup):
#    path = bpy.props.StringProperty(attr = "path",
#                                    name = "Dataref path",
#                                    description = "XPlane Dataref path",
#                                    default = "")

# Class: XPlaneManipulator
# A X-Plane manipulator settings
#
# Properties:
#   bool enabled - True if object is a manipulator
#   enum type - Manipulator types as defined in OBJ specs.
#   string tooltip - Manipulator Tooltip
#   enum cursor - Manipulator cursors as defined in OBJ specs.
#   int dx - X-Drag axis length
#   int dy - Y-Drag axis length
#   int dz - Z-Drag axis length
#   float v1 - Value 1
#   float v2 - Value 2
#   float v1_min - Value 1 min.
#   float v1_max - Value 1 max.
#   float v2_min - Value 2 min.
#   float v2_max - Value 2 max.
#   float v_down - Value on mouse down
#   float v_up - Value on mouse up
#   float v_hold - Value on mouse hold
#   float v_on - On value
#   float v_off - Off value
#   string command - Command
#   string positive_command - Positive command
#   string negative_command - Negative command
#   string dataref1 - Dataref 1
#   string dataref2 - Dataref 2
class XPlaneManipulator(bpy.types.PropertyGroup):
    enabled = bpy.props.BoolProperty(
        attr = "enabled",
        name = "Manipulator",
        description = "If checked this object will be treated as a manipulator",
        default = False
    )

    type = bpy.props.EnumProperty(
        attr = "type",
        name = "Manipulator Type",
        description = "The type of the manipulator",
        default = MANIP_DRAG_XY,
        items = [
            (MANIP_DRAG_XY,      "Drag XY",      "Drag XY"),
            (MANIP_DRAG_AXIS,    "Drag Axis",    "Drag Axis"),
            (MANIP_COMMAND,      "Command",      "Command"),
            (MANIP_COMMAND_AXIS, "Command Axis", "Command Axis"),
            (MANIP_PUSH,         "Push",         "Push"),
            (MANIP_RADIO,        "Radio",        "Radio"),
            (MANIP_DELTA,        "Delta",        "Delta"),
            (MANIP_WRAP,         "Wrap",         "Wrap"),
            (MANIP_TOGGLE,       "Toggle",       "Toggle"),
            (MANIP_NOOP,         "No-op",        "No-op"),
            (MANIP_DRAG_AXIS_PIX,             "Drag Axis Pix (v10.10)",             "Drag Axis Pix (requires at least v10.10)"),
            (MANIP_COMMAND_KNOB,              "Command Knob (v10.50)",              "Command Knob (requires at least v10.50)"),
            (MANIP_COMMAND_SWITCH_UP_DOWN,    "Command Switch Up Down (v10.50)",    "Command Switch Up Down (requires at least v10.50)"),
            (MANIP_COMMAND_SWITCH_LEFT_RIGHT, "Command Switch Left Right (v10.50)", "Command Switch Left Right (requires at least v10.50)"),
            (MANIP_AXIS_SWITCH_UP_DOWN,       "Axis Switch Up Down (v10.50)",       "Axis Switch Up Down (requires at least v10.50)"),
            (MANIP_AXIS_SWITCH_LEFT_RIGHT,    "Axis Switch Left Right (v10.50)",    "Axis Switch Left Right (requires at least v10.50)")
        ]
    )

    tooltip = bpy.props.StringProperty(
        attr = "tooltip",
        name = "Manipulator Tooltip",
        description = "The tooltip will be displayed when hovering over the object",
        default = ""
    )

    cursor = bpy.props.EnumProperty(
        attr = "cursor",
        name = "Manipulator Cursor",
        description = "The mouse cursor type when hovering over the object",
        default = MANIP_CURSOR_HAND,
        items = [
            (MANIP_CURSOR_FOUR_ARROWS,          "Four Arrows",         "Four Arrows"),
            (MANIP_CURSOR_HAND,                 "Hand",                "Hand"),
            (MANIP_CURSOR_BUTTON,               "Button",              "Button"),
            (MANIP_CURSOR_ROTATE_SMALL,         "Rotate Small",        "Rotate Small"),
            (MANIP_CURSOR_ROTATE_SMALL_LEFT,    "Rotate Small Left",   "Rotate Small Left"),
            (MANIP_CURSOR_ROTATE_SMALL_RIGHT,   "Rotate Small Right",  "Rotate Small Right"),
            (MANIP_CURSOR_ROTATE_MEDIUM,        "Rotate Medium",       "Rotate Medium"),
            (MANIP_CURSOR_ROTATE_MEDIUM_LEFT,   "Rotate Medium Left",  "Rotate Medium Left"),
            (MANIP_CURSOR_ROTATE_MEDIUM_RIGHT,  "Rotate Medium Right", "Rotate Medium Right"),
            (MANIP_CURSOR_ROTATE_LARGE,         "Rotate Large",        "Rotate Large"),
            (MANIP_CURSOR_ROTATE_LARGE_LEFT,    "Rotate Large Left",   "Rotate Large Left"),
            (MANIP_CURSOR_ROTATE_LARGE_RIGHT,   "Rotate Large Right",  "Rotate Large Right"),
            (MANIP_CURSOR_UP_DOWN,              "Up Down",             "Up Down"),
            (MANIP_CURSOR_DOWN,                 "Down",                "Down"),
            (MANIP_CURSOR_UP,                   "Up",                  "Up"),
            (MANIP_CURSOR_LEFT_RIGHT,           "Left Right",          "Left Right"),
            (MANIP_CURSOR_LEFT,                 "Left",                "Left"),
            (MANIP_CURSOR_RIGHT,                "Right",               "Right"),
            (MANIP_CURSOR_ARROW,                "Arrow",               "Arrow"),
        ]
    )

    dx = bpy.props.FloatProperty(
        attr = "dx",
        name = "Drag X",
        description = "X-Drag axis length",
        default = 0.0
    )

    dy = bpy.props.FloatProperty(
        attr = "dy",
        name = "Drag Y",
        description = "Y-Drag axis length",
        default = 0.0
    )

    dz = bpy.props.FloatProperty(
        attr = "dz",
        name = "Drag Z",
        description = "Z-Drag axis length",
        default = 0.0
    )

    v1 = bpy.props.FloatProperty(
        attr = "v1",
        name = "Value 1",
        description = "Value 1",
        default = 0.0
    )

    v2 = bpy.props.FloatProperty(
        attr = "v2",
        name = "Value 2",
        description = "Value 2",
        default = 0.0
    )

    v1_min = bpy.props.FloatProperty(
        attr = "v1_min",
        name = "Value 1 Min",
        description = "Value 1 min",
        default = 0.0
    )

    v1_max = bpy.props.FloatProperty(
        attr = "v1_max",
        name = "Value 1 Max",
        description = "Value 1 max",
        default = 0.0
    )

    v2_min = bpy.props.FloatProperty(
        attr = "v2_min",
        name = "Value 2 Min",
        description = "Value 2 min",
        default = 0.0
    )

    v2_max = bpy.props.FloatProperty(
        attr = "v2_max",
        name = "Value 2 Max",
        description = "Value 2 max",
        default = 0.0
    )

    v_down = bpy.props.FloatProperty(
        attr = "v_down",
        name = "Value On Mouse Down",
        description = "Value to set dataref on mouse down",
        default = 0.0
    )

    v_up = bpy.props.FloatProperty(
        attr = "v_up",
        name = "Value On Mouse Up",
        description = "Value to set dataref on mouse up",
        default = 0.0
    )

    v_hold = bpy.props.FloatProperty(
        attr = "v_hold",
        name = "Value On Mouse Hold",
        description = "Value to set dataref on mouse hold",
        default = 0.0
    )

    v_on = bpy.props.FloatProperty(
        attr = "v_on",
        name = "On Value",
        description = "On value",
        default = 0.0
    )

    v_off = bpy.props.FloatProperty(
        attr = "v_off",
        name = "Off Value",
        description = "Off value",
        default = 0.0
    )

    command = bpy.props.StringProperty(
        attr = "command",
        name = "Command",
        description = "The command to fire when manipulator is used",
        default = ""
    )

    positive_command = bpy.props.StringProperty(
        attr = "positive_command",
        name = "Positive Command",
        description = "Positive command",
        default = ""
    )

    negative_command = bpy.props.StringProperty(
        attr = "negative_command",
        name = "Negative Command",
        description = "Negative command",
        default = ""
    )

    dataref1 = bpy.props.StringProperty(
        attr = "dataref1",
        name = "Dataref 1",
        description = "Dataref 1",
        default = "")

    dataref2 = bpy.props.StringProperty(
        attr = "dataref2",
        name = "Dataref 2",
        description = "Dataref 2",
        default = ""
    )

    step = bpy.props.FloatProperty(
        attr = "step",
        name = "Step",
        description = "Dataref increment",
        default = 1.0
    )

    click_step = bpy.props.FloatProperty(
        attr = "click_step",
        name = "Click Step",
        description = "Value change on click",
        default = 0.0
    )

    hold_step = bpy.props.FloatProperty(
        attr = "hold_step",
        name = "Hold Step",
        description = "Value change on hold",
        default = 0.0
    )

    wheel_delta = bpy.props.FloatProperty(
        attr = "wheel_delta",
        name = "Wheel Delta",
        description = "Value change on mouse wheel tick",
        default = 0.0
    )

    exp = bpy.props.FloatProperty(
        attr = "exp",
        name = "Exp",
        description = "Power of an exponential curve that controls the speed at which the dataref changes. Higher numbers cause a more “non-linear” response, where small drags are very precise and large drags are very fast",
        default = 1.0
    )

# Class: XPlaneCockpitRegion
# Defines settings for a cockpit region.
#
# Properties:
#   int top - top position of the region in px
#   int left - left position of the region in px
#   int width - width of the region in powers of 2
#   int height - height of the region in powers of 2
class XPlaneCockpitRegion(bpy.types.PropertyGroup):
    expanded = bpy.props.BoolProperty(
        name = "Expanded",
        description = "Toggle this cockpit region settings visibility",
        default = False
    )

    top = bpy.props.IntProperty(
        attr = "top",
        name = "Top",
        description = "Top",
        default = 0,
        min = 0,
        max = 2048
    )

    left = bpy.props.IntProperty(
        attr = "left",
        name = "Left",
        description = "Left",
        default = 0,
        min = 0,
        max = 2048
    )

    width = bpy.props.IntProperty(
        attr = "width",
        name = "Width",
        description = "Width in powers of 2",
        default = 1,
        min = 1,
        max = 11
    )

    height = bpy.props.IntProperty(
        attr = "height",
        name = "Height",
        description = "Height in powers of 2",
        default = 1,
        min = 1,
        max = 11
    )

# Class: XPlaneLOD
# Defines settings for a level of detail.
#
# Properties:
#   int near - near distance
#   int far - far distance
class XPlaneLOD(bpy.types.PropertyGroup):
    expanded = bpy.props.BoolProperty(
        name = "Expanded",
        description = "Toggle this LOD settings visibility",
        default = False
    )

    near = bpy.props.IntProperty(
        name = "Near",
        description = "Near distance (inclusive) in meters",
        default = 0,
        min = 0
    )

    far = bpy.props.IntProperty(
        name = "Far",
        description = "Far distance (exclusive) in meters",
        default = 0,
        min = 0
    )

def make_lods_array():
    lods_arr = [("0","None","None")]
    for i in range(1,MAX_LODS):
        lods_arr.append((str(i),str(i),str(i)))
    return lods_arr

# Class: XPlaneLayer
# Defines settings for a OBJ file. Is "parented" to a Blender layer.
#
# Properties:
#   int index - index of this layer.
#   bool expanded - True if the settings of this layer are expanded in the UI.
#   string name - Name of the OBJ file to export from this layer.
#   bool cockpit - True if this layer serves as a cockpit OBJ.
#   float slungLoadWeight - Slung Load weight
#   string texture - Texture file to use for this OBJ.
#   string texture_lit - Night Texture to use for this OBJ.
#   string texture_normal - Normal/Specular Texture to use for this OBJ.
#   customAttributes - Collection of <XPlaneCustomAttributes>. Custom X-Plane header attributes.
class XPlaneLayer(bpy.types.PropertyGroup):
    index = bpy.props.IntProperty(
        attr = "index",
        name = "Index",
        description = "The blender layer index",
        default = -1
    )
    
    expanded = bpy.props.BoolProperty(
        attr = "expanded",
        name = "Expanded",
        description = "Toggles the layer settings visibility",
        default = False
    )
    
    export = bpy.props.BoolProperty(
        attr = "export",
        name = "Export",
        description = "If checked, this layer will be exported if visible",
        default = True
    )

    export_path_directives = bpy.props.CollectionProperty(
        name = "Export Directives for Layer",
        description = "A collection of export paths intended for an OBJ's EXPORT directives",
        type = XPlaneExportPathDirective
	)

    debug = bpy.props.BoolProperty(
        attr = "debug",
        name = "Debug",
        description = "If checked, this OBJ file will put diagnostics in Plane's log.txt",
        default = True
    )

    name = bpy.props.StringProperty(
        attr = "name",
        name = "Name",
        description = "This name will be used as a filename hint for OBJ file(s)",
        default = ""
    )

    export_type = bpy.props.EnumProperty(
        attr = "export_type",
        name = "Type",
        description = "What kind of thing are you going to export?",
        default = "aircraft",
        items = [
            (EXPORT_TYPE_AIRCRAFT, "Aircraft (Part)", "Aircraft (Part)"),
            (EXPORT_TYPE_COCKPIT, "Cockpit", "Cockpit"),
            (EXPORT_TYPE_SCENERY, "Scenery Object", "Scenery Object"),
            (EXPORT_TYPE_INSTANCED_SCENERY, "Instanced Scenery Object", "Instanced Scenery Object")
        ]
    )

    # Deprecated: This will be removed in v3.4
    cockpit = bpy.props.BoolProperty(
        attr = "cockpit",
        name = "Cockpit",
        description = "If checked the exported object will be interpreted as a cockpit",
        default = False
    )

    slungLoadWeight = bpy.props.FloatProperty(
        attr = "slungLoadWeight",
        name = "Slung Load Weight",
        description = "Weight of the object in pounds, for use in the physics engine if the object is being carried by a plane or helicopter",
        default = 0.0,
        step = 1,
        precision = 3
    )

    texture = bpy.props.StringProperty(
        attr = "texture",
        subtype = "FILE_PATH",
        name = "Texture",
        description = "Texture to use for objects on this layer",
        default = ""
    )

    texture_lit = bpy.props.StringProperty(
        attr = "texture_lit",
        subtype = "FILE_PATH",
        name = "Night Texture",
        description = "Night Texture to use for objects on this layer",
        default = ""
    )

    texture_normal = bpy.props.StringProperty(
        attr = "texture_normal",
        subtype = "FILE_PATH",
        name = "Normal/Specular Texture",
        description = "Normal/Specular Texture to use for objects on this layer",
        default = ""
    )

    # v1000
    texture_draped = bpy.props.StringProperty(
        attr = "texture_draped",
        subtype = "FILE_PATH",
        name = "Draped Texture",
        description = "Texture to use for draped objects on this layer",
        default = ""
    )

    # v1000
    texture_draped_normal = bpy.props.StringProperty(
        attr = "texture_draped_normal",
        subtype = "FILE_PATH",
        name = "Normal/Specular Texture Draped Texture",
        description = "Normal/Specular Texture to use for draped objects on this layer",
        default = ""
    )

    cockpit_regions = bpy.props.EnumProperty(
        attr = "cockpit_regions",
        name = "Cockpit Regions",
        description = "Number of Cockpit regions to use",
        default = "0",
        items = [
            ("0", "None", "None"),
            ("1", "1", "1"),
            ("2", "2", "2"),
            ("3", "3", "3"),
            ("4", "4", "4")
        ]
    )

    cockpit_region = bpy.props.CollectionProperty(
        name = "Cockpit Region",
        type = XPlaneCockpitRegion,
        description = "Cockpit Region"
    )

    lods = bpy.props.EnumProperty(
        name = "Levels of Detail",
        description = "Levels of detail",
        default = "0",
        items = make_lods_array()
    )

    lod = bpy.props.CollectionProperty(
        name = "LOD",
        type = XPlaneLOD,
        description = "Level of detail"
    )

    # v1000
    lod_draped = bpy.props.FloatProperty(
        attr = "lod_draped",
        name = "Max. Draped LOD",
        description = "Maximum LOD distance for draped geometry. Set to 0 to use farest LOD",
        default = 0,
        min = 0
    )

    # v1000
    tilted = bpy.props.BoolProperty(
        attr = "tilted",
        name = "Tilted",
        description = "Causes objects placed on a scenery tile to sit “on” the ground even if it is sloped",
        default = False
    )

    # v1000
    slope_limit = bpy.props.BoolProperty(
        attr = "slope_limit",
        name = "Slope Limit",
        description = "Establishes the maximum slope limit an object will tolerate (in degrees) for library objects placed in a DSF",
        default = False
    )

    # v1000
    slope_limit_min_pitch = bpy.props.FloatProperty(
        attr = "slope_limit_min_pitch",
        name = "Min. Pitch",
        description = "Represents the ground sloping down at the front of the object in degrees",
        default = 0.0
    )

    # v1000
    slope_limit_max_pitch = bpy.props.FloatProperty(
        attr = "slope_limit_max_pitch",
        name = "Max. Pitch",
        description = "Represents the ground sloping down at the front of the object in degrees",
        default = 0.0
    )

    # v1000
    slope_limit_min_roll = bpy.props.FloatProperty(
        attr = "slope_limit_min_roll",
        name = "Min. Roll",
        description = "Represents the ground sloping down to the left of the object in degrees",
        default = 0.0
    )

    # v1000
    slope_limit_max_roll = bpy.props.FloatProperty(
        attr = "slope_limit_max_roll",
        name = "Max. Roll",
        description = "Represents the ground sloping down to the left of the object in degrees",
        default = 0.0
    )

    # v1000
    require_surface = bpy.props.EnumProperty(
        attr = "require_surface",
        name = "Require Surface",
        description = "Whether an object should be used over wet or dry terrain when placed from the library",
        default = "none",
        items = [
            (REQUIRE_SURFACE_NONE, "Any", "Any surface"),
            (REQUIRE_SURFACE_DRY, "Dry", "Must be placed on dry surface"),
            (REQUIRE_SURFACE_WET, "Wet", "Must be placed on wet surface")
        ]
    )

    # v1010
    shadow = bpy.props.BoolProperty(
        attr = "shadow",
        name = "Cast Shadows (Global)",
        description = "If disabled object will not cast any shadows",
        default = True
    )

    # v1010
    cockpit_lit = bpy.props.BoolProperty(
        attr = "cockpit_lit",
        name = "3D-Cockpit Lighting",
        default = True
    )

    # v1000
    layerGroups = [
        (LAYER_GROUP_NONE,          "None",          "Does not draws this OBJ in any group"),
        (LAYER_GROUP_TERRAIN,       "Terrain",       "Terrain"),
        (LAYER_GROUP_BEACHES,       "Beaches",       "Beaches"),
        (LAYER_GROUP_SHOULDERS,     "Shoulders",     "Shoulders"),
        (LAYER_GROUP_TAXIWAYS,      "Taxiways",      "Taxiways"),
        (LAYER_GROUP_RUNWAYS,       "Runways",       "Runways"),
        (LAYER_GROUP_MARKINGS,      "Markings",      "Markings"),
        (LAYER_GROUP_AIRPORTS,      "Airports",      "Airports"),
        (LAYER_GROUP_ROADS,         "Roads",         "Roads"),
        (LAYER_GROUP_OBJECTS,       "Objects",       "Objects"),
        (LAYER_GROUP_LIGHT_OBJECTS, "Light Objects", "Light Objects"),
        (LAYER_GROUP_CARS,          "Cars",          "Cars")
    ]

    layer_group = bpy.props.EnumProperty(
        attr = "layer_group",
        name = "Layer Group",
        description = "Draw this OBJ in a special group",
        default = "none",
        items = layerGroups
    )

    layer_group_offset = bpy.props.IntProperty(
        attr = "layer_group_offset",
        name = "Layer Group Offset",
        description = "Use to fine tune drawing order",
        default = 0,
        min = -5,
        max = 5
    )

    layer_group_draped = bpy.props.EnumProperty(
        attr = "layer_group_draped",
        name = "Draped Layer Group",
        description = "Draws draped geometry in a special group",
        default = "none",
        items = layerGroups
    )

    layer_group_draped_offset = bpy.props.IntProperty(
        attr = "layer_group_draped_offset",
        name = "Draped Layer Group Offset",
        description = "Use to fine tune drawing order of draped geometry",
        default = 0,
        min = -5,
        max = 5
    )

    customAttributes = bpy.props.CollectionProperty(
        attr = "customAttributes",
        name = "Custom X-Plane Header Attributes",
        description = "User defined header attributes for the X-Plane file",
        type = XPlaneCustomAttribute
    )

    autodetectTextures = bpy.props.BoolProperty(
        attr = "autodetectTextures",
        name = "Autodetect Textures",
        description = "Automaticly determines textures based on materials",
        default = True
    )

# Class: XPlaneSceneSettings
# Settings for Blender scenes.
#
# Properties:
#   layers - Collection of <XPlaneLayers>. Export settings for the Blender layers.
class XPlaneSceneSettings(bpy.types.PropertyGroup):
    debug = bpy.props.BoolProperty(
        attr = "debug",
        name = "Print Debug Info To Output, OBJ",
        description = "If checked debug information will be printed to the console and into OBJ files",
        default = False
    )

    log = bpy.props.BoolProperty(
        attr = "log",
        name = "Create Log File",
        description = "If checked the debug information will be written to a log file",
        default = False
    )

    # Plugin development tools
    plugin_development = bpy.props.BoolProperty(
        attr = "plugin_development",
        name = "Plugin Development Tools (Experimental!)",
        description = "A selection of tools and options for plugin developers to write and debug XPlane2Blender. You are unlikely to find these useful",
        default = False) # Set this to true during development to avoid re-checking it
    
    dev_enable_breakpoints = bpy.props.BoolProperty(
        attr = "dev_enable_breakpoints",
        name = "Enable Breakpoints",
        description = "Allows use of Eclipse breakpoints (must have PyDev, Eclipse installed and configured to use and Pydev Debug Server running!)",
        default = False)
    
    dev_continue_export_on_error = bpy.props.BoolProperty(
        attr = "dev_continue_export_on_error",
        name = "Continue Export On Error",
        description = "Exporter continues even when an OBJ cannot be exported. It does not affect unit tests",
        default = False)
    
    dev_export_as_dry_run = bpy.props.BoolProperty(
        name        = 'Dry Run',
        description = 'Run exporter without actually writing .objs to disk',
        default = False)
    
    dev_fake_xplane2blender_version = bpy.props.StringProperty(
        name       = "Fake XPlane2Blender Version",
        description = "The Fake XPlane2Blender Version to re-run the upgrader with",
        default = "")#str(bpy.context.scene.xplane.get("xplane2blender_ver")))
    #######################################

    layers = bpy.props.CollectionProperty(
        attr = "layers",
        name = "Layers",
        description = "Export settings for the Blender layers",
        type = XPlaneLayer
    )

    optimize = bpy.props.BoolProperty(
        attr = "optimize",
        name = "Optimize",
        description = "If checked file size will be optimized. However this can increase export time dramatically",
        default = False
    )

    version = bpy.props.EnumProperty(
        attr = "version",
        name = "X-Plane Version",
        default = VERSION_1100,
        items = [
            (VERSION_900,  "9.x", "9.x"),
            (VERSION_1000, "10.0x", "10.0x"),
            (VERSION_1010, "10.1x", "10.1x"),
            (VERSION_1040, "10.4x", "10.4x"),
            (VERSION_1050, "10.5x", "10.5x"),
            (VERSION_1100, "11.0x", "11.0x")
        ]
    )

    exportMode = bpy.props.EnumProperty(
        attr = "exportMode",
        name = "Export Mode",
        default = "layers",
        items = [
            (EXPORT_MODE_LAYERS, "Layers", "Allows to export an .obj file for each layer"),
            (EXPORT_MODE_ROOT_OBJECTS, "Root Objects", "Allows to export all objects below a root object into a single .obj file")
        ]
    )

    compositeTextures = bpy.props.BoolProperty(
        attr = "compositeTextures",
        name = "Compile Normal-Textures",
        description = "Will automatically create and use corrected normal textures",
        default = True
    )
    
    # This always represents the current version of the code,
    # or a deliberate build of it. It's values are configured
    # in __init__.py and xplane_config.py
    xplane2blender_ver = bpy.props.PointerProperty(
        name = "Current XPlane2Blender Version",
        description = "The current version of XPlane2Blender",
        type = XPlane2BlenderVersion
    )
    
    # This list of version histories the .blend file has encountered,
    # from the earliest
    xplane2blender_ver_history = bpy.props.CollectionProperty(
        name="XPlane2Blender History",
        description="Every version of XPlane2Blender this .blend file has been opened with",
        type=XPlane2BlenderVersion)

# Class: XPlaneObjectSettings
# Settings for Blender objects.
#
# Properties:
#   datarefs - Collection of <XPlaneDatarefs>. X-Plane Datarefs
#   bool depth - True if object will use depth culling.
#   customAttributes - Collection of <XPlaneCustomAttributes>. Custom X-Plane attributes
#   bool panel - True if object is part of the cockpit panel.
#   XPlaneManipulator manip - Manipulator settings.
#   bool lightLevel - True if object overrides default light levels.
#   float lightLevel_v1 - Light Level Value 1
#   float lightLevel_v2 - Light Level Value 2
#   string lightLevel_dataref - Light Level Dataref
class XPlaneObjectSettings(bpy.types.PropertyGroup):
    datarefs = bpy.props.CollectionProperty(
        attr = "datarefs",
        name = "X-Plane Datarefs",
        description = "X-Plane Datarefs",
        type = XPlaneDataref
    )

    customAttributes = bpy.props.CollectionProperty(
        attr = "customAttributes",
        name = "Custom X-Plane Attributes",
        description = "User defined attributes for the Object",
        type = XPlaneCustomAttribute
    )

    customAnimAttributes = bpy.props.CollectionProperty(
        attr = "customAnimAttributes",
        name = "Custom X-Plane Animation Attributes",
        description = "User defined attributes for animation of the Object",
        type = XPlaneCustomAttribute
    )

    manip = bpy.props.PointerProperty(
        attr = "manip",
        name = "Manipulator",
        description = "X-Plane Manipulator Settings",
        type = XPlaneManipulator
    )

    lod = bpy.props.BoolVectorProperty(
        name = "Levels Of Detail",
        description = "Define in wich LODs this object will be used. If none is checked it will be used in all",
        default = (False, False, False, False),
        size = MAX_LODS-1
    )

    override_weight = bpy.props.BoolProperty(
        name = "Override Weight",
        description = "If checked you can override the internal weight of the object. Heavier objects will be written later in OBJ",
        default = False
    )

    weight = bpy.props.IntProperty(
        name = "Weight",
        description = "Usual weights are: Meshes 0-8999, Lines 9000 - 9999, Lamps > = 10000",
        default = 0,
        min = 0
    )

    exportMeshValues = []
    while len(exportMeshValues) < 20:
        exportMeshValues.append(True)

    export_mesh = bpy.props.BoolVectorProperty(
        name = "Export Mesh in Layers",
        description = "If disabled only object's animations will be exported in the selected layers, but not the mesh itself",
        default = exportMeshValues,
        size = 20,
        subtype = 'LAYER')

    # v1000
    conditions = bpy.props.CollectionProperty(
        attr = "conditions",
        name = "Conditions",
        description = "Hide/show object depending on rendering settings",
        type = XPlaneCondition
    )

    isExportableRoot = bpy.props.BoolProperty(
        attr = 'isExportableRoot',
        name = 'Root Object',
        description = 'Activate to export this object and all its children into it\'s own .obj file',
        default = False
    )

    layer = bpy.props.PointerProperty(
        attr = "layer",
        name = "X-Plane Layer",
        description = "X-Plane Layer/File Settings",
        type = XPlaneLayer
    )

# Class: XPlaneBoneSettings
# Settings for Blender bones.
#
# Properties:
#   datarefs - Collection of <XPlaneDatarefs>. X-Plane Datarefs
class XPlaneBoneSettings(bpy.types.PropertyGroup):
    datarefs = bpy.props.CollectionProperty(
        attr = "datarefs",
        name = "X-Plane Datarefs",
        description = "X-Plane Datarefs",
        type = XPlaneDataref
    )

    customAttributes = bpy.props.CollectionProperty(
        attr = "customAttributes",
        name = "Custom X-Plane Attributes",
        description = "User defined attributes for the Object",
        type = XPlaneCustomAttribute
    )

    customAnimAttributes = bpy.props.CollectionProperty(
        attr = "customAnimAttributes",
        name = "Custom X-Plane Animation Attributes",
        description = "User defined attributes for animation of the Object",
        type = XPlaneCustomAttribute
    )

    override_weight = bpy.props.BoolProperty(
        name = "Override Weight",
        description = "If checked you can override the internal weight of the object. Heavier objects will be written later in OBJ",
        default = False
    )

    weight = bpy.props.IntProperty(
        name = "Weight",
        description = "Usual weights are: Meshes 0-8999, Lines 9000 - 9999, Lamps > = 10000",
        default = 0,
        min = 0
    )

def updateMaterialLitPreview(self, context):
    texture, textureLit = getColorAndLitTextureSlots(context.material)

    if texture and textureLit:
        factor = context.material.xplane.litFactor

        texture.diffuse_color_factor = 1 - factor
        textureLit.emit_factor = factor

# Class: XPlaneMaterialSettings
# Settings for Blender materials.
#
# Properties:
#   enum surfaceType - Surface type as defined in OBJ specs.
#   bool blend - True if the material uses alpha cutoff.
#   float blendRatio - Alpha cutoff ratio.
#   customAttributes - Collection of <XPlaneCustomAttributes>. Custom X-Plane attributes
class XPlaneMaterialSettings(bpy.types.PropertyGroup):
    draw = bpy.props.BoolProperty(
        attr = "draw",
        name = "Draw Linked Objects",
        description = "If turned off, objects with this material won't be drawn",
        default = True
    )

    surfaceType = bpy.props.EnumProperty(
        attr = 'surfaceType',
        name = 'Surface Type',
        description = 'Controls the bumpiness of material in X-Plane',
        default = 'none',
        items = [
            (SURFACE_TYPE_NONE,     "None",    "None"),
            (SURFACE_TYPE_WATER,    "Water",   "Water"),
            (SURFACE_TYPE_CONCRETE, "Concrete","Concrete"),
            (SURFACE_TYPE_ASPHALT,  "Asphalt", "Asphalt"),
            (SURFACE_TYPE_GRASS,    "Grass",   "Grass"),
            (SURFACE_TYPE_DIRT,     "Dirt",    "Dirt"),
            (SURFACE_TYPE_GRAVEL,   "Gravel",  "Gravel"),
            (SURFACE_TYPE_LAKEBED,  "Lakebed", "Lakebed"),
            (SURFACE_TYPE_SNOW,     "Snow",    "Snow"),
            (SURFACE_TYPE_SHOULDER, "Shoulder","Shoulder"),
            (SURFACE_TYPE_BLASTPAD, "Blastpad","Blastpad"),
        ]
    )

    deck = bpy.props.BoolProperty(
        name = "Deck",
        description = "Allows the user to fly under the surface",
        default = False
    )

    solid_camera = bpy.props.BoolProperty(
        name = "Camera Collision",
        description = "X-Plane's camera will be prevented from moving through objects with this material. Only allowed in Cockpit type exports",
        default = False
    )

    blend = bpy.props.BoolProperty(
        attr = "blend",
        name = "Use Alpha Cutoff",
        description = "If turned on the textures alpha channel will be used to cutoff areas above the Alpha cutoff ratio",
        default = False
    )

    __blend_v1000_items = [
            (BLEND_OFF, 'Alpha Cutoff', 'Textures alpha channel will be used to cutoff areas above the Alpha cutoff ratio'),
            (BLEND_ON, 'Alpha Blend', 'Textures alpha channel will blended'),
            (BLEND_SHADOW, 'Shadow', 'In shadow mode, shadows are not blended but primary drawing is')
        ]

    # v1000
    blend_v1000 = bpy.props.EnumProperty(
        attr = "blend_v1000",
        name = "Blend",
        description = "Controls texture alpha/blending",
        default = BLEND_ON,
        items = __blend_v1000_items
    )

    __blend_v1100_items = [(BLEND_GLASS, 'Blend Glass', 'The alpha channel of the albedo (day texture) will be used to create translucent rendering')]
    
    # v1100
    blend_v1100 = bpy.props.EnumProperty(
        attr = "blend_v1100",
        name = "Blend",
        description = "Controls texture alpha/blending",
        default = BLEND_ON,
        items = __blend_v1000_items + __blend_v1100_items
    )
    
    blendRatio = bpy.props.FloatProperty(
        attr = "blendRatio",
        name = "Alpha Cutoff Ratio",
        description = "Alpha levels in the texture below this level are rendered as fully transparent and alpha levels above this level are fully opaque",
        default = 0.5,
        step = 0.1,
        precision = 2,
        max = 1.0,
        min = 0.0
    )

    panel = bpy.props.BoolProperty(
        attr = "panel",
        name = "Part Of Cockpit Panel",
        description = "If checked this object will use the panel texture and will be clickable",
        default = False
    )

    cockpit_region = bpy.props.EnumProperty(
        attr = "cockpit_region",
        name = "Cockpit Region",
        description = "Cockpit region to use",
        default = "0",
        items = [
            ("0", "None", "None"),
            ("1", "1", "1"),
            ("2", "2", "2"),
            ("3", "3", "3"),
            ("4", "4", "4")
        ]
    )

    lightLevel = bpy.props.BoolProperty(
        attr = "lightLevel",
        name = "Override Light Level",
        description = "If checked values will change the brightness of the _LIT texture for the object. This overrides the sim's decision about object lighting",
        default = False
    )

    lightLevel_v1 = bpy.props.FloatProperty(
        attr = "lightLevel_v1",
        name = "Value 1",
        description = "Value 1 for light level",
        default = 0.0
    )

    lightLevel_v2 = bpy.props.FloatProperty(
        attr = "lightLevel_v2",
        name = "Value 2",
        description = "Value 2 for light level",
        default = 1.0
    )

    lightLevel_dataref = bpy.props.StringProperty(
        attr = "lightLevel_dataref",
        name = "Dataref",
        description = "The dataref is interpreted as a value between v1 and v2. Values outside v1 and v2 are clamped",
        default = ""
    )

    poly_os = bpy.props.IntProperty(
        name = "Polygon Offset",
        description = "Sets the polygon offset state. Leave at 0 for default behaviour",
        default = 0,
        step = 1,
        min = 0
    )

    # v1000
    conditions = bpy.props.CollectionProperty(
        attr = "conditions",
        name = "Conditions",
        description = "Hide/show objects with material depending on rendering settings",
        type = XPlaneCondition
    )

    customAttributes = bpy.props.CollectionProperty(
        attr = "customAttributes",
        name = "Custom X-Plane Material Attributes",
        description = "User defined material attributes for the X-Plane file",
        type = XPlaneCustomAttribute
    )

    litFactor = bpy.props.FloatProperty(
        attr = "litFactor",
        name = "Day-Night Preview Balance",
        description = "Adjusts 3D View's preview of day vs night texture",
        default = 0,
        min = 0,
        max = 1,
        step = 0.1,
        update = updateMaterialLitPreview
    )

    # v1000
    draped = bpy.props.BoolProperty(
        attr = "draped",
        name = "Draped",
        description = "Will perfectly match with the ground",
        default = False
    )

    # v1100
    normal_metalness = bpy.props.BoolProperty(
        attr = "normal_metalness",
        name = "Normal Metalness",
        description = "Blue channel will be used for base reflectance",
        default = False
        )
    

    # v1000 (draped only)
    bump_level = bpy.props.FloatProperty(
        attr = "bump_level",
        name = "Draped Bump Level",
        description = "Scales the Bump for draped geometry up or down",
        default = 1.0,
        min = -2.0,
        max = 2.0
    )

    # v1000 (only for instances)
    tint = bpy.props.BoolProperty(
        attr = "tint",
        name = "Tint", 
        description = "If active you can set the albedo and emissive tint",
        default = False
    )

    # v1000 (only for instances)
    tint_albedo = bpy.props.FloatProperty(
        attr = "tint_albedo",
        name = "Albedo",
        description = "Albedo tint. 0.0 no darkening, 1.0 total darkening",
        min = 0.0,
        max = 1.0,
        step = 1 / 255,
        default = 0.0
    )

    # v1000 (only for instances)
    tint_emissive = bpy.props.FloatProperty(
        attr = "tint_emissive",
        name = "Emissive",
        description = "Emissive tint. 0.0 no darkening, 1.0 total darkening",
        min = 0.0,
        max = 1.0,
        step = 1 / 255,
        default = 0.0
    )

# Class: XPlaneLampSettings
# Settings for Blender lamps.
#
# Properties:
#   enum type - Light type as defined in OBJ specs.
#   string name - Light name, if "type" is 'named'.
#   string params - Light params, if "type" is 'param'.
#   float size - Light size, if "type" is 'custom'.
#   string dataref - Dataref driving the light, if "type" is 'custom'.
#   customAttributes - Collection of <XPlaneCustomAttributes>. Custom X-Plane attributes
class XPlaneLampSettings(bpy.types.PropertyGroup):
    # TODO: deprecate named, flashing, pulising, strobe, traffic lights in v3.4
    type = bpy.props.EnumProperty(
        attr = "type",
        name = "Type",
        description = "Defines the type of the light in X-Plane",
        default = LIGHT_DEFAULT,
        items = [
                (LIGHT_DEFAULT,  "Default",                     "Default"),
                (LIGHT_FLASHING, "Flashing" + " (deprecated)",  "Flashing" + " (deprecated)"),
                (LIGHT_PULSING,  "Pulsing"  + " (deprecated)",  "Pulsing"  + " (deprecated)"),
                (LIGHT_STROBE,   "Strobe"   + " (deprecated)",  "Strobe"   + " (deprecated)"),
                (LIGHT_TRAFFIC,  "Traffic"  + " (deprecated)",  "Traffic"  + " (deprecated)"),
                (LIGHT_NAMED,    "Named",                       "Named"),
                (LIGHT_CUSTOM,   "Custom",                      "Custom"),
                (LIGHT_PARAM,    "Param",                       "Param")
        ]
    )

    name = bpy.props.StringProperty(
        attr = "name",
        name = 'Name',
        description = "Named lights allow a light to be created based on pre-existing types",
        default = ""
    )

    params = bpy.props.StringProperty(
        attr = "params",
        name = 'Parameters',
        description = "The additional parameters vary in number and definition based on the particular parameterized light selected",
        default = ""
    )

    size = bpy.props.FloatProperty(
        attr = "size",
        name = 'Size',
        description = "The size of the light - this is not in a particular unit (like meters), but larger numbers produce bigger brighter lights",
        default = 1.0,
        min = 0.0
    )

    dataref = bpy.props.StringProperty(
        attr = "dataref",
        name = 'Dataref',
        description = "A X-Plane Dataref",
        default = ""
    )

    uv = bpy.props.FloatVectorProperty(
        name = "Texture Coordinates",
        description = "The texture coordinates in the following order: left,top,right,bottom (fractions from 0 to 1)",
        default = (0.0, 0.0, 1.0, 1.0),
        min = 0.0,
        max = 1.0,
        precision = 3,
        size = 4
    )

    customAttributes = bpy.props.CollectionProperty(
        attr = "customAttributes",
        name = "Custom X-Plane Light Attributes",
        description = "User defined light attributes for the X-Plane file",
        type = XPlaneCustomAttribute
    )


# Function: addXPlaneRNA
# Registers all properties.
def addXPlaneRNA():
    # basic classes
    bpy.utils.register_class(XPlane2BlenderVersion)
    bpy.utils.register_class(XPlaneCustomAttribute)
    bpy.utils.register_class(XPlaneDataref)
    bpy.utils.register_class(XPlaneCondition)
    #bpy.utils.register_class(XPlaneDatarefSearch)
    bpy.utils.register_class(XPlaneExportPathDirective)
    bpy.utils.register_class(XPlaneManipulator)
    bpy.utils.register_class(XPlaneCockpitRegion)
    bpy.utils.register_class(XPlaneLOD)

    # complex classes, depending on basic classes
    bpy.utils.register_class(XPlaneLayer)
    bpy.utils.register_class(XPlaneObjectSettings)
    bpy.utils.register_class(XPlaneBoneSettings)
    bpy.utils.register_class(XPlaneMaterialSettings)
    bpy.utils.register_class(XPlaneLampSettings)
    bpy.utils.register_class(XPlaneSceneSettings)

    bpy.types.Scene.xplane = bpy.props.PointerProperty(
        attr = "xplane",
        type = XPlaneSceneSettings,
        name = "XPlane",
        description = "X-Plane Scene Settings"
    )
    bpy.types.Object.xplane = bpy.props.PointerProperty(
        attr = "xplane",
        type = XPlaneObjectSettings,
        name = "XPlane",
        description = "X-Plane Object Settings"
    )
    bpy.types.Bone.xplane = bpy.props.PointerProperty(
        attr = "xplane",
        type = XPlaneBoneSettings,
        name = "XPlane",
        description = "X-Plane Bone Settings"
    )
    bpy.types.Material.xplane = bpy.props.PointerProperty(
        attr = "xplane",
        type = XPlaneMaterialSettings,
        name = "XPlane",
        description = "X-Plane Material Settings"
    )
    bpy.types.Lamp.xplane = bpy.props.PointerProperty(
        attr = "xplane",
        type = XPlaneLampSettings,
        name = "XPlane",
        description = "X-Plane Lamp Settings"
    )

# Function: removeXPlaneRNA
# Unregisters all properties.
def removeXPlaneRNA():
    # complex classes, depending on basic classes
    bpy.utils.unregister_class(XPlaneObjectSettings)
    bpy.utils.unregister_class(XPlaneBoneSettings)
    bpy.utils.unregister_class(XPlaneMaterialSettings)
    bpy.utils.unregister_class(XPlaneLampSettings)
    bpy.utils.unregister_class(XPlaneSceneSettings)
    bpy.utils.unregister_class(XPlaneLayer)

    # basic classes
    bpy.utils.unregister_class(XPlane2BlenderVersion)
    bpy.utils.unregister_class(XPlaneCustomAttribute)
    bpy.utils.unregister_class(XPlaneDataref)
    #bpy.utils.unregister_class(XPlaneDatarefSearch)
    bpy.utils.unregister_class(XPlaneExportPathDirective)
    bpy.utils.unregister_class(XPlaneManipulator)
    bpy.utils.unregister_class(XPlaneCockpitRegion)
    bpy.utils.unregister_class(XPlaneLOD)
