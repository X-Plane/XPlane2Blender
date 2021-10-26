import collections
import inspect
import itertools
import math
import os
import pathlib
import re
import shutil
import sys
import unittest
from dataclasses import dataclass
from pprint import pprint
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union

import bpy
from mathutils import Euler, Vector

import io_xplane2blender
from io_xplane2blender import xplane_config, xplane_helpers, xplane_props
from io_xplane2blender.importer import xplane_imp_cmd_builder, xplane_imp_parser
from io_xplane2blender.tests import animation_file_mappings, test_creation_helpers
from io_xplane2blender.xplane_config import getDebug, setDebug
from io_xplane2blender.xplane_constants import (
    ANIM_TYPE_HIDE,
    ANIM_TYPE_SHOW,
    ANIM_TYPE_TRANSFORM,
    PRECISION_KEYFRAME,
    PRECISION_OBJ_FLOAT,
)
from io_xplane2blender.xplane_helpers import XPlaneLogger, logger
from io_xplane2blender.xplane_types import (
    xplane_attribute,
    xplane_bone,
    xplane_file,
    xplane_primitive,
)

FLOAT_TOLERANCE = 0.0001

__dirname__ = os.path.dirname(__file__)

FilterLinesCallback = Callable[[List[Union[float, str]]], bool]


class TemporarilyMakeRootExportable:
    """
    Ensures a potential_root will be exportable
    and when finished, will revert it's exportable
    and viewport settings
    """

    def __init__(
        self,
        potential_root: Union[xplane_helpers.PotentialRoot, str],
        view_layer: Optional[bpy.types.ViewLayer] = None,
    ):
        """
        If view_layer is None, uses current scene's 1st view_layer
        """
        self.view_layer = view_layer or bpy.context.scene.view_layers[0]

        if isinstance(potential_root, str):
            self.potential_root = test_creation_helpers.lookup_potential_root_from_name(
                potential_root
            )
        else:
            self.potential_root = potential_root

        if isinstance(self.potential_root, bpy.types.Collection):
            self.original_exportable = (
                self.potential_root.xplane.is_exportable_collection
            )
            # The little eyeball
            all_layer_collections = {
                lc.name: lc
                for lc in xplane_helpers.get_layer_collections_in_view_layer(
                    self.view_layer
                )
            }
            self.original_hide_viewport = all_layer_collections[
                self.potential_root.name
            ].hide_viewport
        elif isinstance(self.potential_root, bpy.types.Object):
            self.original_exportable = self.potential_root.xplane.isExportableRoot
            # The little eyeball
            self.original_hide_viewport = self.potential_root.hide_get(
                view_layer=self.view_layer
            )
        else:
            assert False, "How did we get here?!"

        self.original_disable_viewport = self.potential_root.hide_viewport

    def __enter__(self):
        test_creation_helpers.make_root_exportable(self.potential_root, self.view_layer)

    def __exit__(self, exc_type, value, traceback):
        if isinstance(self.potential_root, bpy.types.Collection):
            self.potential_root.xplane.is_exportable_collection = (
                self.original_exportable
            )
        elif isinstance(self.potential_root, bpy.types.Object):
            self.potential_root.xplane.isExportableRoot = self.original_exportable

        test_creation_helpers.make_root_unexportable(
            self.potential_root,
            self.view_layer,
            self.original_hide_viewport,
            self.original_disable_viewport,
        )


class XPlaneTestCase(unittest.TestCase):
    def setUp(self, useLogger=True):
        dd_index = sys.argv.index("--")
        blender_args, xplane_args = sys.argv[:dd_index], sys.argv[dd_index + 1 :]
        setDebug("--force-xplane-debug" in xplane_args)

        if useLogger:
            self.useLogger()

        # logger.warn("---------------")

    def useLogger(self):
        debug = getDebug()
        logLevels = ["error", "warning"]

        if debug:
            logLevels.append("info")
            logLevels.append("success")

        logger.clear()
        logger.addTransport(XPlaneLogger.ConsoleTransport(), logLevels)


    def assertTransformAction(
        self,
        bl_object: bpy.types.Object,
        expected_inter_anim: xplane_imp_cmd_builder.IntermediateAnimation,
    ):
        """
        Asserts that an object's action datablock matches the animation specified by the ImportedAnimation struct.

        Assumes
            - bl_object has an action with `location` or `rotation` (in XYZ Eulers), **exclusively**
            - Tests 1 dataref path at a time
        """
        try:
            action = bl_object.animation_data.action
        except AttributeError:  # animation_data is None
            assert False
        else:

            def action_as_intermediate_animation(
                bl_object: bpy.types.Object,
            ) -> xplane_imp_cmd_builder.IntermediateAnimation:
                """
                Convert a bl_object's action into an IntermediateAnimation
                """

                action_as_intermediate_animation = (
                    xplane_imp_cmd_builder.IntermediateAnimation()
                )

                def recombine_fcurves(
                    action: bpy.types.Action, data_path: str
                ) -> Union[List[Vector], Euler]:
                    """
                    Turns an FCurve's Location and Rotation into lists of Vectors or Eulers

                    TODO: Cannot handle missing channels or an object with location and rotation
                    """
                    try:
                        x_comp, y_comp, z_comp = (
                            [k.co[1] for k in f.keyframe_points]
                            for f in action.fcurves
                            if f.data_path == data_path
                        )
                    except ValueError:  # no matching fcurves found
                        if data_path == "location":
                            return []
                        elif data_path == "rotation_euler":
                            return {}
                    else:
                        if data_path == "location":
                            return [
                                Vector((x, y, z))
                                for x, y, z in zip(x_comp, y_comp, z_comp)
                            ]
                        elif data_path == "rotation_euler":
                            return Euler((x_comp, y_comp, z_comp))

                action_as_intermediate_animation.locations = recombine_fcurves(
                    bl_object.animation_data.action, "location"
                )
                action_as_intermediate_animation.rotations = recombine_fcurves(
                    bl_object.animation_data.action, "rotation_euler"
                )
                # ---end recombine_fcurves-------------------------------------

                def get_dataref_prop_from_data_path(
                    bl_object: bpy.types.Object, expected_path: str
                ) -> Tuple[bpy.types.FCurve, xplane_props.XPlaneDataref]:
                    for fcurve in (
                        fcurve
                        for fcurve in bl_object.animation_data.action.fcurves
                        if fcurve.data_path.startswith("xplane.datarefs[")
                    ):
                        try:
                            data_path_idx = int(
                                re.match(
                                    "xplane\.datarefs\[(\d+)\]\.value", fcurve.data_path
                                ).group(1)
                            )
                        except AttributeError:
                            # We expect tests to be so simple that they only have 1 dataref,
                            # but in case they have multiple...
                            pass
                        except IndexError:  # Is this actually impossible?
                            assert (
                                False
                            ), f"{bl_object.name} has data_path as out of index: {expected_path}"
                        else:
                            # Unit tests are so carefuly authored
                            # we don't need error handling here.
                            # fcurves and datarefs will be 1:1
                            dataref_prop = bl_object.xplane.datarefs[data_path_idx]
                            if dataref_prop.path == expected_path:
                                return (fcurve, dataref_prop)
                    else:  # no early return
                        assert (
                            False
                        ), f"{expected_path} was not found in {bl_object.name}"

                # ----end get_dataref_prop_from_data_path----------------------

                expected_path = expected_inter_anim.xp_dataref.path
                xp_fcurve, dataref_prop = get_dataref_prop_from_data_path(
                    bl_object, expected_path
                )
                xp_values: List[float] = [k.co[1] for k in xp_fcurve.keyframe_points]
                action_as_intermediate_animation.xp_dataref = xplane_imp_cmd_builder.IntermediateDataref(
                    anim_type=dataref_prop.anim_type,
                    loop=dataref_prop.loop,
                    path=dataref_prop.path,
                    # Why? The importer tracks these seperately to make optimzations
                    # XPlane2Blender will have the data on one "time line" only
                    location_values=xp_values,
                    rotation_values=xp_values,
                )

                return action_as_intermediate_animation

            # fmt: off
            real_action_struct = action_as_intermediate_animation(bl_object)
            self.assertEqual(real_action_struct.xp_dataref.anim_type,    expected_inter_anim.xp_dataref.anim_type)
            self.assertAlmostEqual(real_action_struct.xp_dataref.loop,   expected_inter_anim.xp_dataref.loop, places=1)
            self.assertEqual(real_action_struct.xp_dataref.path,         expected_inter_anim.xp_dataref.path)
            self.assertAlmostEqual(real_action_struct.xp_dataref.show_hide_v1, expected_inter_anim.xp_dataref.show_hide_v1, places=PRECISION_OBJ_FLOAT)
            self.assertAlmostEqual(real_action_struct.xp_dataref.show_hide_v2, expected_inter_anim.xp_dataref.show_hide_v2, places=PRECISION_OBJ_FLOAT)
            # fmt: on

            for real_loc, expected_loc in zip(
                real_action_struct.locations, expected_inter_anim.locations
            ):
                self.assertVectorAlmostEqual(real_loc, expected_loc, 1)

            for real_rot_degrees, expected_rot_degrees in [
                (
                    real_action_struct.rotations[axis],
                    expected_inter_anim.rotations[axis],
                )
                for axis in real_action_struct.rotations
            ]:
                for real_deg, exp_deg in zip(real_rot_degrees, expected_rot_degrees):
                    self.assertAlmostEqual(real_deg, exp_deg, places=1)

    def assertImportSucceeds(self, filepath: Union[str, pathlib.Path], msg: str = None):
        """
        Tests import succeeds without syntatic or semantic errors.

        If filepath is just a file name, assume a folder called 'fixtures'
        exists in the current directory and check there as a shortcut.

        Appends '.obj' as needed.
        """

        filepath = pathlib.Path(filepath).with_suffix(".obj")
        if len(filepath.parts) == 1:
            filepath = pathlib.Path(
                inspect.currentframe().f_back.f_globals["__file__"]
            ).parent / pathlib.Path("fixtures", filepath)

        try:
            result = xplane_imp_parser.import_obj(filepath)
        except xplane_imp_parser.UnrecoverableParserError:
            self.fail(msg=msg if msg else f"Import of {filepath} did not succeed",)
        else:
            self.assertEqual(
                result,
                "FINISHED",
                msg=f"Import of {filepath} finished parsing but had semantic errors",
            )

    def assertMatricesEqual(self, mA, mB, tolerance=FLOAT_TOLERANCE):
        for row_a, row_b in zip(mA, mB):
            self.assertFloatVectorsEqual(row_a, row_b, tolerance)

    # Utility method to check if objects are contained in file
    def assertObjectsInXPlaneFile(self, xplaneFile, objectNames):
        for name in objectNames:
            # TODO:  Remove/change
            self.assertIsNotNone(xplaneFile._bl_obj_name_to_bone[name])
            self.assertTrue(
                isinstance(
                    xplaneFile._bl_obj_name_to_bone[name].xplaneObject,
                    xplane_primitive.XPlanePrimitive,
                )
            )
            self.assertEquals(
                xplaneFile._bl_obj_name_to_bone[name].blenderObject,
                bpy.data.objects[name],
            )

    def assertVectorAlmostEqual(
        self,
        vec_a: Union[Iterable, Vector],
        vec_b: Union[Iterable, Vector],
        places: int,
    ) -> None:
        """Given two equal length vectors (or any iterable), ask if they are almost equal"""
        for i, (comp_a, comp_b) in enumerate(zip(vec_a, vec_b)):
            self.assertAlmostEqual(
                comp_a,
                comp_b,
                places,
                msg=f"{i}th component: {comp_a:.5f} != {comp_b:.5f}",
            )

    def assertVTTable(
        self, object_a: bpy.types.Object, object_b: bpy.types.Object
    ) -> None:
        o_vt_cos = sorted(
            set(tuple(object_a.matrix_world @ v.co) for v in object_a.data.vertices)
        )
        i_vt_cos = sorted(
            set(tuple(object_b.matrix_world @ v.co) for v in object_b.data.vertices)
        )
        o_vt_normals = sorted(set(tuple(v.normal) for v in object_a.data.vertices))
        i_vt_normals = sorted(set(tuple(v.normal) for v in object_b.data.vertices))
        o_vt_uvs = sorted(set(tuple(v.uv) for v in object_a.data.uv_layers[0].data))
        i_vt_uvs = sorted(set(tuple(v.uv) for v in object_b.data.uv_layers[0].data))
        for i, (o_vt_co, i_vt_co) in enumerate(zip(o_vt_cos, i_vt_cos)):
            self.assertVectorAlmostEqual(o_vt_co, i_vt_co, 1)
        for i, (o_vt_normal, i_vt_normal) in enumerate(zip(o_vt_normals, i_vt_normals)):
            self.assertVectorAlmostEqual(o_vt_normal, i_vt_normal, 1)
        for i, (o_vt_uv, i_vt_uv) in enumerate(zip(o_vt_uvs, i_vt_uvs)):
            self.assertVectorAlmostEqual(o_vt_uv, i_vt_uv, 1)

    def assertXPlaneBoneTreeEqual(
        self,
        file_root_bone: xplane_bone.XPlaneBone,
        fixture_root_bone: xplane_bone.XPlaneBone,
    ) -> None:
        """
        Recurses down two XPlaneBone trees, and compares each XPlaneBone's
        - xplaneObject
        - blenderObject
        - blenderBone

        self.xplaneFile and self.parent are not compared
        """
        assert file_root_bone
        assert fixture_root_bone

        def recursively_check(
            file_bone: xplane_bone.XPlaneBone, fixture_bone: xplane_bone.XPlaneBone
        ) -> None:
            file_bone_name = getattr(file_bone.xplaneObject, "name", "None")
            fixture_bone_name = getattr(fixture_bone.xplaneObject, "name", "None")
            self.assertEqual(
                bool(file_bone.xplaneObject),
                bool(fixture_bone.xplaneObject),
                msg=f"File Bone '{file_bone.getName(ignore_indent_level=True)}'"
                f" and Fixture Bone '{file_bone.getName(ignore_indent_level=True)}'"
                f" don't have the same xplaneObject: ({file_bone_name, fixture_bone_name}),",
            )
            self.assertEqual(file_bone.blenderObject, fixture_bone.blenderObject)
            self.assertEqual(file_bone.blenderBone, fixture_bone.blenderBone)
            self.assertEqual(len(file_bone.children), len(fixture_bone.children))
            for child_file_bone, child_fixture_bone in zip(
                file_bone.children, fixture_bone.children
            ):
                recursively_check(child_file_bone, child_fixture_bone)

        recursively_check(file_root_bone, fixture_root_bone)

    def assertFloatsEqual(self, a: float, b: float, tolerance: float = FLOAT_TOLERANCE):
        """
        Tests if floats are equal, with a default tollerance. The difference between this and assertAlmostEqual
        is that we use abs instead of round, then compare
        """
        if abs(a - b) < tolerance:
            return True
        else:
            raise AssertionError(f"{a} != {b}, within a tolerance of {tolerance}")

    def assertFloatVectorsEqual(
        self, a: int, b: int, tolerance: float = FLOAT_TOLERANCE
    ):
        self.assertEquals(len(a), len(b))
        for a_comp, b_comp in zip(a, b):
            self.assertFloatsEqual(a_comp, b_comp, tolerance)

    def parseFileToLines(self, data: str) -> List[Tuple[Union[float, str]]]:
        """
        Turns a string of \n seperated lines into a list of lines
        without comments or 0 length strings with all numeric parts are converted
        """
        lines = []  # type: List[Union[float,str]]

        def tryToFloat(part: str) -> Union[float, str]:
            try:
                return float(part)
            except (TypeError, ValueError):
                return part

        for line in filter(lambda l: len(l) > 0 and l[0] != "#", data.split("\n")):
            if "#" in line:
                line = line[0 : line.index("#")]
            line = line.strip()
            if line:
                if line.startswith("800"):
                    lines.append(tuple(line.split()))
                else:
                    lines.append(tuple(map(tryToFloat, line.split())))

        return lines

    def assertFilesEqual(
        self,
        a: str,
        b: str,
        filterCallback: Union[FilterLinesCallback, List[str]],
        floatTolerance: float = FLOAT_TOLERANCE,
    ):
        """
        a and b should be the contents of files a and b as returned
        from open(file).read()
        """

        def isnumber(d):
            return isinstance(d, (float, int))

        linesA = self.parseFileToLines(a)
        linesB = self.parseFileToLines(b)

        # if a filter function is provided, additionally filter lines with it
        if isinstance(filterCallback, collections.abc.Collection):
            linesA = [
                line
                for line in linesA
                if any(directive in line[0] for directive in filterCallback)
            ]
            linesB = [
                line
                for line in linesB
                if any(directive in line[0] for directive in filterCallback)
            ]
        else:
            linesA = list(filter(filterCallback, linesA))
            linesB = list(filter(filterCallback, linesB))

        # ensure same number of lines
        try:
            self.assertEquals(len(linesA), len(linesB))
        except AssertionError as e:
            only_in_a = set(linesA) - set(linesB)
            only_in_b = set(linesB) - set(linesA)
            diff = ">" + "\n>".join(
                " ".join(map(str, l))
                for l in (only_in_a if len(only_in_a) > len(only_in_b) else only_in_b)
            )
            diff += "\n\n>" + "\n>".join(
                " ".join(map(str, l))
                for l in (only_in_a if len(only_in_a) < len(only_in_b) else only_in_b)
            )

            raise AssertionError(
                f"Length of filtered parsed lines unequal: " f"{e.args[0]}\n{diff}\n"
            ) from None

        for lineIndex, (lineA, lineB) in enumerate(zip(linesA, linesB)):
            try:
                # print(f"lineA:{lineA}, lineB:{lineB}")
                self.assertEquals(len(lineA), len(lineB))
            except AssertionError as e:
                raise AssertionError(
                    f"Number of line components unequal: {e.args[0]}\n"
                    f"{lineIndex}> {lineA} ({len(lineA)})\n"
                    f"{lineIndex}> {lineB} ({len(lineB)})"
                ) from None

            for linePos, (segmentA, segmentB) in enumerate(zip(lineA, lineB)):
                # assure same values (floats must be compared with tolerance)
                if isnumber(segmentA) and isnumber(segmentB):
                    # TODO: This is too simple! This will make call abs on the <value> AND <angle> in ANIM_rotate_key
                    # which are not semantically the same!
                    # Also not covered are PHI, PSI, and THETA!
                    segmentA = (
                        abs(segmentA)
                        if "rotate" in lineA[0] or "manip_keyframe" in lineA[0]
                        else segmentA
                    )
                    segmentB = (
                        abs(segmentB)
                        if "rotate" in lineB[0] or "manip_keyframe" in lineB[0]
                        else segmentB
                    )
                    try:
                        self.assertFloatsEqual(segmentA, segmentB, floatTolerance)
                    except AssertionError as e:

                        def make_context(source: List[str], segment: str) -> str:
                            current_line = (
                                f"{lineIndex}> {' '.join(map(str, source[lineIndex]))}"
                            )
                            # Makes something like
                            # 480> ATTR_ -0.45643 1.0 sim/test1
                            # ?          ^~~~~~~~
                            # 480> ATTR_ -1.0 1.0 sim/test1
                            # ?          ^~~~
                            question_line = (
                                "?"
                                + " " * (len(str(lineIndex)) + 3)
                                + "^".rjust(
                                    len(" ".join(map(str, lineA[:linePos]))), " "
                                )
                                + "~" * (len(str(segment)) - 1)
                            )

                            return "\n".join(
                                (
                                    f"{lineIndex - 1}: {' '.join(map(str, source[lineIndex-1]))}"
                                    if lineIndex > 0
                                    else "",
                                    current_line,
                                    question_line,
                                    f"{lineIndex + 1}: {' '.join(map(str, source[lineIndex+1]))}"
                                    if lineIndex + 1 < len(source)
                                    else "",
                                )
                            )

                        context_lineA = make_context(linesA, segmentA)
                        context_lineB = make_context(linesB, segmentB)

                        raise AssertionError(
                            e.args[0]
                            + "\n"
                            + "\n\n".join((context_lineA, context_lineB))
                        ) from None
                else:
                    self.assertEquals(segmentA, segmentB)

    def assertFileOutputEqualsFixture(
        self,
        fileOutput: str,
        fixturePath: str,
        filterCallback: Union[FilterLinesCallback, List[str]],
        floatTolerance: float = FLOAT_TOLERANCE,
    ) -> None:
        """
        Compares the output of XPlaneFile.write (a \n separated str) to a fixture on disk.

        A filterCallback ensures only matching lines are compared.
        Highly recommended, with as simple a function as possible to prevent fixture fragility.
        """

        with open(fixturePath, "r") as fixtureFile:
            fixtureOutput = fixtureFile.read()

        return self.assertFilesEqual(
            fileOutput, fixtureOutput, filterCallback, floatTolerance
        )

    def assertFileTmpEqualsFixture(
        self,
        tmpPath: str,
        fixturePath: str,
        filterCallback: Union[FilterLinesCallback, List[str]],
        floatTolerance: float = FLOAT_TOLERANCE,
    ):
        tmpFile = open(tmpPath, "r")
        tmpOutput = tmpFile.read()
        tmpFile.close()

        return self.assertFileOutputEqualsFixture(
            tmpOutput, fixturePath, filterCallback, floatTolerance
        )

    def assertLoggerErrors(self, expected_logger_errors: int) -> None:
        """
        Asserts the logger has some number of errors, then clears the logger
        of all messages
        """
        try:
            found_errors = len(logger.findErrors())
            self.assertEqual(found_errors, expected_logger_errors)
        except AssertionError as e:
            raise AssertionError(
                f"Expected {expected_logger_errors} logger errors, got {found_errors}"
            ) from None
        else:
            logger.clearMessages()

    # TODO: Must filter warnings to have this be useful
    # Method: assertLoggerWarnings
    #
    # expected_logger_warnings - The number of warnings you expected to have happen
    # asserts the number of warnings and clears the logger of all messages
    # def assertLoggerWarnings(self, expected_logger_warnings):
    #    self.assertEqual(len(logger.findWarnings()), expected_logger_warnings)
    #    logger.clearMessages()

    def assertLayerExportEqualsFixture(
        self,
        layer_number: int,
        fixturePath: str,
        filterCallback: Union[FilterLinesCallback, List[str]],
        tmpFilename: Optional[str] = None,
        floatTolerance: float = FLOAT_TOLERANCE,
    ) -> None:
        """
        DEPRECATED: New unit tests should not use this!

        - layer_number starts at 0, as it used to access the scene.layers collection
        """
        # if not ('-q' in sys.argv or '--quiet' in sys.argv):
        #     print("Comparing: '%s', '%s'" % (tmpFilename, fixturePath))

        out = self.exportExportableRoot(
            bpy.data.collections[f"Layer {layer_number + 1}"], tmpFilename
        )
        self.assertFileOutputEqualsFixture(
            out, fixturePath, filterCallback, floatTolerance
        )

    def assertExportableRootExportEqualsFixture(
        self,
        root_object: Union[bpy.types.Collection, bpy.types.Object, str],
        fixturePath: str,
        filterCallback: [Union[FilterLinesCallback, List[str]]],
        tmpFilename: Optional[str] = None,
        floatTolerance: float = FLOAT_TOLERANCE,
    ) -> None:
        """
        Exports only a specific exportable root and compares the output
        to a fixutre.

        If filterCallback is a List[str], those directives will be filtered
        will be used. Tip: Use TRIS or POINT_COUNTS instead of VT.
        """
        out = self.exportExportableRoot(root_object, tmpFilename)
        self.assertFileOutputEqualsFixture(
            out, fixturePath, filterCallback, floatTolerance
        )

    # asserts that an attributes object equals a dict
    def assertAttributesEqualDict(
        self,
        attrs: List[Union[str, xplane_attribute.XPlaneAttribute]],
        d: Dict[str, Any],
        floatTolerance: float = FLOAT_TOLERANCE,
    ):
        self.assertEquals(
            len(d),
            len(attrs),
            f"Attribute lists {list(d.keys())}, {list(attrs.keys())} have different length",
        )

        for name in attrs:
            attr = attrs[name]
            value = attr.getValue()
            expectedValue = d[name]

            if isinstance(expectedValue, (list, tuple)):
                self.assertIsInstance(
                    value,
                    (list, tuple),
                    msg='Attribute value for "%s" is no list or tuple but: %s',
                )
                self.assertEquals(
                    len(expectedValue),
                    len(value),
                    'Attribute values for "%s" have different length' % name,
                )

                for i, (v, expectedV) in enumerate(zip(value, expectedValue)):
                    if isinstance(expectedV, (float, int)):
                        self.assertFloatsEqual(expectedV, v, floatTolerance)
                    else:
                        self.assertEquals(
                            expectedV,
                            v,
                            'Attribute list value %d for "%s" is different' % (i, name),
                        )
            else:
                self.assertEquals(
                    expectedValue, value, 'Attribute "%s" is not equal' % name
                )

    def createXPlaneFileFromPotentialRoot(
        self,
        potential_root: Union[xplane_helpers.PotentialRoot, str],
        view_layer: Optional[bpy.types.ViewLayer] = None,
    ) -> xplane_file.XPlaneFile:
        """
        A thin wrapper around xplane_file.createFileFromBlenderObject, where the potential root
        temporarily is made exportable.
        """
        potential_root = (
            test_creation_helpers.lookup_potential_root_from_name(potential_root)
            if isinstance(potential_root, str)
            else potential_root
        )

        view_layer = view_layer or bpy.context.scene.view_layers[0]
        with TemporarilyMakeRootExportable(potential_root, view_layer):
            xp_file = xplane_file.createFileFromBlenderRootObject(
                potential_root, view_layer
            )

        return xp_file

    def exportLayer(
        self, layer_number: int, dest: Optional[str] = None, force_visible=True
    ) -> str:
        """
        DEPRECATED: New unit tests should not use this!

        - layer_number starts at 0, as it used to access the scene.layers collection
        - dest is a filepath without the file extension .obj, written to the TMP_DIR if not None
        """
        return self.exportExportableRoot(
            bpy.data.collections[f"Layer {layer_number + 1}"], dest, force_visible=True
        )

    def exportExportableRoot(
        self,
        potential_root: Union[xplane_helpers.PotentialRoot, str],
        dest: Optional[str] = None,
        force_visible=True,
        view_layer: Optional[bpy.types.ViewLayer] = None,
    ) -> str:
        """
        Returns the result of calling xplaneFile.write()

        - dest is a filepath without the file extension .obj, writes result to the TMP_DIR if not None
        - force_visible forces a potential_root to be visible
        - view_layer is needed for checking if potential_root is visible, when None
          the current scene's 1st view layer is used

        If an XPlaneFile could not be made, a ValueError will bubble up
        """
        view_layer = view_layer or bpy.context.scene.view_layers[0]
        assert isinstance(
            potential_root, (bpy.types.Collection, bpy.types.Object, str)
        ), f"root_object type ({type(potential_root)}) isn't allowed, must be Collection, Object, or str"
        if isinstance(potential_root, str):
            try:
                potential_root = bpy.data.collections[potential_root]
            except KeyError:
                try:
                    potential_root = bpy.data.objects[potential_root]
                except KeyError:
                    assert (
                        False
                    ), f"{potential_root} must be in bpy.data.collections|objects"

        if force_visible:
            xp_file = self.createXPlaneFileFromPotentialRoot(potential_root, view_layer)
        else:
            xp_file = xplane_file.createFileFromBlenderRootObject(
                potential_root, view_layer
            )
        out = xp_file.write()
        xplane_file._all_keyframe_infos.clear()

        if dest:
            with open(os.path.join(get_tmp_folder(), dest + ".obj"), "w") as tmp_file:
                tmp_file.write(out)

        return out

    @staticmethod
    def get_XPlane2Blender_log_content() -> List[str]:
        """
        Returns the content of the log file after export as a collection of lines, no trailing new lines,
        or KeyError if the text block doesn't exist yet (rare).
        """
        return [l.body for l in bpy.data.texts["XPlane2Blender.log"].lines]


class XPlaneAnimationTestCase(XPlaneTestCase):
    def setUp(self):
        super(XPlaneAnimationTestCase, self).setUp()

    def exportAnimationTestCase(self, name, dest):
        self.assertTrue(animation_file_mappings.mappings[name])

        for layer in animation_file_mappings.mappings[name]:
            outFile = os.path.join(
                dest, os.path.basename(animation_file_mappings.mappings[name][layer])
            )
            print('Exporting to "%s"' % outFile)

            io_xplane2blender.tests.test_creation_helpers.make_root_exportable(
                bpy.data.collections[f"Layer {layer + 1}"]
            )
            try:
                xplaneFile = xplane_file.createFileFromBlenderRootObject(
                    bpy.data.collections[f"Layer {layer + 1}"],
                    bpy.context.scene.view_layers[0],
                )
            except xplane_file.NotExportableRootError:
                assert (
                    False
                ), f"Unable to create XPlaneFile for {name} from Layer {layer + 1}"
            else:
                with open(outFile, "w") as outFile:
                    out = xplaneFile.write()
                    outFile.write(out)

    def runAnimationTestCase(self, name, __dirname__):
        self.assertTrue(animation_file_mappings.mappings[name])

        def filterLine(line):
            # only keep ANIM_ lines
            return isinstance(line[0], str) and ("ANIM" in line[0] or "TRIS" in line[0])

        for layer in animation_file_mappings.mappings[name]:
            # print('Testing animations against fixture "%s"' % mappings[name][layer])
            bpy.data.collections[f"Layer {layer + 1}"].hide_viewport = False
            xplaneFile = self.createXPlaneFileFromPotentialRoot(
                bpy.data.collections[f"Layer {layer + 1}"]
            )

            self.assertIsNotNone(
                xplaneFile,
                "Unable to create XPlaneFile for %s layer %d" % (name, layer),
            )

            out = xplaneFile.write()
            fixtureFile = os.path.join(
                __dirname__, animation_file_mappings.mappings[name][layer]
            )

            self.assertTrue(
                os.path.exists(fixtureFile), 'File "%s" does not exist' % fixtureFile
            )
            self.assertFileOutputEqualsFixture(out, fixtureFile, filterLine)


def get_source_folder() -> pathlib.Path:
    """Returns the full path to the addon folder"""
    return pathlib.Path(__file__).parent


def get_project_folder() -> pathlib.Path:
    """Returns the full path to the project folder"""
    return pathlib.Path(__file__).parent.parent.parent


def get_tests_folder() -> pathlib.Path:
    return pathlib.Path(get_project_folder(), "tests")


def get_tmp_folder() -> pathlib.Path:
    return os.path.realpath(os.path.join(__dirname__, "../../tests/tmp"))


def make_fixture_path(dirname, filename, sub_dir=""):
    return os.path.join(dirname, "fixtures", sub_dir, filename + ".obj")


def runTestCases(testCases):
    # Until a better solution for knowing if the logger's error count should be used to quit the testing,
    # we are currently saying only 1 is allow per suite at a time (which is likely how it should be anyways)
    assert (
        len(testCases) == 1
    ), "Currently, only one test case per suite is supported at a time"
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(testCases[0])
    test_result = unittest.TextTestRunner().run(suite)

    # See XPlane2Blender/tests.py for documentation. The strings must be kept in sync!
    # This is not an optional debug print statement! The test runner needs this print statement to function
    print(
        f"RESULT: After {(test_result.testsRun)} tests got {len(test_result.errors)} errors, {len(test_result.failures)} failures, and {len(test_result.skipped)} skipped"
    )
