import inspect
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *

__dirname__ = os.path.dirname(__file__)

def filterLines(line):
    return isinstance(line[0],str) and\
            ("VT" in line[0]    or\
             "IDX10" in line[0] or\
             "IDX"  in line[0]  or\
             "TRIS" in line[0]  or\
             "ANIM" in line[0])

class TestArmatureNestedOffset(XPlaneTestCase):
    def test_01_datablock_datablock(self):
        filename = inspect.stack()[0][3]

        self.assertLayerExportEqualsFixture(
            0, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

    def test_02_bone_datablock(self):
        filename = inspect.stack()[0][3]

        self.assertLayerExportEqualsFixture(
            1, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

    def test_03_bone_bone_connected_offset_translation(self):
        filename = inspect.stack()[0][3]

        self.assertLayerExportEqualsFixture(
            2, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

    def test_05_bone_bone_connected_no_offset_translation(self):
        filename = inspect.stack()[0][3]

        self.assertLayerExportEqualsFixture(
            4, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

runTestCases([TestArmatureNestedOffset])
