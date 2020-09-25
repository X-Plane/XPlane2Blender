import copy
import math
from collections import Iterable, namedtuple
from collections.abc import MutableSequence
from typing import List, Tuple

import bpy
import mathutils
from mathutils import Vector

from io_xplane2blender import xplane_constants
from io_xplane2blender.xplane_helpers import round_vec
from io_xplane2blender.xplane_types.xplane_keyframe import XPlaneKeyframe


# Class: XPlaneKeyframeCollection
#
# A list of at least 2 XPlaneKeyframes. All keyframes should share the same dataref and
# have the same rotation mode
class XPlaneKeyframeCollection(MutableSequence):
    EULER_AXIS_ORDERING = {
        "ZYX": (0, 1, 2),
        "ZXY": (1, 0, 2),
        "YZX": (0, 2, 1),
        "YXZ": (2, 0, 1),
        "XZY": (1, 2, 0),
        "XYZ": (2, 1, 0),
    }

    def __init__(self, data: List[XPlaneKeyframe]):
        """
        data - A list of XPlaneKeyframes, all with the same dataref and
        rotationMode, at least 2 entries big.

        XPlaneKeyframeCollection may mutate some of the keyframe data to maintain a reference
        axis of animation.
        """

        super().__init__()
        assert data is not None and len(data) >= 2
        assert len({kf.dataref for kf in data}) == 1
        assert len({kf.rotationMode for kf in data}) == 1
        self._list = copy.deepcopy(data)

        # _makeReferenceAxes uses a "cute but regrettable" recursive strategy for
        # converting Quaternions->AA->Euler as needed
        def _makeReferenceAxes(keyframes):
            axes = []
            if keyframes.getRotationMode() == "QUATERNION":
                keyframes.toAA()

            if keyframes.getRotationMode() == "AXIS_ANGLE":
                refAxis = None
                refAxisInv = None

                for keyframe in keyframes:
                    angle = keyframe.rotation[0]
                    axis = keyframe.rotation[1]

                    def round_vector(vec, ndigits=5):
                        v = Vector([round(comp, ndigits) for comp in vec])
                        return v

                    """
                    This section covers the following cases
                    - keyframe has 0 degrees of rotation, so no axis should be produced
                    - refAxis and axis are the same. If this happens for all keyframes, 1 reference axis will be returned! Yay!
                    - Correct axis that are the same as the previous reference axes, just inverted
                    - If at least two axis are different, we convert to Euler angles
                    """
                    if round(angle, 5) == 0:
                        continue
                    elif refAxis == None:
                        refAxis = axis
                        refAxisInv = refAxis * -1
                    elif round_vector(refAxis) == round_vector(axis):
                        continue
                    elif round_vector(refAxisInv) == round_vector(axis):
                        keyframe.rotation = (angle * -1, axis * -1)
                    else:
                        return _makeReferenceAxes(keyframes.toEuler())

                # If our AA's W component was 0 the whole time, we need a default
                if refAxis == None:
                    refAxis = mathutils.Vector((0, 0, 1))
                axes.append(refAxis)
            else:
                try:
                    eulerAxesOrdering = self.EULER_AXIS_ORDERING[
                        keyframes.getRotationMode()
                    ]
                    eulerAxes = [
                        mathutils.Vector((1.0, 0.0, 0.0)),
                        mathutils.Vector((0.0, 1.0, 0.0)),
                        mathutils.Vector((0.0, 0.0, 1.0)),
                    ]
                    for axis in eulerAxesOrdering:
                        axes.append(eulerAxes[axis])
                except:
                    raise Exception(
                        "Rotation mode %s doesn't exist in eulerAxisMap"
                        % (keyframes.getRotationMode())
                    )

            assert len(axes) == 1 or len(axes) == 3
            assert (
                len([axis for axis in axes if not isinstance(axis, mathutils.Vector)])
                == 0
            )
            return axes, keyframes.getRotationMode()

        self._referenceAxes, final_rotation_mode = _makeReferenceAxes(self)

    def __repr__(self):
        return "<{0} {1}>".format(self.__class__.__name__, self._list)

    def __len__(self):
        """List length"""
        return len(self._list)

    def __getitem__(self, i):
        """Get a list item"""
        return self._list[i]

    def __delitem__(self, i):
        """Delete an item"""
        del self._list[i]

    def __setitem__(self, i, val):
        self._list[i] = val

    def __str__(self):
        return str(self._list)

    def insert(self, i, val):
        self._list.insert(i, val)

    def append(self, val):
        self.insert(len(self._list), val)

    def getReferenceAxes(self):
        """
        rotation_mode:str->List[Vector], str (final rotation mode)
        """

        return (self._referenceAxes, self.getRotationMode())

    def getDataref(self):
        return self._list[0].dataref

    def getRotationMode(self):
        return self._list[0].rotationMode

    AxisKeyframeTable = namedtuple("AxisKeyframeTable", ["axis", "table"])
    AxisKeyframeTable.__doc__ = (
        "The reference axis and the table of keyframe rotations along it"
    )
    TableEntry = namedtuple("TableEntry", ["value", "degrees"])
    TableEntry.__doc__ = (
        "An entry in the keyframe table, where value is the dataref value"
    )

    def getRotationKeyframeTables(
        self,
    ) -> List["XPlaneKeyframeCollection.AxisKeyframeTable"]:
        """
        List of sub tables will either be 1 (for AA or Quaternion) or 3 (for Eulers)
        """
        AxisKeyframeTable = XPlaneKeyframeCollection.AxisKeyframeTable
        TableEntry = XPlaneKeyframeCollection.TableEntry

        axes, final_rotation_mode = self.getReferenceAxes()
        if final_rotation_mode in {"AXIS_ANGLE", "QUATERNION"}:
            rot_keyframe_tables = [
                AxisKeyframeTable(
                    axis=axes[0],
                    table=[
                        TableEntry(
                            keyframe.dataref_value,
                            math.degrees(keyframe.rotation[0]),
                        )
                        for keyframe in self
                    ],
                )
            ]
        else:
            rot_keyframe_tables = []
            cur_order = self.EULER_AXIS_ORDERING[final_rotation_mode]
            for i, axis in enumerate(axes):
                rot_keyframe_tables.append(
                    AxisKeyframeTable(
                        axis=axis,
                        table=[
                            TableEntry(
                                keyframe.dataref_value,
                                math.degrees(keyframe.rotation[cur_order[i]]),
                            )
                            for keyframe in self
                        ],
                    )
                )

        assert isinstance(rot_keyframe_tables, list)
        for axis_info in rot_keyframe_tables:
            assert isinstance(axis_info, tuple)
            assert isinstance(axis_info.axis, Vector)
            assert isinstance(axis_info.table, list)

            for table_entry in axis_info.table:
                assert isinstance(table_entry, tuple)
                assert isinstance(table_entry.value, float)
                assert isinstance(table_entry.degrees, float)

        return rot_keyframe_tables

    def getRotationKeyframeTablesNoClamps(
        self,
    ) -> List["XPlaneKeyframeCollection.AxisKeyframeTable"]:
        """
        Returns rotation keyframbe tables without clamping keyframes.
        Throws a ValueError if all resulting keyframe tables would be less than 2 keyframes
        (this should only be possible for certain Euler cases)
        """
        return XPlaneKeyframeCollection.filter_clamping_keyframes(
            self.getRotationKeyframeTables(), "degrees"
        )

    def getTranslationKeyframeTable(self):
        """
        Returns List[TranslationKeyframe[keyframe.value, keyframe.location]] where location is a Vector
        """
        TranslationKeyframe = namedtuple("TranslationKeyframe", ["value", "location"])
        return [
            TranslationKeyframe(keyframe.dataref_value, keyframe.location)
            for keyframe in self
        ]

    def getTranslationKeyframeTableNoClamps(self):
        """
        ()->List[TranslationKeyframe[keyframe.value, keyframe.location]] where location is a Vector
        without any clamping values in the keyframe table
        """
        return XPlaneKeyframeCollection.filter_clamping_keyframes(
            self.getTranslationKeyframeTable(), "location"
        )

    # Returns list  of tuples of (keyframe.dataref_value, keyframe.location)
    # with location being a Vector in Blender form and scaled by the scaling amount
    def getTranslationKeyframeTableWScale(self):
        pre_scale = self[0].xplaneBone.getPreAnimationMatrix().decompose()[2]
        return [
            (value, location * pre_scale)
            for value, location in self.getTranslationKeyframeTable()
        ]

    def asAA(self) -> "XPlaneKeyframeCollection":
        return XPlaneKeyframeCollection([keyframe.asAA() for keyframe in self])

    def asEuler(self) -> "XPlaneKeyframeCollection":
        return XPlaneKeyframeCollection([keyframe.asEuler() for keyframe in self])

    def asQuaternion(self) -> "XPlaneKeyframeCollection":
        return XPlaneKeyframeCollection([keyframe.asQuaternion() for keyframe in self])

    def toAA(self) -> "XPlaneKeyframeCollection":
        self._list = [keyframe.asAA() for keyframe in self]
        return self

    def toEuler(self) -> "XPlaneKeyframeCollection":
        self._list = [keyframe.asEuler() for keyframe in self]
        return self

    def toQuaternion(self) -> "XPlaneKeyframeCollection":
        self._list = [keyframe.asQuaternion() for keyframe in self]
        return self

    @staticmethod
    def filter_clamping_keyframes(
        keyframe_collection: "XPlaneKeyframeCollection", attr: str
    ) -> "XPlaneKeyframeCollection":
        """
        Returns a new keyframe collection without clamping keyframes
        attr specifies which keyframe attribute will be used to filter,
        and must be "location" or "degrees".

        Raises ValueError if resulting cleaned XPlaneKeyframeCollection
        would have less than 2 keyframes
        (which should only be possible for Euler RotationKeyframeTables)
        """
        assert attr in ("location", "degrees")

        # Remove clamp values
        # if attr == 'location':
        #   List[TranslationKeyframe[keyframe.value, keyframe.location]]
        # elif attr == 'degrees
        #   List[RotationKeyframe['value','degrees']] from List[Tuple[axis, List[Tuple['value','degrees']]]]
        ndigits = xplane_constants.PRECISION_KEYFRAME

        def find_1st_non_clamping(keyframes, attr) -> int:
            def cmp_location(current, next_keyframe):
                return round_vec(current.location, ndigits) != round_vec(
                    next_keyframe.location, ndigits
                )

            def cmp_rotation(current, next_keyframe):
                return round(current.degrees, ndigits) != round(
                    next_keyframe.degrees, ndigits
                )

            if attr == "location":
                cmp_fn = cmp_location
            elif attr == "degrees":
                cmp_fn = cmp_rotation

            if len(keyframes) < 2:
                raise ValueError("Keyframe table is less than 2 entries long")

            for i in range(len(keyframes) - 1):
                if cmp_fn(keyframes[i], keyframes[i + 1]):
                    break
            else:  # nobreak
                raise ValueError("No non-clamping found")
            return i

        if attr == "location":
            try:
                start = find_1st_non_clamping(keyframe_collection, attr)
            except ValueError:
                raise
            else:
                try:
                    end = len(keyframe_collection) - find_1st_non_clamping(
                        list(reversed(keyframe_collection)), attr
                    )
                except ValueError:
                    raise
                else:
                    return keyframe_collection[start:end]
        elif attr == "degrees":
            new_keyframe_table = []
            for i, (axis, table) in enumerate(keyframe_collection):
                try:
                    start = find_1st_non_clamping(table, attr)
                except ValueError:
                    new_keyframe_table.append(
                        XPlaneKeyframeCollection.AxisKeyframeTable(axis, [])
                    )
                    continue
                else:
                    try:
                        end = len(table) - find_1st_non_clamping(
                            list(reversed(table)), attr
                        )
                    except ValueError:
                        new_keyframe_table.append(
                            XPlaneKeyframeCollection.AxisKeyframeTable(axis, [])
                        )
                        continue
                    else:
                        new_keyframe_table.append(
                            XPlaneKeyframeCollection.AxisKeyframeTable(
                                axis, table[start:end]
                            )
                        )
            if all(table == [] for axis, table in new_keyframe_table):
                raise ValueError("XPlaneKeyframeCollection had only clamping keyframes")
            return new_keyframe_table
