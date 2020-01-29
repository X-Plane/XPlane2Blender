import inspect
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *

__dirname__ = os.path.dirname(__file__)

def filterLines(line):
    return isinstance(line[0],str) and\
            ("ATTR_shadow" in line[0] or\
             "ATTR_no_shadow" in line[0])

class TestShadowNoShadow(XPlaneTestCase):
    def test_01_all_cast_shadows_off(self):
        filename = inspect.stack()[0].function
        self.assertExportableRootExportEqualsFixture(
            bpy.data.objects[filename[5:]],
            os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

    def test_02_all_cast_shadows_on(self):
        filename = inspect.stack()[0].function
        self.assertExportableRootExportEqualsFixture(
            bpy.data.objects[filename[5:]],
            os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

    def test_03_1_cast_shadows_off(self):
        filename = inspect.stack()[0].function
        self.assertExportableRootExportEqualsFixture(
            bpy.data.objects[filename[5:]],
            os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

    def test_04_1_or_more_but_not_all_off(self):
        filename = inspect.stack()[0].function
        self.assertExportableRootExportEqualsFixture(
            bpy.data.objects[filename[5:]],
            os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )


    def test_05_all_cast_shadows_off_non_scenery(self):
        filename = inspect.stack()[0].function
        self.assertExportableRootExportEqualsFixture(
            bpy.data.objects[filename[5:]],
            os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )


runTestCases([TestShadowNoShadow])
