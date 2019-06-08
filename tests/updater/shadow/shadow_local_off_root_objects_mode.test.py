import inspect
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *

__dirname__ = os.path.dirname(__file__)

def filterLines(line):
    return isinstance(line[0],str) and\
            ("GLOBAL_no_shadow" in line[0]
             or "ATTR_shadow" in line[0]
             or "ATTR_no_shadow" in line[0])

class TestShadowLocalOffRootObjectsMode(XPlaneTestCase):
    def test_properties_correct(self):
        for mat in [bpy.data.materials["Material_shadow_should_be_off_1"],
                    bpy.data.materials["Material_shadow_should_be_off_2"],
                    bpy.data.materials["Material_shadow_should_be_off_3"],]:
            self.assertFalse(mat.xplane.shadow_local)

        for mat in [bpy.data.materials["Material_shadow_should_be_on_1"],
                    bpy.data.materials["Material_shadow_should_be_on_2"],
                    bpy.data.materials["Material_shadow_should_be_on_3"],]:
            self.assertTrue(mat.xplane.shadow_local)

        for root_name in ["01_global_off", "02_global_on", "03_global_off_shared", "04_global_on_shared"]:
            self.assertIsNone(bpy.data.objects[root_name].xplane.layer.get("shadow"))

    def test_01_global_off(self):
        filename = inspect.stack()[0].function
        self.assertRootObjectExportEqualsFixture(
                bpy.data.objects[filename[5:]],
                os.path.join(__dirname__, 'fixtures', filename + '_root_objects.obj'),
                filename,
                filterLines
            )

    def test_02_global_on(self):
        filename = inspect.stack()[0].function
        self.assertRootObjectExportEqualsFixture(
                bpy.data.objects[filename[5:]],
                os.path.join(__dirname__, 'fixtures', filename + '_root_objects.obj'),
                filename,
                filterLines
            )

    """
    def test_03_global_off_shared(self):
        filename = inspect.stack()[0].function
        self.assertRootObjectExportEqualsFixture(
                bpy.data.objects[filename[5:]],
                os.path.join(__dirname__, 'fixtures', filename + '_root_objects.obj'),
                filename,
                filterLines
            )

    def test_04_global_on_shared(self):
        filename = inspect.stack()[0].function
        self.assertRootObjectExportEqualsFixture(
                bpy.data.objects[filename[5:]],
                os.path.join(__dirname__, 'fixtures', filename + '_root_objects.obj'),
                filename,
                filterLines
            )
    """


runTestCases([TestShadowLocalOffRootObjectsMode])
