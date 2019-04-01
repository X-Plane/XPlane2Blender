import inspect
import os
import sys

import bpy
from io_xplane2blender import xplane_config, xplane_constants
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_249_converter.xplane_249_constants import WorkflowType

__dirname__ = os.path.dirname(__file__)

def filterLines(line):
    return isinstance(line[0],str) and\
            ("VLIGHT" in line[0] and
             "LIGHTS" in line[0])

class TestConvertLightsCustom(XPlaneTestCase):
    def test_DatarefCustom(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        filename = inspect.stack()[0].function

        self.assertRootObjectExportEqualsFixture(
        "OBJ" + filename, os.path.join(__dirname__, 'fixtures', filename + ".obj"),
            filename,
                filterLines
            )

    def test_DatarefError(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        filename = inspect.stack()[0].function

        self.assertRootObjectExportEqualsFixture(
        "OBJ" + filename, os.path.join(__dirname__, 'fixtures', filename + ".obj"),
            filename,
                filterLines
            )

    def test_DatarefKnown(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        filename = inspect.stack()[0].function

        self.assertRootObjectExportEqualsFixture(
        "OBJ" + filename, os.path.join(__dirname__, 'fixtures', filename + ".obj"),
            filename,
                filterLines
            )

    def test_DatarefNone(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        filename = inspect.stack()[0].function

        self.assertRootObjectExportEqualsFixture(
        "OBJ" + filename, os.path.join(__dirname__, 'fixtures', filename + ".obj"),
            filename,
                filterLines
            )

    def test_MultiVert(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        filename = inspect.stack()[0].function

        self.assertRootObjectExportEqualsFixture(
        "OBJ" + filename, os.path.join(__dirname__, 'fixtures', filename + ".obj"),
            filename,
                filterLines
            )

    def test_RGBAFromMat(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        filename = inspect.stack()[0].function

        self.assertRootObjectExportEqualsFixture(
        "OBJ" + filename, os.path.join(__dirname__, 'fixtures', filename + ".obj"),
            filename,
                filterLines
            )

    def test_RGBAFromMixed(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        filename = inspect.stack()[0].function

        self.assertRootObjectExportEqualsFixture(
        "OBJ" + filename, os.path.join(__dirname__, 'fixtures', filename + ".obj"),
            filename,
                filterLines
            )

    def test_RGBAFromProps(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        filename = inspect.stack()[0].function

        self.assertRootObjectExportEqualsFixture(
        "OBJ" + filename, os.path.join(__dirname__, 'fixtures', filename + ".obj"),
            filename,
                filterLines
            )

    def test_TexGivesUV(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        filename = inspect.stack()[0].function

        self.assertRootObjectExportEqualsFixture(
        "OBJ" + filename, os.path.join(__dirname__, 'fixtures', filename + ".obj"),
            filename,
                filterLines
            )


runTestCases([TestConvertLightsCustom])
