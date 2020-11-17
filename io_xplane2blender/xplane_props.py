"""
Defines X-Plane Properties attached to regular Blender data types.
"""

from typing import List

import bpy

import io_xplane2blender
from io_xplane2blender import xplane_config, xplane_constants, xplane_helpers
from io_xplane2blender.xplane_constants import VERSION_1100

from .xplane_constants import *

"""
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

- Make sure to increment the CURRENT_DATA_MODEL_VERSION number in xplane_config

- This file contains 99% of the properties. xplane2blender is set in xplane_updater.py and now we're stuck with it there

- Properties use snake_case

- Name is in the form of "Title Case Always", description is "Sentence case, no period". Don't be lazy and just copy and paste the constant name for all three columns.
A good deal of time was spent making the UI look pretty for 3.4.0 so please don't undo that over time

- Properties and classes must be in alphabetical order, starting from the top, including if they're exceptionally related.
Classes may be out of order if needed to be declared out of order. Try to make everything as alphabetically ordered as possible

Take the existing class XPlaneExampleClass with properties
currently listed as:

- b_ex
- a_ex
- d_ex
- e_ex
- f_ex

A new property called g_ex would go after b_ex, not f_ex!
This is true even if it seemed like a natural fit to be paired with something else.

<rant>
Why? Because attempting to keep properties together as
a set of "common uses" or "as ordered as in the UI" gets messy quick
making it more confusing later as things are in a pseudo-arbitrary layout.

In this way at least the top of every class will be organized,
order slowly coming into fruition by way of
undebatable alphabetical listing.
</rant>

- If you've actually read this far, congratulations! You get a cookie!

- For defaults, use the constants, not redundantly copying their values

- Don't forget to add your new prop to addXPlaneRNA and removeXPlaneRNA!

- Tip: If you've invented a new PropertyGroup, you must wrap it in a PointerProperty or use it in a CollectionProperty
"""


# Internal variable to enable and disable the ability to update the value of XPlane2Blender's properties
# DO NOT CHANGE OUTSIDE OF safe_set_version_data!
_version_safety_off = False


class XPlane2BlenderVersion(bpy.types.PropertyGroup):
    """
    Contains useful methods for getting information about the
    version and build number of XPlane2Blender

    Names are usually in the format of
    major.minor.release-(alpha|beta|dev|leg|rc)\.[0-9]+)\+\d+\.(YYYYMMDDHHMMSS)
    """

    # Guards against being updated without being validated
    def update_version_property(self, context):
        if _version_safety_off is False:
            raise Exception(
                "Do not modify version property outside of safe_set_version_data!"
            )
        return None

    # Property: addon_version
    #
    # Tuple of Blender addon version, (major, minor, revision)
    addon_version: bpy.props.IntVectorProperty(
        name="XPlane2Blender Addon Version",
        description="The version of the addon (also found in it's addon information)",
        default=xplane_config.CURRENT_ADDON_VERSION,
        update=update_version_property,
        size=3,
    )

    # Property: build_type
    #
    # The type of build this is, always a value in BUILD_TYPES
    build_type: bpy.props.StringProperty(
        name="Build Type",
        description="Which iteration in the development cycle of the chosen build type we're at",
        default=xplane_config.CURRENT_BUILD_TYPE,
        update=update_version_property,
    )

    # Property: build_type_version
    #
    # The iteration in the build cycle, 0 for dev and legacy, > 0 for everything else
    build_type_version: bpy.props.IntProperty(
        name="Build Type Version",
        description="Which iteration in the development cycle of the chosen build type we're at",
        default=xplane_config.CURRENT_BUILD_TYPE_VERSION,
        update=update_version_property,
    )

    # Property: data_model_version
    #
    # The version of the data model, tracked separately. Always incrementing.
    data_model_version: bpy.props.IntProperty(
        name="Data Model Version",
        description="Version of the data model (constants,props, and updater functionality) this version of the addon is. Always incrementing on changes",
        default=xplane_config.CURRENT_DATA_MODEL_VERSION,
        update=update_version_property,
    )

    # Property: build_number
    #
    # If run as a public facing build, this value will be replaced
    # with the YYYYMMSSHHMMSS at build creation date in UTC.
    # Otherwise, it defaults to xplane_constants.BUILD_NUMBER_NONE
    build_number: bpy.props.StringProperty(
        name="Build Number",
        description="Build number of XPlane2Blender. If xplane_constants.BUILD_NUMBER_NONE, this is a development or legacy build!",
        default=xplane_config.CURRENT_BUILD_NUMBER,
        update=update_version_property,
    )

    # Method: safe_set_version_data
    #
    # The only way to change version data! Use responsibly for suffer the Dragons described above!
    # Returns True if it succeeded, or False if it failed due to invalid data. debug_add_to_history only works
    # when the data is valid
    #
    # Passing nothing in results in no change
    def safe_set_version_data(
        self,
        addon_version=None,
        build_type=None,
        build_type_version=None,
        data_model_version=None,
        build_number=None,
        debug_add_to_history=False,
    ):
        if addon_version is None:
            addon_version = self.addon_version
        if build_type is None:
            build_type = self.build_type
        if build_type_version is None:
            build_type_version = self.build_type_version
        if data_model_version is None:
            data_model_version = self.data_model_version
        if build_number is None:
            build_number = self.build_number

        if xplane_helpers.VerStruct(
            addon_version,
            build_type,
            build_type_version,
            data_model_version,
            build_number,
        ).is_valid():
            global _version_safety_off
            _version_safety_off = True
            self.addon_version = addon_version
            self.build_type = build_type
            self.build_type_version = build_type_version
            self.data_model_version = data_model_version
            self.build_number = build_number
            _version_safety_off = False
            if debug_add_to_history:
                xplane_helpers.VerStruct.add_to_version_history(bpy.context.scene, self)
            return True
        else:
            return False

    # Method: make_struct
    #
    # Make a VerStruct version of itself
    def make_struct(self):
        return xplane_helpers.VerStruct(
            self.addon_version,
            self.build_type,
            self.build_type_version,
            self.data_model_version,
            self.build_number,
        )

    # Addon string in the form of "m.m.r", no parenthesis
    def addon_version_clean_str(self):
        return ".".join(map(str, self.addon_version))

    # Method: __repr__
    #
    # repr and repr of VerStruct are the same. It is used as a key for scene.xplane.xplane2blender_ver_history
    def __repr__(self) -> str:
        return "(%s, %s, %s, %s, %s)" % (
            "(" + ",".join(map(str, self.addon_version)) + ")",
            "'" + str(self.build_type) + "'",
            str(self.build_type_version),
            str(self.data_model_version),
            "'" + str(self.build_number) + "'",
        )

    # Method: __str__
    #
    # str and str of VerStruct are the same. It is used for printing to the user
    def __str__(self) -> str:
        return "%s-%s.%s+%s.%s" % (
            ".".join(map(str, self.addon_version)),
            self.build_type,
            self.build_type_version,
            self.data_model_version,
            self.build_number,
        )


# fmt: off
class XPlaneAxisDetentRange(bpy.types.PropertyGroup):
    start: bpy.props.FloatProperty(
            name = "Start",
            description = "Start value (from Dataref 1) of the detent region",
            default=0.0,
            precision = 3)
    end: bpy.props.FloatProperty(
            name = "End",
            description = "End value (from Dataref 1) of the detent region",
            default=0.0,
            precision = 3)
    height: bpy.props.FloatProperty(
            name = "Height",
            description = "The height (in units of Dataref 2) the user must drag to overcome the detent",
            default=0.0,
            precision = 3)

    def __str__(self):
       return "({0},{1},{2})".format(self.start,self.end,self.height)

# Class: XPlaneCustomAttribute
# A custom attribute.
#
# Properties:
#   string name - Name of the attribute
#   string value - Value of the attribute
#   string reset - Reseter of the attribute
class XPlaneCustomAttribute(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(
        name = "Name",
        description = "Name",
        default = ""
    )

    value: bpy.props.StringProperty(
        name = "Value",
        description = "Value",
        default = ""
    )

    reset: bpy.props.StringProperty(
        name = "Reset",
        description = "Reset",
        default = ""
    )

    weight: bpy.props.IntProperty(
        name = "Weight",
        description = "The more weight an attribute has the later it gets written in the OBJ",
        default = 0,
        min = 0
    )
# fmt: on


class ListItemCommand(bpy.types.PropertyGroup):
    """
    This is essentially a copy of xplane_commands_txt_parser.CommandInfoStruct's members
    """

    command: bpy.props.StringProperty(
        name="Command For Search List",
        description="A command path in the command search window. Comes from a Commands definitions file",
    )

    command_description: bpy.props.StringProperty(
        name="Command Description For Search List",
        description="Indicates the type, shown in a column in the commands search window. Comes from a Commands definitions file",
    )


class ListItemDataref(bpy.types.PropertyGroup):
    """
    This is essentially a copy of xplane_datarefs_txt_parser.DatarefInfoStruct's members
    """

    dataref_path: bpy.props.StringProperty(
        name="Dataref Path Data For Search List",
        description="A dataref path in the dataref search window. Comes from a Datarefs definitions file",
    )

    dataref_type: bpy.props.StringProperty(
        name="Dataref Type Data For Search List",
        description="Indicates the type, shown in a column in the datarefs search window. Comes from a Datarefs definitions file",
    )

    dataref_is_writable: bpy.props.StringProperty(
        name="Dataref 'Is Writable' Data For Search List", description="A "
    )

    dataref_units: bpy.props.StringProperty(name="", description="")

    dataref_description: bpy.props.StringProperty(name="", description="")


class XPlaneCommandSearchWindow(bpy.types.PropertyGroup):
    # This is only set through a CommandSeachToggle's action.
    # It should be the full path to the command property to change,
    # as if it were being put into the Python console.
    # For instance: "bpy.context.active_object.xplane.commands[0].path"
    command_prop_dest: bpy.props.StringProperty(
        default="",
        name="Current Command Property To Change",
        description="The destination command property, starting with 'bpy.context...'",
    )

    def onclick_command(self, context):
        """
        This method is called when the template_list uilist writes to the current selected index as the user selects.
        We dig out our stashed search info, write the command, and clear the current search, zapping out the UI.
        """

        xplane = context.scene.xplane
        command_prop_dest = xplane.command_search_window_state.command_prop_dest
        commands_search_list = xplane.command_search_window_state.command_search_list
        commands_search_list_idx = (
            xplane.command_search_window_state.command_search_list_idx
        )
        command = commands_search_list[commands_search_list_idx].command
        assert (
            command_prop_dest != ""
        ), "should not be able to click button when search window is supposed to be closed"

        def getattr_recursive(obj, names):
            """This automatically expands [] operators"""
            if len(names) == 1:
                if "[" in names[0]:
                    name = names[0]
                    collection_name = name[: name.find("[")]
                    index = name[name.find("[") + 1 : -1]
                    return getattr(obj, collection_name)[int(index)]
                else:
                    return getattr(obj, names[0])
            else:
                if "[" in names[0]:
                    name = names[0]
                    collection_name = name[: name.find("[")]
                    index = name[name.find("[") + 1 : -1]
                    obj = getattr(obj, collection_name)[int(index)]
                else:
                    obj = getattr(obj, names[0])
                return getattr_recursive(obj, names[1:])

        components = command_prop_dest.split(".")
        assert components[0] == "bpy"
        setattr(getattr_recursive(bpy, components[1:-1]), components[-1], command)
        xplane.command_search_window_state.command_prop_dest = ""

    command_search_list: bpy.props.CollectionProperty(type=ListItemCommand)
    command_search_list_idx: bpy.props.IntProperty(update=onclick_command)


class XPlaneDatarefSearchWindow(bpy.types.PropertyGroup):
    # This is only set through a DatarefSeachToggle's action.
    # It should be the full path to the dataref property to change,
    # as if it were being put into the Python console.
    # For instance: "bpy.context.active_object.xplane.datarefs[0].path"
    dataref_prop_dest: bpy.props.StringProperty(
        default="",
        name="Current Dataref Property To Change",
        description="The destination dataref property, starting with 'bpy.context...'",
    )

    def onclick_dataref(self, context):
        """
        This method is called when the template_list uilist writes to the current selected index as the user selects.
        We dig out our stashed search info, write the dataref, and clear the current search, zapping out the UI.
        """

        xplane = context.scene.xplane
        dataref_prop_dest = xplane.dataref_search_window_state.dataref_prop_dest
        datarefs_search_list = xplane.dataref_search_window_state.dataref_search_list
        datarefs_search_list_idx = (
            xplane.dataref_search_window_state.dataref_search_list_idx
        )
        path = datarefs_search_list[datarefs_search_list_idx].dataref_path
        assert (
            dataref_prop_dest != ""
        ), "should not be able to click button when search window is supposed to be closed"

        def getattr_recursive(obj, names):
            """This automatically expands [] operators"""
            if len(names) == 1:
                if "[" in names[0]:
                    name = names[0]
                    collection_name = name[: name.find("[")]
                    index = name[name.find("[") + 1 : -1]
                    return getattr(obj, collection_name)[int(index)]
                else:
                    return getattr(obj, names[0])
            else:
                if "[" in names[0]:
                    name = names[0]
                    collection_name = name[: name.find("[")]
                    index = name[name.find("[") + 1 : -1]
                    obj = getattr(obj, collection_name)[int(index)]
                else:
                    obj = getattr(obj, names[0])
                return getattr_recursive(obj, names[1:])

        components = dataref_prop_dest.split(".")
        assert components[0] == "bpy"
        setattr(getattr_recursive(bpy, components[1:-1]), components[-1], path)
        xplane.dataref_search_window_state.dataref_prop_dest = ""

    dataref_search_list: bpy.props.CollectionProperty(type=ListItemDataref)
    dataref_search_list_idx: bpy.props.IntProperty(update=onclick_dataref)


# fmt: off
class XPlaneExportPathDirective(bpy.types.PropertyGroup):
    export_path: bpy.props.StringProperty(
        name = "Special library.txt Directive",
        description="Special Laminar Research only directive for library.txt maintenance",
    )


class XPlaneEmitter(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(
        name = "Emitter Name",
        description = "The name of the emitter, coming from the .pss file"
    )

    index: bpy.props.IntProperty(
        name = "Emitter Index",
        description = "The index in the emitter's array",
        min = 0
    )

    index_enabled: bpy.props.BoolProperty(
        name = "Emitter Index Enabled",
        description = "Enables the emitter array index",
        default=False
    )

class XPlaneMagnet(bpy.types.PropertyGroup):
    debug_name: bpy.props.StringProperty(
        name="Debug Name",
        description="Human readable name for debugging purposes"
    )

    magnet_type_is_xpad: bpy.props.BoolProperty(
        name="xpad",
        description="Sets the type to include 'xpad'"
    )

    magnet_type_is_flashlight: bpy.props.BoolProperty(
        name="flashlight",
        description="Sets the type to include 'flashlight'"
    )


class XPlaneEmpty(bpy.types.PropertyGroup):
    emitter_props: bpy.props.PointerProperty(
        name="Emitter Settings",
        description="Settings for emitter, if special type is an Emitter",
        type=XPlaneEmitter
    )

    magnet_props: bpy.props.PointerProperty(
        name="Magnet Settings",
        description="Settings for magnet, if special type is Magnet",
        type=XPlaneMagnet
    )

    special_type: bpy.props.EnumProperty(
        name="Empty Special Type",
        description="Type XPlane2Blender item this is",
        items= [
            (EMPTY_USAGE_NONE,             "None",             "Empty has no special use", 0),
            (EMPTY_USAGE_EMITTER_PARTICLE, "Particle Emitter", "A particle emitter", 1),
            #(EMPTY_USAGE_EMITTER_SOUND,   "Sound Emitter",    "Empty represents a sound emitter", 2), #One day...
            (EMPTY_USAGE_MAGNET,           "Magnet",           "A mounting point on a yoke where a VR tablet can be attached", 3)
        ]
    )


# Class: XPlaneDataref
# A X-Plane Dataref
#
# Properties:
#   string path - Dataref path
#   float value - Dataref value (can be keyframed)
#   int loop - Loop amount of dataref animation.
class XPlaneDataref(bpy.types.PropertyGroup):
    path: bpy.props.StringProperty(
        name = "Dataref Path",
        description = "Dataref Path",
        default = ""
    )

    value: bpy.props.FloatProperty(
        name = "Value",
        description = "Value",
        default = 0.0,
        precision = 6
    )

    loop: bpy.props.FloatProperty(
        name = "Loop Animation Every",
        description = "Loop amount of animation, useful for ever increasing Datarefs. A value of 0 will ignore this setting",
        min = 0.0,
        precision = 3
    )

    anim_type: bpy.props.EnumProperty(
        name = "Animation Type",
        description = "Type of animation this Dataref will use",
        default = ANIM_TYPE_TRANSFORM,
        items = [
            (ANIM_TYPE_TRANSFORM, "Transformation", "Transformation"),
            (ANIM_TYPE_SHOW, "Show", "Show"),
            (ANIM_TYPE_HIDE, "Hide", "Hide")
        ]
    )

    show_hide_v1: bpy.props.FloatProperty(
        name = "Value 1",
        description = "Show/Hide value 1",
        default = 0.0,
        precision = 3
    )

    show_hide_v2: bpy.props.FloatProperty(
        name = "Value 2",
        description = "Show/Hide value 2",
        default = 0.0,
        precision = 3
    )


# Class: XPlaneCondition
# A custom attribute.
#
# Properties:
#   string variable - Condition variable
#   string value - Value of the variable
#   string operator - Conditional operator to use
class XPlaneCondition(bpy.types.PropertyGroup):
    variable: bpy.props.EnumProperty(
        name = "Variable",
        description = "Variable",
        default = CONDITION_GLOBAL_LIGHTING,
        items = [
            (CONDITION_GLOBAL_LIGHTING, 'HDR', 'HDR mode On/Off'),
            (CONDITION_GLOBAL_SHADOWS, 'Global Shadows', 'Global shadows On/Off'),
            (CONDITION_VERSION10, 'Version 10.x', 'Always "On", as V9 does not support conditions')
        ]
    )

    value: bpy.props.BoolProperty(
        name = "Must Be On",
        description = "On/Off",
        default = True
    )

# Class: XPlaneManipulatorSettings
# A X-Plane manipulator settings
#
# Properties:
#   bool enabled - True if object is a manipulator
#   enum type - Manipulator types as defined in OBJ specs.
#   string tooltip - Manipulator Tooltip
#   enum cursor - Manipulator cursors as defined in OBJ specs.

#   float dx - X-Drag axis length
#   float dy - Y-Drag axis length
#   float dz - Z-Drag axis length
#
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
class XPlaneManipulatorSettings(bpy.types.PropertyGroup):
    autodetect_datarefs: bpy.props.BoolProperty(
        name = "Autodetect Datarefs",
        description = "If checked, dataref(s) for this manipulator will be taken from its mesh's animations",
        default = True
        )

    #This is meant for making old manipulator types smarter, not new manipulator types
    autodetect_settings_opt_in: bpy.props.BoolProperty(
        name = "Autodetect Settings",
        description = "Use new algorithms to autodetect certain manipulator settings from animation data",
        default = False
    )

    axis_detent_ranges: bpy.props.CollectionProperty(
        name = "Axis Detent Range",
        description = "The ranges where a drag rotate manipulator can move freely, and what heights must be overcome to enter each range",
        type=XPlaneAxisDetentRange
    )

    enabled: bpy.props.BoolProperty(
        name = "Manipulator",
        description = "If checked, this object will be treated as a manipulator",
        default = False
    )


    def get_manip_types_for_this_version(self,context):
        type_items = [
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
            (MANIP_AXIS_SWITCH_LEFT_RIGHT,    "Axis Switch Left Right (v10.50)",    "Axis Switch Left Right (requires at least v10.50)"),
            (MANIP_AXIS_KNOB, "Axis Knob (v10.50)", "Axis Knob (requires at least v10.50)")
        ]

        type_v1110_items = [
            (MANIP_DRAG_AXIS_DETENT,           "Drag Axis With Detents",      "Drag Axis With Detents (requires at least v11.10)"),
            (MANIP_COMMAND_KNOB2,              "Command Knob 2",              "Command Knob 2 (requires at least v11.10)"),
            (MANIP_COMMAND_SWITCH_UP_DOWN2,    "Command Switch Up Down 2",    "Command Switch Up Down 2 (requires at least v11.10)"),
            (MANIP_COMMAND_SWITCH_LEFT_RIGHT2, "Command Switch Left Right 2", "Command Switch Left Right 2 (requires at least v11.10)"),
            (MANIP_DRAG_ROTATE,                "Drag Rotate",                 "Drag Rotate (requires at least v11.10)"),
            (MANIP_DRAG_ROTATE_DETENT,         "Drag Rotate With Detents",    "Drag Rotate With Detents (requires at least v11.10)")
        ]

        xplane_version = int(bpy.context.scene.xplane.version)
        if xplane_version >= int(VERSION_1110):
            return type_items + type_v1110_items
        else:
            return type_items

    type: bpy.props.EnumProperty(
        name = "Manipulator Type",
        description = "The type of the manipulator",
        items = get_manip_types_for_this_version

    )

    tooltip: bpy.props.StringProperty(
        name = "Manipulator Tooltip",
        description = "The tooltip will be displayed when hovering over the object",
        default = ""
    )

    cursor: bpy.props.EnumProperty(
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

    dx: bpy.props.FloatProperty(
        name = "Drag X",
        description = "X-Drag axis length",
        default = 0.0,
        precision = 3
    )

    dy: bpy.props.FloatProperty(
        name = "Drag Y",
        description = "Y-Drag axis length",
        default = 0.0,
        precision = 3
    )

    dz: bpy.props.FloatProperty(
        name = "Drag Z",
        description = "Z-Drag axis length",
        default = 0.0,
        precision = 3
    )

    v1: bpy.props.FloatProperty(
        name = "Value 1",
        description = "Value 1",
        default = 0.0,
        precision = 3
    )

    v2: bpy.props.FloatProperty(
        name = "Value 2",
        description = "Value 2",
        default = 0.0,
        precision = 3
    )

    v1_min: bpy.props.FloatProperty(
        name = "Value 1 Min",
        description = "Value 1 min",
        default = 0.0,
        precision = 3
    )

    v1_max: bpy.props.FloatProperty(
        name = "Value 1 Max",
        description = "Value 1 max",
        default = 0.0,
        precision = 3
    )

    v2_min: bpy.props.FloatProperty(
        name = "Value 2 Min",
        description = "Value 2 min",
        default = 0.0,
        precision = 3
    )

    v2_max: bpy.props.FloatProperty(
        name = "Value 2 Max",
        description = "Value 2 max",
        default = 0.0,
        precision = 3
    )

    v_down: bpy.props.FloatProperty(
        name = "Value On Mouse Down",
        description = "Value to set dataref on mouse down",
        default = 0.0,
        precision = 3
    )

    v_up: bpy.props.FloatProperty(
        name = "Value On Mouse Up",
        description = "Value to set dataref on mouse up",
        default = 0.0,
        precision = 3
    )

    v_hold: bpy.props.FloatProperty(
        name = "Value On Mouse Hold",
        description = "Value to set dataref on mouse hold",
        default = 0.0,
        precision = 3
    )

    v_on: bpy.props.FloatProperty(
        name = "On Value",
        description = "On value",
        default = 0.0,
        precision = 3
    )

    v_off: bpy.props.FloatProperty(
        name = "Off Value",
        description = "Off value",
        default = 0.0,
        precision = 3
    )

    command: bpy.props.StringProperty(
        name = "Command",
        description = "The command to fire when manipulator is used",
        default = ""
    )

    positive_command: bpy.props.StringProperty(
        name = "Positive Command",
        description = "Positive command",
        default = ""
    )

    negative_command: bpy.props.StringProperty(
        name = "Negative Command",
        description = "Negative command",
        default = ""
    )

    dataref1: bpy.props.StringProperty(
        name = "Dataref 1",
        description = "Dataref 1",
        default = "")

    dataref2: bpy.props.StringProperty(
        name = "Dataref 2",
        description = "Dataref 2",
        default = ""
    )

    step: bpy.props.FloatProperty(
        name = "Step",
        description = "Dataref increment",
        default = 1.0,
        precision = 3
    )

    click_step: bpy.props.FloatProperty(
        name = "Click Step",
        description = "Value change on click",
        default = 0.0,
        precision = 3
    )

    hold_step: bpy.props.FloatProperty(
        name = "Hold Step",
        description = "Value change on hold",
        default = 0.0,
        precision = 3
    )

    wheel_delta: bpy.props.FloatProperty(
        name = "Wheel Delta",
        description = "Value change on mouse wheel tick",
        default = 0.0,
        precision = 3
    )

    exp: bpy.props.FloatProperty(
        name = "Exp",
        description = "Power of an exponential curve that controls the speed at which the dataref changes. Higher numbers cause a more “non-linear” response, where small drags are very precise and large drags are very fast",
        default = 1.0,
        precision = 3
    )

    def get_effective_type_desc(self) -> str:
        '''
        The description returned will the same as in the UI
        '''
        items = xplane_props.XPlaneManipulatorSettings.bl_rna.properties['type'].enum_items
        return next(filter(lambda item: item[0] == self.type, items))[2]#.description


    def get_effective_type_name(self) -> str:
        '''
        The name returned will the same as in the UI
        '''
        items = self.get_manip_types_for_this_version(None)
        return next(filter(lambda item: item[0] == self.type, items))[1]#.name


# Class: XPlaneCockpitRegion
# Defines settings for a cockpit region.
#
# Properties:
#   int top - BAD NAME ALERT it should have been called bottom! Bottom position of the region in px
#   int left - left position of the region in px
#   int width - width of the region in powers of 2
#   int height - height of the region in powers of 2
class XPlaneCockpitRegion(bpy.types.PropertyGroup):
    expanded: bpy.props.BoolProperty(
        name = "Expanded",
        description = "Toggle this cockpit region settings visibility",
        default = False
    )

    # BAD NAME ALERT: Should have been called "bottom"
    # One day we'll have nothing better to do in life than fix this
    # see #416
    top: bpy.props.IntProperty(
        name = "Bottom",
        description = "Bottom of cockpit region",
        default = 0,
        min = 0,
        max = 2048
    )

    left: bpy.props.IntProperty(
        name = "Left",
        description = "Left of cockpit region",
        default = 0,
        min = 0,
        max = 2048
    )

    width: bpy.props.IntProperty(
        name = "Width",
        description = "Width of cockpit region in powers of 2",
        default = 1,
        min = 1,
        max = 11
    )

    height: bpy.props.IntProperty(
        name = "Height",
        description = "Height of cockpit region in powers of 2",
        default = 1,
        min = 1,
        max = 11
    )

class XPlaneLOD(bpy.types.PropertyGroup):
    expanded: bpy.props.BoolProperty(
        name = "Expanded",
        description = "Toggle this LOD settings visibility",
        default = False
    )

    near: bpy.props.IntProperty(
        name = "Near",
        description = "Near distance (inclusive) in meters",
        default = 0,
        min = 0
    )

    far: bpy.props.IntProperty(
        name = "Far",
        description = "Far distance (exclusive) in meters",
        default = 0,
        min = 0
    )

    def __str__(self)->str:
        return f"({self.near}, {self.far})"

class XPlaneLayer(bpy.types.PropertyGroup):
    """
    Defines settings for an OBJ file. Is was formerly tied to
    Blender 3D-View Layers, but now is for Roots
    """

    """
    In case something removes lods or cockpit regions in Blender
    via Python after load, we need to make sure users can, even accidentally,
    make it come back. We solve this with an update function on the props.

    Either they change lods or cockpits trying to figure out what happened
    or they'll reload the file and the problem will be (hopefully solved)
    """
    def update_cockpit_regions(self, context)->None:
        # Avoids the need for operators to increase and decrease the size of self.cockpit_region
        while len(self.cockpit_region) < xplane_constants.MAX_COCKPIT_REGIONS:
            self.cockpit_region.add()
        return None

    def update_lods(self, context):
        # Avoids the need for operators to increase and decrease the size of self.lods
        #MAX_LODS also counts "None", so we have to subtract by 1
        while len(self.lod) < xplane_constants.MAX_LODS - 1:
            self.lod.add()

        return None

    blend_glass: bpy.props.BoolProperty(
        name = "Blend Glass",
        description = "The alpha channel of the albedo (day texture) will be used to create translucent rendering",
        default = False
    )

    cockpit_panel_mode: bpy.props.EnumProperty(
        name="Panel Texture Mode",
        description="Panel Texture Mode, affects all Materials using Panel",
        items=[
            (PANEL_COCKPIT, "Default", "Full Panel Texture: Albedo, Lit, and Normal"),
            (PANEL_COCKPIT_LIT_ONLY, "Emissive Panel Texture Only", "Only emissive panel texture will be dynamic. Great for computer displays"),
            (PANEL_COCKPIT_REGION, "Regions", "Uses regions of panel texture"),
        ],
        default=PANEL_COCKPIT,
    )

    expanded: bpy.props.BoolProperty(
        name = "Expanded",
        description = "Toggles the layer settings visibility",
        default = False
    )

    export_path_directives: bpy.props.CollectionProperty(
        name = "Export Directives for OBJ",
        description = "A collection of export paths intended for an OBJ's EXPORT directives",
        type = XPlaneExportPathDirective
    )

    normal_metalness: bpy.props.BoolProperty(
        name = "Normal Metalness",
        description = "The normal map's blue channel will be used for base reflectance",
        default = False
    )

    normal_metalness_draped: bpy.props.BoolProperty(
        name = "Normal Metalness (Draped)",
        description = "The draped normal map's blue channel will be used for base reflectance",
        default = False
    )

    particle_system_file: bpy.props.StringProperty(
        name = "Particle System Definition File",
        description = "Relative file path to a .pss that defines particles",
        subtype = "FILE_PATH"
    )

    # v1000 (only for instances)
    tint: bpy.props.BoolProperty(
        name = "Tint",
        description = "If active you can set the albedo and emissive tint",
        default = False
    )

    # v1000 (only for instances)
    tint_albedo: bpy.props.FloatProperty(
        name = "Albedo Tint",
        description = "Albedo tint. 0.0 is no darkening, 1.0 is total darkening",
        min = 0.0,
        max = 1.0,
        step = .01,
        default = 0.0,
        precision = 2
    )

    # v1000 (only for instances)
    tint_emissive: bpy.props.FloatProperty(
        name = "Emissive Tint",
        description = "Emissive tint. 0.0 is no darkening, 1.0 is total darkening",
        min = 0.0,
        max = 1.0,
        step = 0.01,
        default = 0.0,
        precision = 2
    )

    debug: bpy.props.BoolProperty(
        name = "Debug This OBJ",
        description = "If this and Scene > Advanced Settings > Debug are checked, debug information for this OBJ will be written to the export log and the OBJ",
        default = True
    )

    name: bpy.props.StringProperty(
        name = "Name",
        description = "This name will be used as a filename hint for OBJ file(s)",
        default = ""
    )

    export_type: bpy.props.EnumProperty(
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

    # TODO: Remove this already!
    # Deprecated: This will be removed in v3.4
    cockpit: bpy.props.BoolProperty(
        name = "Cockpit",
        description = "If checked the exported object will be interpreted as a cockpit",
        default = False
    )

    slungLoadWeight: bpy.props.FloatProperty(
        name = "Slung Load Weight",
        description = "Weight of the object in pounds, for use in the physics engine if the object is being carried by a plane or helicopter",
        default = 0.0,
        step = 1,
        precision = 3
    )

    texture: bpy.props.StringProperty(
        subtype = "FILE_PATH",
        name = "Texture",
        description = "Texture to use for objects on this layer",
        default = ""
    )

    texture_lit: bpy.props.StringProperty(
        subtype = "FILE_PATH",
        name = "Night Texture",
        description = "Night Texture to use for objects on this layer",
        default = ""
    )

    texture_normal: bpy.props.StringProperty(
        subtype = "FILE_PATH",
        name = "Normal/Specular Texture",
        description = "Normal/Specular Texture to use for objects on this layer",
        default = ""
    )

    # v1000
    texture_draped: bpy.props.StringProperty(
        subtype = "FILE_PATH",
        name = "Draped Texture",
        description = "Texture to use for draped objects on this layer",
        default = ""
    )

    # v1000
    texture_draped_normal: bpy.props.StringProperty(
        subtype = "FILE_PATH",
        name = "Normal/Specular Texture Draped Texture",
        description = "Normal/Specular Texture to use for draped objects on this layer",
        default = ""
    )

    # BAD NAME ALERT!
    # regions (plural) is the enum, region (singular) is the collection
    cockpit_regions: bpy.props.EnumProperty(
        name = "Cockpit Regions",
        description = "Number of Cockpit regions to use",
        default = "0",
        items = [
            ("0", "None", "None"),
            ("1", "1", "1"),
            ("2", "2", "2"),
            ("3", "3", "3"),
            ("4", "4", "4")
        ],
        update=update_cockpit_regions
    )

    cockpit_region: bpy.props.CollectionProperty(
        name = "Cockpit Region",
        type = XPlaneCockpitRegion,
        description = "Cockpit Region"
    )

    # BAD NAME ALERT!
    # lods (plural) is the enum, lod (singular) is the collection
    lods: bpy.props.EnumProperty(
        name = "Levels of Detail",
        description = "Levels of detail",
        default = "0",
        items = [("0", "None", "None")] + [(str(i),) * 3 for i in range(1, MAX_LODS)],
        update = update_lods
    )

    lod: bpy.props.CollectionProperty(
        name = "LOD",
        type = XPlaneLOD,
        description = "Level of detail",
    )

    # v1000
    lod_draped: bpy.props.FloatProperty(
        name = "Max. Draped LOD",
        description = "Maximum LOD distance for draped geometry. Set to 0 to use farest LOD",
        default = 0,
        min = 0
    )

    # v1000
    tilted: bpy.props.BoolProperty(
        name = "Tilted",
        description = "Causes objects placed on a scenery tile to sit “on” the ground even if it is sloped",
        default = False
    )

    # v1000
    slope_limit: bpy.props.BoolProperty(
        name = "Slope Limit",
        description = "Establishes the maximum slope limit an object will tolerate (in degrees) for library objects placed in a DSF",
        default = False
    )

    # v1000
    slope_limit_min_pitch: bpy.props.FloatProperty(
        name = "Min. Pitch",
        description = "Represents the ground sloping down at the front of the object in degrees",
        default = 0.0,
        precision = 2
    )

    # v1000
    slope_limit_max_pitch: bpy.props.FloatProperty(
        name = "Max. Pitch",
        description = "Represents the ground sloping down at the front of the object in degrees",
        default = 0.0,
        precision = 2
    )

    # v1000
    slope_limit_min_roll: bpy.props.FloatProperty(
        name = "Min. Roll",
        description = "Represents the ground sloping down to the left of the object in degrees",
        default = 0.0,
        precision = 2
    )

    # v1000
    slope_limit_max_roll: bpy.props.FloatProperty(
        name = "Max. Roll",
        description = "Represents the ground sloping down to the left of the object in degrees",
        default = 0.0,
        precision = 2
    )

    # v1000
    require_surface: bpy.props.EnumProperty(
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
    cockpit_lit: bpy.props.BoolProperty(
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

    layer_group: bpy.props.EnumProperty(
        name = "Layer Group",
        description = "Draw this OBJ in a special group",
        default = "none",
        items = layerGroups
    )

    layer_group_offset: bpy.props.IntProperty(
        name = "Layer Group Offset",
        description = "Use to fine tune drawing order",
        default = 0,
        min = -5,
        max = 5
    )

    layer_group_draped: bpy.props.EnumProperty(
        name = "Draped Layer Group",
        description = "Draws draped geometry in a special group",
        default = "none",
        items = layerGroups
    )

    layer_group_draped_offset: bpy.props.IntProperty(
        name = "Draped Layer Group Offset",
        description = "Use to fine tune drawing order of draped geometry",
        default = 0,
        min = -5,
        max = 5
    )

    customAttributes: bpy.props.CollectionProperty(
        name = "Custom X-Plane Header Attributes",
        description = "User defined header attributes for the X-Plane file",
        type = XPlaneCustomAttribute
    )

    autodetectTextures: bpy.props.BoolProperty(
        name = "Autodetect Textures",
        description = "Automaticly determines textures based on materials",
        default = False
    )


class XPlaneCollectionSettings(bpy.types.PropertyGroup):
    is_exportable_collection: bpy.props.BoolProperty(
        name = "Root Collection",
        description = "Activate to export all this collection's children as an .obj file",
        default = False
    )

    layer: bpy.props.PointerProperty(
        name = "X-Plane OBJ File Settings",
        description = "X-Plane OBJ File Settings",
        type = XPlaneLayer
    )

class XPlaneSceneSettings(bpy.types.PropertyGroup):
    command_search_window_state: bpy.props.PointerProperty(
            name = "Command Search Window State",
            description = "An internally important property that keeps track of the state of the command search window",
            type = XPlaneCommandSearchWindow
            )

    dataref_search_window_state: bpy.props.PointerProperty(
            name = "Dataref Search Window State",
            description = "An internally important property that keeps track of the state of the dataref search window",
            type = XPlaneDatarefSearchWindow
            )

    debug: bpy.props.BoolProperty(
        name = "Print Debug Info To Output, OBJ",
        description = "If checked debug information will be printed to the console and into OBJ files",
        default = False
    )

    expanded_non_exporting_collections: bpy.props.BoolProperty(
            name = "Other Collections",
            description = "Reveals Non-Root Collections"
    )

    log: bpy.props.BoolProperty(
        name = "Create Log File",
        description = "If checked the debug information will be written to a log file",
        default = False
    )

    # Plugin development tools
    plugin_development: bpy.props.BoolProperty(
        name = "Plugin Development Tools (Experimental!)",
        description = "A selection of tools and options for plugin developers to write and debug XPlane2Blender. You are unlikely to find these useful",
        default = False) # Set this to true during development to avoid re-checking it

    #######################################
    #TODO: Should these be in their own namespace?
    dev_enable_breakpoints: bpy.props.BoolProperty(
        name = "Enable Breakpoints",
        description = "Allows use of Eclipse breakpoints (must have PyDev, Eclipse installed and configured to use and Pydev Debug Server running!)",
        default = False)

    dev_continue_export_on_error: bpy.props.BoolProperty(
        name = "Continue Export On Error",
        description = "Exporter continues even when an OBJ cannot be exported. It does not affect unit tests",
        default = False)

    dev_export_as_dry_run: bpy.props.BoolProperty(
        name        = 'Dry Run',
        description = 'Run exporter without actually writing .objs to disk',
        default = False)

    dev_fake_xplane2blender_version: bpy.props.StringProperty(
        name       = "Fake XPlane2Blender Version",
        description = "The Fake XPlane2Blender Version to re-run the upgrader with",
        default = "")#str(bpy.context.scene.xplane.get("xplane2blender_ver")))
    #######################################

    optimize: bpy.props.BoolProperty(
        name = "Optimize",
        description = "If checked file size will be optimized. However this can increase export time slightly",
        default = False
    )

    version: bpy.props.EnumProperty(
        name = "X-Plane Version",
        default = VERSION_1130,
        items = [
            (VERSION_900,  "9.x", "9.x"),
            (VERSION_1000, "10.0x", "10.0x"),
            (VERSION_1010, "10.1x", "10.1x"),
            (VERSION_1040, "10.4x", "10.4x"),
            (VERSION_1050, "10.5x", "10.5x"),
            (VERSION_1100, "11.0x", "11.0x"),
            (VERSION_1110, "11.1x", "11.1x"),
            (VERSION_1130, "11.3x", "11.3x")
        ]
    )

    compositeTextures: bpy.props.BoolProperty(
        name = "Compile Normal-Textures",
        description = "Will automatically create and use corrected normal textures",
        default = True
    )

    # This list of version histories the .blend file has encountered,
    # from the earliest
    xplane2blender_ver_history: bpy.props.CollectionProperty(
        name="XPlane2Blender History",
        description="Every version of XPlane2Blender this .blend file has been opened with",
        type=XPlane2BlenderVersion)

# Class: XPlaneObjectSettings
#
# Properties:
#   datarefs - Collection of <XPlaneDatarefs>. X-Plane Datarefs
#   bool depth - True if object will use depth culling.
#   customAttributes - Collection of <XPlaneCustomAttributes>. Custom X-Plane attributes
#   XPlaneManipulator manip - Manipulator settings.
#   bool lightLevel - True if object overrides default light levels.
#   float lightLevel_v1 - Light Level Value 1
#   float lightLevel_v2 - Light Level Value 2
#   string lightLevel_dataref - Light Level Dataref
class XPlaneObjectSettings(bpy.types.PropertyGroup):
    """
    Settings for Blender objects. On Blender Objects these are accessed via a
    pointer property called xplane. Ex: bpy.data.objects[0].xplane.datarefs
    """
    customAttributes: bpy.props.CollectionProperty(
        name = "Custom X-Plane Attributes",
        description = "User defined attributes for the Object",
        type = XPlaneCustomAttribute
    )

    customAnimAttributes: bpy.props.CollectionProperty(
        name = "Custom X-Plane Animation Attributes",
        description = "User defined attributes for animation of the Object",
        type = XPlaneCustomAttribute
    )

    datarefs: bpy.props.CollectionProperty(
        name = "X-Plane Datarefs",
        description = "X-Plane Datarefs",
        type = XPlaneDataref
    )

    override_lods: bpy.props.BoolProperty(
        name = "Override LODs",
        description = "Overrides any parent's LOD buckets for this object and its children",
        default = False
    )

    # Since "Empty" is not a Blender type, only a "type" of Object, we have
    # to put this on here, even if it might not be relavent
    # to the current object.
    # Always check for type == "EMPTY" before using!
    special_empty_props: bpy.props.PointerProperty(
        name = "Special Empty Properties",
        description = "Empty Only Properties",
        type = XPlaneEmpty
    )

    manip: bpy.props.PointerProperty(
        name = "Manipulator",
        description = "X-Plane Manipulator Settings",
        type = XPlaneManipulatorSettings
    )

    lod: bpy.props.BoolVectorProperty(
        name = "Levels Of Detail",
        description = "Define in wich LODs this object will be used. If none is checked it will be used in all",
        default = (False, False, False, False),
        size = MAX_LODS-1
    )

    override_weight: bpy.props.BoolProperty(
        name = "Override Weight",
        description = "If checked you can override the internal weight of the object. Heavier objects will be written later in OBJ",
        default = False
    )

    weight: bpy.props.IntProperty(
        name = "Weight",
        description = "Usual weights are: Meshes 0-8999, Lines 9000 - 9999, Lights > = 10000",
        default = 0,
        min = 0
    )

    # v1000
    conditions: bpy.props.CollectionProperty(
        name = "Conditions",
        description = "Hide/show object depending on rendering settings",
        type = XPlaneCondition
    )

    isExportableRoot: bpy.props.BoolProperty(
        name = "Root Object",
        description = "Activate to export this object and all its children into it's own .obj file",
        default = False
    )

    layer: bpy.props.PointerProperty(
        name = "X-Plane Layer",
        description = "X-Plane OBJ File Settings",
        type = XPlaneLayer
    )

# Class: XPlaneBoneSettings
# Settings for Blender bones.
#
# Properties:
#   datarefs - Collection of <XPlaneDatarefs>. X-Plane Datarefs
class XPlaneBoneSettings(bpy.types.PropertyGroup):
    datarefs: bpy.props.CollectionProperty(
        name = "X-Plane Datarefs",
        description = "X-Plane Datarefs",
        type = XPlaneDataref
    )

    customAttributes: bpy.props.CollectionProperty(
        name = "Custom X-Plane Attributes",
        description = "User defined attributes for the Object",
        type = XPlaneCustomAttribute
    )

    customAnimAttributes: bpy.props.CollectionProperty(
        name = "Custom X-Plane Animation Attributes",
        description = "User defined attributes for animation of the Object",
        type = XPlaneCustomAttribute
    )

    override_weight: bpy.props.BoolProperty(
        name = "Override Weight",
        description = "If checked you can override the internal weight of the object. Heavier objects will be written later in OBJ",
        default = False
    )

    weight: bpy.props.IntProperty(
        name = "Weight",
        description = "Usual weights are: Meshes 0-8999, Lines 9000 - 9999, Lights > = 10000",
        default = 0,
        min = 0
    )

# Class: XPlaneMaterialSettings
# Settings for Blender materials.
#
# Properties:
#   enum surfaceType - Surface type as defined in OBJ specs.
#   bool blend - True if the material uses alpha cutoff.
#   float blendRatio - Alpha cutoff ratio.
class XPlaneMaterialSettings(bpy.types.PropertyGroup):
    draw: bpy.props.BoolProperty(
        name = "Draw Objects With This Material",
        description = "If turned off, objects with this material won't be drawn",
        default = True
    )

    # --- cockpit_device props ------------------------------------------------
    device_name: bpy.props.EnumProperty(
        name = "Cockpit Device Name",
        description = "GPS device name",
        default = DEVICE_GNS430_1,
        items = [
            (DEVICE_GNS430_1,    DEVICE_GNS430_1,     DEVICE_GNS430_1),
            (DEVICE_GNS430_2,    DEVICE_GNS430_2,     DEVICE_GNS430_2),
            (DEVICE_GNS530_1,    DEVICE_GNS530_1,     DEVICE_GNS530_1),
            (DEVICE_GNS530_2,    DEVICE_GNS530_2,     DEVICE_GNS530_2),
            (DEVICE_CDU739_1,    DEVICE_CDU739_1,     DEVICE_CDU739_1),
            (DEVICE_CDU739_2,    DEVICE_CDU739_2,     DEVICE_CDU739_2),
            (DEVICE_G1000_PFD1,  DEVICE_G1000_PFD1,   DEVICE_G1000_PFD1),
            (DEVICE_G1000_MFD,   DEVICE_G1000_MFD,    DEVICE_G1000_MFD),
            (DEVICE_G1000_PFD2,  DEVICE_G1000_PFD2,   DEVICE_G1000_PFD2),
        ]
    )
    device_bus_0: bpy.props.BoolProperty(name="Bus 1", description="1st system bus")
    device_bus_1: bpy.props.BoolProperty(name="Bus 2", description="2nd system bus")
    device_bus_2: bpy.props.BoolProperty(name="Bus 3", description="3rd system bus")
    device_bus_3: bpy.props.BoolProperty(name="Bus 4", description="4th system bus")
    device_bus_4: bpy.props.BoolProperty(name="Bus 5", description="5th system bus")
    device_bus_5: bpy.props.BoolProperty(name="Bus 6", description="6th system bus")

    device_lighting_channel: bpy.props.IntProperty(
        name="Rheostat Lighting Channel",
        description="0 based index that control's screen's brightness. Not affected by 'Light Level'",
        default=0,
        min=0,
    )
    device_auto_adjust: bpy.props.BoolProperty(
        name="Auto-adjust for daytime readability",
        description="If true, the screen brightens automatically to be readable in the day. Otherwise it is 'washed out' in daylight",
        default=True,
    )
    # -------------------------------------------------------------------------

    surfaceType: bpy.props.EnumProperty(
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

    shadow_local: bpy.props.BoolProperty(
        name="Cast Shadows (Local)",
        description="If enabled, object will cast shadows. Must have 'Cast Shadows (Global)' checked",
        default=True
    )

    deck: bpy.props.BoolProperty(
        name = "Deck",
        description = "Allows the user to fly under the surface",
        default = False
    )

    solid_camera: bpy.props.BoolProperty(
        name = "Camera Collision",
        description = "X-Plane's camera will be prevented from moving through objects with this material. Only allowed in Cockpit type exports",
        default = False
    )

    blend: bpy.props.BoolProperty(
        name = "Use Alpha Cutoff",
        description = "If turned on the textures alpha channel will be used to cutoff areas above the Alpha cutoff ratio",
        default = False
    )

    # v1000
    blend_v1000: bpy.props.EnumProperty(
        name = "Blend",
        description = "Controls texture alpha/blending",
        default = BLEND_ON,
        items = [
            (BLEND_OFF, 'Alpha Cutoff', 'Textures alpha channel will be used to cutoff areas above the Alpha cutoff ratio'),
            (BLEND_ON, 'Alpha Blend', 'Textures alpha channel will blended'),
            (BLEND_SHADOW, 'Shadow', 'In shadow mode, shadows are not blended but primary drawing is')
        ]
    )

    blendRatio: bpy.props.FloatProperty(
        name = "Alpha Cutoff Ratio",
        description = "Levels in the texture below this level are rendered as fully transparent and levels above this level are fully opaque",
        default = 0.5,
        step = 0.1,
        precision = 2,
        min = 0.0,
        max = 1.0,
    )

    cockpit_feature: bpy.props.EnumProperty(
        name = "Cockpit Feature",
        description = "What cockpit feature to enable",
        default=COCKPIT_FEATURE_NONE,
        items=[
            (COCKPIT_FEATURE_NONE, "None", "Material uses no advanced cocked features"),
            (COCKPIT_FEATURE_PANEL, "Panel Texture", "Material uses Panel Texture"),
            (COCKPIT_FEATURE_DEVICE, "Cockpit Device", "Material uses Device Texture"),
            ],
        )
    cockpit_region: bpy.props.EnumProperty(
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

    lightLevel: bpy.props.BoolProperty(
        name = "Override Light Level",
        description = "If checked values will change the brightness of the _LIT texture for the object. This overrides the sim's decision about object lighting",
        default = False
    )

    lightLevel_v1: bpy.props.FloatProperty(
        name = "Value 1",
        description = "Value 1 for light level",
        default = 0.0,
        precision = 2
    )

    lightLevel_v2: bpy.props.FloatProperty(
        name = "Value 2",
        description = "Value 2 for light level",
        default = 1.0,
        precision = 2
    )

    lightLevel_dataref: bpy.props.StringProperty(
        name = "Dataref",
        description = "The dataref is interpreted as a value between v1 and v2. Values outside v1 and v2 are clamped",
        default = ""
    )

    poly_os: bpy.props.IntProperty(
        name = "Polygon Offset",
        description = "Sets the polygon offset state. Leave at 0 for default behaviour",
        default = 0,
        step = 1,
        min = 0
    )

    # v1000
    conditions: bpy.props.CollectionProperty(
        name = "Conditions",
        description = "Hide/show objects with material depending on rendering settings",
        type = XPlaneCondition
    )

    customAttributes: bpy.props.CollectionProperty(
        name = "Custom X-Plane Material Attributes",
        description = "User defined material attributes for the X-Plane file",
        type = XPlaneCustomAttribute
    )

    #TODO: When we have the updater again, remove this unneeded thing.
    # This was only for automatically playing with Blender Render which is dead
    litFactor: bpy.props.FloatProperty(
        name = "Day-Night Preview Balance",
        description = "Adjusts 3D View's preview of day vs night texture",
        default = 0,
        min = 0,
        max = 1,
        step = 0.1,
        #update = updateMaterialLitPreview
    )

    # v1000
    draped: bpy.props.BoolProperty(
        name = "Draped",
        description = "Will perfectly match with the ground",
        default = False
    )



    # v1000 (draped only)
    bump_level: bpy.props.FloatProperty(
        name = "Draped Bump Level",
        description = "Scales the Bump for draped geometry up or down",
        default = 1.0,
        min = -2.0,
        max = 2.0
    )



class XPlaneLightSettings(bpy.types.PropertyGroup):
    enable_rgb_override: bpy.props.BoolProperty(
        name = "Enable RGB Picker Override",
        description = "Used instead of the Blender color picker to input any RGB values. Useful for certain datarefs",
        default = False
        )

    param_freq: bpy.props.FloatProperty(
        name = "Flash Frequency",
        description = "The number of light flashes per second",
        min = 0.0,
    )

    param_index: bpy.props.IntProperty(
        name = "Dataref Index",
        description = "Index in light's associated array dataref",
        min = 0,
        max = 127
    )

    param_phase: bpy.props.FloatProperty(
        name = "Phase Offset",
        description = "Phase offset in seconds of light (so it can make flashing lights that don't flash at the same time)",
        min = 0.0,
    )

    param_size: bpy.props.FloatProperty(
        name = "Light Size",
        description = "Spill size uses meters; billboard size uses arbitrary scales - bigger is brighter",
        default = 1.0,
        min = LIGHT_PARAM_SIZE_MIN,
        precision = 3
    )

    rgb_override_values: bpy.props.FloatVectorProperty(
        name = "RGB Override Values",
        description = "The values that will be used instead of the RGB picker",
        default = (0.0,0.0,0.0),
        subtype = "NONE",
        unit    = "NONE",
        precision = 3,
        size = 3
        )

    type: bpy.props.EnumProperty(
        name = "Type",
        description = "Defines the type of the light in X-Plane",
        default = LIGHT_AUTOMATIC,
        items = [
                (LIGHT_DEFAULT,   "Default",                    "Default"),
                (LIGHT_FLASHING,  "Flashing" + " (deprecated)", "Flashing" + " (deprecated)"),
                (LIGHT_PULSING,   "Pulsing"  + " (deprecated)", "Pulsing"  + " (deprecated)"),
                (LIGHT_STROBE,    "Strobe"   + " (deprecated)", "Strobe"   + " (deprecated)"),
                (LIGHT_TRAFFIC,   "Traffic"  + " (deprecated)", "Traffic"  + " (deprecated)"),
                (LIGHT_NAMED,     "Named"    + " (deprecated)", "Makes named and named only lights, use automatic"),
                (LIGHT_CUSTOM,    "Custom Billboard",           "Custom billboard light"),
                (LIGHT_PARAM,     "Manual Param (deprecated)",  "Uses manual entry for parameters, not recommended"),
                (LIGHT_AUTOMATIC, "Automatic",                  "Makes named and param lights with params taken from Blender light data"),
                (LIGHT_SPILL_CUSTOM, "Custom Spill",            "Custom spill light, with automatic parameter detection"),
                (LIGHT_NON_EXPORTING, "Non-Exporting", "Light will not be in the OBJ"),
        ]
    )

    name: bpy.props.StringProperty(
        name = "Name",
        description = "Name from lights.txt, see the summary for more detail",
        default = "",
    )

    params: bpy.props.StringProperty(
        name = 'Parameters',
        description = "The additional parameters vary in number and definition based on the particular parameterized light selected",
        default = ""
    )

    size: bpy.props.FloatProperty(
        name = 'Size',
        description = "Size parameter for Custom Lights",
        default = 1.0,
    )

    dataref: bpy.props.StringProperty(
        name = 'Dataref',
        description = "An X-Plane Dataref",
        default = ""
    )

    uv: bpy.props.FloatVectorProperty(
        name = "Texture Coordinates",
        description = "The texture coordinates in the following order: left,top,right,bottom (fractions from 0 to 1)",
        default = (0.0, 0.0, 1.0, 1.0),
        min = 0.0,
        max = 1.0,
        precision = 3,
        size = 4
    )

    customAttributes: bpy.props.CollectionProperty(
        name = "Custom X-Plane Light Attributes",
        description = "User defined light attributes for the X-Plane file",
        type = XPlaneCustomAttribute
    )
# fmt: on


_classes = (
    XPlane2BlenderVersion,
    XPlaneAxisDetentRange,
    XPlaneCondition,
    XPlaneCustomAttribute,
    XPlaneDataref,
    XPlaneEmitter,
    XPlaneMagnet,
    XPlaneEmpty,
    XPlaneExportPathDirective,
    ListItemCommand,
    XPlaneCommandSearchWindow,
    ListItemDataref,
    XPlaneDatarefSearchWindow,
    XPlaneManipulatorSettings,
    XPlaneCockpitRegion,
    XPlaneLOD,
    # complex classes, depending on basic classes
    XPlaneLayer,
    XPlaneCollectionSettings,
    XPlaneObjectSettings,
    XPlaneBoneSettings,
    XPlaneMaterialSettings,
    XPlaneLightSettings,
    XPlaneSceneSettings,
)


def register():
    # basic classes
    for c in _classes:
        bpy.utils.register_class(c)

    bpy.types.Collection.xplane = bpy.props.PointerProperty(
        type=XPlaneCollectionSettings,
        name="X-Plane Collection Settings",
        description="X-Plane Collection Settings",
    )

    bpy.types.Scene.xplane = bpy.props.PointerProperty(
        type=XPlaneSceneSettings,
        name="X-Plane Scene Settings",
        description="X-Plane Scene Settings",
    )
    bpy.types.Object.xplane = bpy.props.PointerProperty(
        type=XPlaneObjectSettings,
        name="X-Plane Object Settings",
        description="X-Plane Object Settings",
    )
    bpy.types.Bone.xplane = bpy.props.PointerProperty(
        type=XPlaneBoneSettings,
        name="X-Plane Bone Settings",
        description="X-Plane Bone Settings",
    )
    bpy.types.Material.xplane = bpy.props.PointerProperty(
        type=XPlaneMaterialSettings,
        name="X-Plane Material Settings",
        description="X-Plane Material Settings",
    )
    bpy.types.Light.xplane = bpy.props.PointerProperty(
        type=XPlaneLightSettings,
        name="X-Plane Light Settings",
        description="X-Plane Light Settings",
    )


def unregister():
    for c in reversed(_classes):
        bpy.utils.unregister_class(c)
