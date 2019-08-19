import inspect
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *

__dirname__ = os.path.dirname(__file__)

def filterLines(line):
    return isinstance(line[0],str) and\
            ("GLOBAL_no_shadow" in line[0] or\
             "ATTR_shadow" in line[0] or\
             "ATTR_no_shadow" in line[0])

class TestShadowNoShadowNonSceneryType(XPlaneTestCase):
    def test_01_all_cast_local_off(self):
        filename = inspect.stack()[0].function
        self.assertRootObjectExportEqualsFixture(
            bpy.data.objects[filename[5:]],
            os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

    def test_02_all_cast_local_on(self):
        filename = inspect.stack()[0].function
        self.assertRootObjectExportEqualsFixture(
            bpy.data.objects[filename[5:]],
            os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

    def test_03a_1_cast_local_off(self):
        filename = inspect.stack()[0].function
        self.assertRootObjectExportEqualsFixture(
            bpy.data.objects[filename[5:]],
            os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

    def test_03b_1_or_more_cast_local_off_on_off(self):
        filename = inspect.stack()[0].function
        self.assertRootObjectExportEqualsFixture(
            bpy.data.objects[filename[5:]],
            os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )


runTestCases([TestShadowNoShadowNonSceneryType])
