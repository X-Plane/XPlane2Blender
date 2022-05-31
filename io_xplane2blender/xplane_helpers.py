import datetime
import itertools
import os
import re
from datetime import timezone
from typing import Iterable, List, Optional, Tuple, Union

import bpy
import mathutils
from mathutils import Euler, Matrix, Quaternion, Vector

import io_xplane2blender
from io_xplane2blender import xplane_config, xplane_constants, xplane_props
from io_xplane2blender.xplane_constants import PRECISION_OBJ_FLOAT

"""
Given the difficulty in keeping all these words straight, these
types have been created. Use these to keep yourself from
running in circles
"""

"""Something with an XPlaneLayer property"""
PotentialRoot = Union[bpy.types.Collection, bpy.types.Object]

"""
Something with an XPlaneLayer property that also meets all other requirements.
It does not garuntee an error or warning free export, however
"""
ExportableRoot = Union[bpy.types.Collection, bpy.types.Object]

"""
Something that has a .children property. A collection and object's
children are not compatible
"""
BlenderParentType = Union[bpy.types.Collection, bpy.types.Object]


class UnwriteableXPlaneType(ValueError):
    pass


def floatToStr(n: float) -> str:
    """
    Makes a rounded float with as 0's
    and decimal place removed if possible
    """
    # THIS IS A HOT PATH, DO NOT CHANGE WITHOUT PROFILING

    # 'g' can do the rstrip and '.' removal for us, except for rare cases when we need to fallback
    # to the less fast 'f', rstrip, ternary approach
    s = f"{n:.{PRECISION_OBJ_FLOAT}g}"
    if "e" in s:
        s = f"{n:.{PRECISION_OBJ_FLOAT}f}".rstrip("0")
        return s if s[-1] != "." else s[:-1]
    return s


def resolveBlenderPath(path: str) -> str:
    blenddir = os.path.dirname(bpy.context.blend_data.filepath)

    if path[0:2] == "//":
        return os.path.join(blenddir, path[2:])
    else:
        return path


def effective_normal_metalness(xp_file: "xplane_file.XPlaneFile") -> bool:
    return (
        int(bpy.context.scene.xplane.version) >= 1100
        and xp_file.options.normal_metalness
    )


def effective_normal_metalness_draped(xp_file: "xplane_file.XPlaneFile") -> bool:
    return (
        int(bpy.context.scene.xplane.version) >= 1100
        and xp_file.options.normal_metalness_draped
    )


def get_plugin_resources_folder() -> str:
    return os.path.join(os.path.dirname(__file__), "resources")


def get_potential_objects_in_exportable_root(
    root: PotentialRoot,
) -> List[bpy.types.Object]:
    def is_potential_child(obj: bpy.types.Object) -> bool:
        return obj.type in {"MESH", "LIGHT", "ARMATURE", "EMPTY"}

    def collect_children(obj: bpy.types.Object) -> List[bpy.types.Object]:
        objects = []  # type: List[bpy.types.Object]
        for child in obj.children:
            if is_potential_child(child):
                objects.append(child)
            objects.extend(collect_children(child))
        return objects

    if isinstance(root, bpy.types.Object):
        return collect_children(root)
    else:
        return [obj for obj in root.all_objects if is_potential_child(obj)]


def get_rotation_from_rotatable(
    obj_or_bone: Union[bpy.types.Object, bpy.types.PoseBone]
) -> Union[mathutils.Euler, mathutils.Quaternion, Tuple[float, float, float, float]]:
    """Returns a copy of the rotation, in whatever mode was given"""
    rotation_mode = obj_or_bone.rotation_mode

    if rotation_mode == "QUATERNION":
        return obj_or_bone.rotation_quaternion.copy()
    elif rotation_mode == "AXIS_ANGLE":
        return tuple(obj_or_bone.rotation_axis_angle)
    else:
        return obj_or_bone.rotation_euler.copy()


def get_collections_in_scene(scene: bpy.types.Scene) -> List[bpy.types.Collection]:
    """
    First entry in list is always the scene's 'Master Collection'
    """

    def get_collections_from_collection(
        collection: bpy.types.Collection,
    ) -> List[bpy.types.Collection]:
        collections = []
        for child in collection.children:
            collections.append(child)
            collections.extend(get_collections_from_collection(child))

        return collections

    return [scene.collection] + get_collections_from_collection(scene.collection)


def get_layer_collections_in_view_layer(
    view_layer: bpy.types.ViewLayer,
) -> List[bpy.types.LayerCollection]:
    """
    First entry in list is always the scene's Master Layer Collection
    """

    def get_layer_collections_from_layer_collection(
        layer_collection: bpy.types.LayerCollection,
    ) -> List[bpy.types.LayerCollection]:
        child_lcs = []
        for child_lc in layer_collection.children:
            child_lcs.append(child_lc)
            child_lcs.extend(get_layer_collections_from_layer_collection(child_lc))
        return child_lcs

    return [view_layer.layer_collection] + get_layer_collections_from_layer_collection(
        view_layer.layer_collection
    )


def get_exportable_roots_in_scene(
    scene: bpy.types.Scene, view_layer: bpy.types.ViewLayer
) -> List[bpy.types.Object]:
    return [
        root
        for root in filter(
            lambda o: is_exportable_root(o, view_layer),
            itertools.chain(get_collections_in_scene(scene), scene.objects),
        )
    ]


def is_vector_axis_aligned(
    vector: Union[Vector, Tuple[float, float, float]],
    ndigits: float = 5,
) -> bool:
    """
    Returns true if a vector is along one of the standard cartesian axes.
    It does not test that the magnitude is 1, however.
    """
    vector = Vector(map(abs, vector)).normalized()
    return any(
        int(round(vector.dot(Vector(v)), ndigits)) == 1
        for v in {*itertools.permutations([1, 0, 0])}
    )


def is_visible_in_viewport(
    datablock: Union[bpy.types.Collection, bpy.types.Object],
    view_layer: bpy.types.ViewLayer,
) -> Optional[ExportableRoot]:
    if isinstance(datablock, bpy.types.Collection):
        all_layer_collections = {
            c.name: c for c in get_layer_collections_in_view_layer(view_layer)
        }
        return all_layer_collections[datablock.name].is_visible
    elif isinstance(datablock, bpy.types.Object):
        return datablock.visible_get() or None


def is_exportable_root(
    potential_root: PotentialRoot, view_layer: bpy.types.ViewLayer
) -> bool:
    """
    Since datablocks don't keep track of which view layers they're a part of,
    we have to provide it
    """
    return (
        potential_root.xplane.get("isExportableRoot")
        or potential_root.xplane.get("is_exportable_collection")
    ) and is_visible_in_viewport(potential_root, view_layer)


def round_vec(v: mathutils.Vector, ndigits: int) -> mathutils.Vector:
    return mathutils.Vector(round(comp, ndigits) for comp in v)


def vec_b_to_x(v) -> mathutils.Vector:
    """Converts Vector from Blender co-ords (X, Y, Z) to X-Plane as (X, Z, -Y)"""
    return mathutils.Vector((v[0], v[2], -v[1]))


def vec_x_to_b(v) -> mathutils.Vector:
    """Converts Vector from X-Plane co-ords (X, Y, Z) to Blender as (X, -Z, Y)"""
    return mathutils.Vector((v[0], -v[2], v[1]))


# This is a convenience struct to help prevent people from having to repeatedly copy and paste
# a tuple of all the members of XPlane2BlenderVersion. It is only a data transport struct!
class VerStruct:
    def __init__(
        self,
        addon_version: Optional[Tuple[int, int, int]] = None,
        build_type: Optional[str] = None,
        build_type_version: Optional[int] = None,
        data_model_version: Optional[int] = None,
        build_number: Optional[str] = None,
    ):
        # fmt: off
        self.addon_version      = tuple(addon_version) if addon_version      is not None else (0,0,0)
        self.build_type         = build_type           if build_type         is not None else xplane_constants.BUILD_TYPE_DEV
        self.build_type_version = build_type_version   if build_type_version is not None else 0
        self.data_model_version = data_model_version   if data_model_version is not None else 0
        self.build_number       = build_number         if build_number       is not None else xplane_constants.BUILD_NUMBER_NONE
        # fmt: on

    def __eq__(self, other):
        if tuple(self.addon_version) == tuple(other.addon_version):
            if self.build_type == other.build_type:
                if self.build_type_version == other.build_type_version:
                    if self.data_model_version == other.data_model_version:
                        return True
        return False

    def __ne__(self, other):
        return not self == other

    def __lt__(self, other):
        return (
            self.addon_version,
            xplane_constants.BUILD_TYPES.index(self.build_type),
            self.build_type_version,
            self.data_model_version,
        ) < (
            other.addon_version,
            xplane_constants.BUILD_TYPES.index(other.build_type),
            other.build_type_version,
            other.data_model_version,
        )

    def __gt__(self, other):
        return (
            self.addon_version,
            xplane_constants.BUILD_TYPES.index(self.build_type),
            self.build_type_version,
            self.data_model_version,
        ) > (
            other.addon_version,
            xplane_constants.BUILD_TYPES.index(other.build_type),
            other.build_type_version,
            other.data_model_version,
        )

    def __ge__(self, other):
        return (self > other) or (self == other)

    def __le__(self, other):
        return (self < other) or (self == other)

    # Works for XPlane2BlenderVersion or VerStruct
    def __repr__(self):
        # WARNING! Make sure this is the same as XPlane2BlenderVersion's!!!
        return "(%s, %s, %s, %s, %s)" % (
            "(" + ",".join(map(str, self.addon_version)) + ")",
            "'" + str(self.build_type) + "'",
            str(self.build_type_version),
            str(self.data_model_version),
            "'" + str(self.build_number) + "'",
        )

    def __str__(self):
        # WARNING! Make sure this is the same as XPlane2BlenderVersion's!!!
        return "%s-%s.%s+%s.%s" % (
            ".".join(map(str, self.addon_version)),
            self.build_type,
            self.build_type_version,
            self.data_model_version,
            self.build_number,
        )

    # Method: is_valid
    #
    # Tests if all members of VerStruct are the right type and semantically valid
    # according to our spec
    #
    # Returns True or False
    def is_valid(self) -> bool:
        types_correct = (
            isinstance(self.addon_version, tuple)
            and len(self.addon_version) == 3
            and isinstance(self.build_type, str)
            and isinstance(self.build_type_version, int)
            and isinstance(self.data_model_version, int)
            and isinstance(self.build_number, str)
        )

        if not types_correct:
            raise Exception("Incorrect types passed into VerStruct")

        if (
            self.addon_version[0] >= 3
            and self.addon_version[1] >= 0
            and self.addon_version[2] >= 0
        ):
            if xplane_constants.BUILD_TYPES.index(self.build_type) != -1:
                if (
                    self.build_type == xplane_constants.BUILD_TYPE_DEV
                    or self.build_type == xplane_constants.BUILD_TYPE_LEGACY
                ):
                    if self.build_type_version > 0:
                        print(
                            "build_type_version must be 0 when build_type is %s"
                            % self.build_type
                        )
                        return False
                elif self.build_type_version <= 0:
                    print(
                        "build_type_version must be > 0 when build_type is %s"
                        % self.build_type
                    )
                    return False

                if (
                    self.build_type == xplane_constants.BUILD_TYPE_LEGACY
                    and self.data_model_version != 0
                ):
                    print(
                        "Invalid build_type,data_model_version combo: legacy and data_model_version is not 0"
                    )
                    return False
                elif (
                    self.build_type != xplane_constants.BUILD_TYPE_LEGACY
                    and self.data_model_version <= 0
                ):
                    print(
                        "Invalid build_type,data_model_version combo: non-legacy and data_model_version is > 0"
                    )
                    return False

                if self.build_number == xplane_constants.BUILD_NUMBER_NONE:
                    return True
                else:
                    datetime_matches = re.match(
                        r"(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})", self.build_number
                    )
                    try:
                        # a timezone aware datetime object preforms the validations on construction.
                        dt = datetime.datetime(
                            *[int(group) for group in datetime_matches.groups()],
                            tzinfo=timezone.utc,
                        )
                    except Exception as e:
                        print(
                            "Exception %s occurred while trying to parse datetime" % e
                        )
                        print('"%s" is an invalid build number' % (self.build_number))
                        return False
                    else:
                        return True
            else:
                print("build_type %s was not found in BUILD_TYPES" % self.build_type)
                return False
        else:
            print("addon_version %s is invalid" % str(self.addon_version))
            return False

    @staticmethod
    def add_to_version_history(
        scene: bpy.types.Scene,
        version_to_add: Union["VerStruct", "xplane_props.XPlane2BlenderVersion"],
    ):
        history = scene.xplane.xplane2blender_ver_history

        if len(history) == 0 or history[-1].name != repr(version_to_add):
            new_hist_entry = history.add()
            new_hist_entry.name = repr(version_to_add)
            success = new_hist_entry.safe_set_version_data(
                version_to_add.addon_version,
                version_to_add.build_type,
                version_to_add.build_type_version,
                version_to_add.data_model_version,
                version_to_add.build_number,
            )
            if not success:
                history.remove(len(history) - 1)
                return None
            else:
                return new_hist_entry
        else:
            return False

    # Method: current
    #
    # Returns a VerStruct with all the current xplane_config information.
    # Note: This SHOULD be the same as scene.xplane.xplane2blender_ver, and it is better to use that version.
    # This is provided to reduce error-prone copy and pasting, as needed only!

    @staticmethod
    def current():
        return VerStruct(
            xplane_config.CURRENT_ADDON_VERSION,
            xplane_config.CURRENT_BUILD_TYPE,
            xplane_config.CURRENT_BUILD_TYPE_VERSION,
            xplane_config.CURRENT_DATA_MODEL_VERSION,
            xplane_config.CURRENT_BUILD_NUMBER,
        )

    @staticmethod
    def from_version_entry(
        version_entry: "xplane_props.XPlane2BlenderVersion",
    ) -> "VerStruct":
        return VerStruct(
            version_entry.addon_version,
            version_entry.build_type,
            version_entry.build_type_version,
            version_entry.data_model_version,
            version_entry.build_number,
        )

    @staticmethod
    def make_new_build_number():
        # Use the UNIX Timestamp in UTC
        return datetime.datetime.now(tz=datetime.timezone.utc).strftime("%Y%m%d%H%M%S")

    # Method: parse_version
    #
    # Parameters:
    #    version_string: The string to attempt to parse
    # Returns:
    # A valid XPlane2BlenderVersion.VerStruct or None if the parse was unsuccessful
    #
    # Parses a variety of strings and attempts to extract a valid version number and a build number
    # Formats
    # Old version numbers: '3.2.0', '3.2', or '3.3.13'
    # New, moder format: '3.4.0-beta.5+1.20170906154330'
    @staticmethod
    def parse_version(version_str: str) -> Optional["VerStruct"]:
        version_struct = VerStruct()
        # We're dealing with modern
        if version_str.find("-") != -1:
            ######################################
            # Regex matching and data extraction #
            ######################################
            format_str = r"(\d+\.\d+\.\d+)-(alpha|beta|dev|leg|rc)\.(\d+)"

            if "+" in version_str:
                format_str += r"\+(\d+)\.(\w{14})"

            version_matches = re.match(format_str, version_str)

            # Part 1: Major.Minor.revision (1)
            # Part 2: '-' and a build type (2), then a literal '.' and build type number (3)
            # (Optional) literal '+'
            # Part 3: 1 or more digits for data model number (4), a literal '.',
            # then a YYYYMMDDHHMMSS (5)
            if version_matches:
                version_struct.addon_version = tuple(
                    [int(comp) for comp in version_matches.group(1).split(".")]
                )
                version_struct.build_type = version_matches.group(2)
                version_struct.build_type_version = int(version_matches.group(3))

                # If we have a build number, we can take this opportunity to validate it
                if "+" in version_str:
                    version_struct.data_model_version = int(version_matches.group(4))
                    # Regex groups for (hopefully matching) YYYYMMDDHHMMSS
                    version_struct.build_number = version_matches.group(5)
            else:
                return None
        else:
            if re.search("[^\d.]", version_str) is not None:
                return None
            else:
                version_struct.addon_version = tuple(
                    [int(v) for v in version_str.split(".")]
                )
                version_struct.build_type = xplane_constants.BUILD_TYPE_LEGACY

        if version_struct.is_valid():
            return version_struct
        else:
            return None


# This a hack to help tests.py catch when an error is an error,
# because everybody and their pet poodle like using the words 'Fail',
#'Error', "FAIL", and "ERROR" making regex impossible.
#
# unittest prints a handy string of .'s, F's, and E's on the first line,
# but due to reasons beyond my grasp, sometimes they don't print a newline
# at the end of it when a failure occurs, making it useless, since we use the word
# "INFO" with an F, meaning you can't search the first line for an F!
#
# Hence this stupid stupid hack, which, is hopefully useful in someway
# Rather than a "did_print_once"
#
# This is yet another reminder about how relying on strings printed to a console
# To tell how your unit test went is a bad idea, especially when you can't seem to control
# What gets output when.
message_to_str_count = 0

"""
Logging Style Guide:
    - Put the name of object or source of error first, leave a trail to follow quickly
    - Include how to correct a problem instead of simply complaining about it, if possible
    - Simple English benefits all, no programmer speak, mentions of the API, or complex grammar
    - Be clear when you're talking about Blender concepts and X-Plane concepts
    - Be terse, avoid more than a sentence including data filled in strings - avoid word wrapping
    - Speak calmly and positively. Avoid "you failed" statements and exclamation marks
    - One error per problem, not one error per newline
    - Find errors whenever possible during the collection phase instead of writing the writing phase
    - Test errors are emitted as part of unit testing

Spending 20mins on a good error message is better than 2hrs troubleshooting an author's
non-existant bug
"""


class XPlaneLogger:
    def __init__(self):
        self.transports = []
        self.messages = []

    def addTransport(
        self, transport, messageTypes=["error", "warning", "info", "success"]
    ):
        self.transports.append({"fn": transport, "types": messageTypes})

    def clear(self):
        self.clearTransports()
        self.clearMessages()

    def clearTransports(self):
        del self.transports[:]

    def clearMessages(self):
        del self.messages[:]

    def messagesToString(self, messages=None):
        if messages == None:
            messages = self.messages

        out = ""

        for message in messages:
            out += (
                XPlaneLogger.messageToString(
                    message["type"], message["message"], message["context"]
                )
                + "\n"
            )

        return out

    def log(self, messageType, message, context=None):
        self.messages.append(
            {"type": messageType, "message": message, "context": context}
        )

        for transport in self.transports:
            if messageType in transport["types"]:
                transport["fn"](messageType, message, context)

    def error(self, message, context=None):
        self.log("error", message, context)

    def warn(self, message, context=None):
        self.log("warning", message, context)

    def info(self, message, context=None):
        self.log("info", message, context)

    def success(self, message, context=None):
        self.log("success", message, context)

    def findOfType(self, messageType):
        messages = []

        for message in self.messages:
            if message["type"] == messageType:
                messages.append(message)

        return messages

    def hasOfType(self, messageType):
        for message in self.messages:
            if message["type"] == messageType:
                return True

        return False

    def findErrors(self):
        return self.findOfType("error")

    def hasErrors(self):
        return self.hasOfType("error")

    def findWarnings(self):
        return self.findOfType("warning")

    def hasWarnings(self):
        return self.hasOfType("warning")

    def findInfos(self):
        return self.findOfType("info")

    @staticmethod
    def messageToString(messageType, message, context=None):
        io_xplane2blender.xplane_helpers.message_to_str_count += 1
        return "%s: %s" % (messageType.upper(), message)

    @staticmethod
    def InternalTextTransport(name="XPlane2Blender.log"):
        if bpy.data.texts.find(name) == -1:
            log = bpy.data.texts.new(name)
        else:
            log = bpy.data.texts[name]

        log.clear()

        def transport(messageType, message, context=None):
            log.write(
                XPlaneLogger.messageToString(messageType, message, context) + "\n"
            )

        return transport

    @staticmethod
    def ConsoleTransport():
        def transport(messageType, message, context=None):
            if io_xplane2blender.xplane_helpers.message_to_str_count == 1:
                print("\n")
            print(XPlaneLogger.messageToString(messageType, message, context))

        return transport

    @staticmethod
    def FileTransport(filehandle):
        def transport(messageType, message, context=None):
            filehandle.write(
                XPlaneLogger.messageToString(messageType, message, context) + "\n"
            )

        return transport


logger = XPlaneLogger()
