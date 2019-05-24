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
    def test_01_good_ATTR_no_shadow(self):
        filename = inspect.stack()[0].function
        self.assertRootObjectExportEqualsFixture(
            bpy.data.objects[filename[5:]],
            os.path.join(__dirname__, '..', 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

    def test_02_good_ATTR_shadow_on_off_on(self):
        filename = inspect.stack()[0].function
        self.assertRootObjectExportEqualsFixture(
            bpy.data.objects[filename[5:]],
            os.path.join(__dirname__, '..', 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

    def test_03_good_GLOBAL_no_shadow_only(self):
        filename = inspect.stack()[0].function
        self.assertRootObjectExportEqualsFixture(
            bpy.data.objects[filename[5:]],
            os.path.join(__dirname__, '..', 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

    def test_04_bad_GLOBAL_no_shadow_ATTR_shadow(self):
        filename = inspect.stack()[0].function
        out = self.exportRootObject(bpy.data.objects[filename[5:]])
        self.assertLoggerErrors(1)

    def test_05_ignored_export_type_aircraft(self):
        filename = inspect.stack()[0].function
        self.assertRootObjectExportEqualsFixture(
            bpy.data.objects[filename[5:]],
            os.path.join(__dirname__, '..', 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

    def test_06_ignored_export_type_cockpit(self):
        filename = inspect.stack()[0].function
        self.assertRootObjectExportEqualsFixture(
            bpy.data.objects[filename[5:]],
            os.path.join(__dirname__, '..', 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )


runTestCases([TestShadowNoShadow])
