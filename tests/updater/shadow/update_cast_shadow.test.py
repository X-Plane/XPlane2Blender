import inspect

from typing import Tuple

import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *

__dirname__ = os.path.dirname(__file__)

def filterLines(line:Tuple[str])->bool:
    return (isinstance(line[0],str)
            and ("GLOBAL_no_shadow" in line[0]
                 or "ATTR_shadow" in line[0]
                 or "ATTR_no_shadow" in line[0]))

class TestUpdateCastShadow(XPlaneTestCase):
    def test_properties_correct(self):
        for mat in [bpy.data.materials["Material_shadow_should_be_off_1"],
                    bpy.data.materials["Material_shadow_should_be_off_2"],
                    bpy.data.materials["Material_shadow_should_be_off_3"],]:
            self.assertFalse(mat.xplane.shadow_local)

        for mat in [bpy.data.materials["Material_shadow_should_be_on_1"],
                    bpy.data.materials["Material_shadow_should_be_on_2"],
                    bpy.data.materials["Material_shadow_should_be_on_3"],]:
            self.assertTrue(mat.xplane.shadow_local)

        # Test that every layer.shadow property was removed as well
        for scene in bpy.data.scenes:
            for exportable_root in xplane_helpers.get_exportable_roots_in_scene(scene, scene.view_layers[0]):
                self.assertIsNone(exportable_root.xplane.layer.get("shadow"), msg=f"Exportable Root {exportable_root.name}'s 'shadow' is {exportable_root.xplane.layer.get('shadow')}, not None")

        for obj in bpy.data.objects:
            self.assertIsNone(obj.xplane.layer.get("shadow"), msg=f"Object {obj.name}'s 'shadow' is {obj.xplane.layer.get('shadow')}, not None")

    def test_01_global_off_layers(self):
        bpy.context.window.scene = bpy.data.scenes["Scene_layers_mode"]
        filename = inspect.stack()[0].function
        self.assertLayerExportEqualsFixture(
            0,
            os.path.join(__dirname__, "fixtures", filename + ".obj"),
            filterLines,
            filename,
        )

    @unittest.skip
    def test_02_global_on_layers(self):
        bpy.context.window.scene = bpy.data.scenes["Scene_layers_mode"]
        filename = inspect.stack()[0].function
        self.assertLayerExportEqualsFixture(
            1,
            os.path.join(__dirname__, "fixtures", filename + ".obj"),
            filterLines,
            filename,
        )

    """
    def test_03_global_off_shared(self):
        filename = inspect.stack()[0].function + "_layers"
        self.assertLayerExportEqualsFixture(
            2,
            os.path.join(__dirname__, "fixtures", filename + ".obj"),
            filterLines,
            filename,
        )

    def test_04_global_on_shared(self):
        filename = inspect.stack()[0].function + "_layers"
        self.assertLayerExportEqualsFixture(
            3,
            os.path.join(__dirname__, "fixtures", filename + ".obj"),
            filterLines,
            filename,
        )
    """

    @unittest.skip
    def test_01_global_off_root_objects(self):
        bpy.context.window.scene = bpy.data.scenes["Scene_root_objects_mode"]
        filename = inspect.stack()[0].function
        self.assertExportableRootExportEqualsFixture(
                bpy.data.objects["01_global_off.001"],
                os.path.join(__dirname__, 'fixtures', filename + '.obj'),
                filterLines,
                filename,
            )

    @unittest.skip
    def test_02_global_on_root_objects(self):
        bpy.context.window.scene = bpy.data.scenes["Scene_root_objects_mode"]
        filename = inspect.stack()[0].function
        self.assertExportableRootExportEqualsFixture(
                bpy.data.objects["02_global_on.001"],
                os.path.join(__dirname__, 'fixtures', filename + '.obj'),
                filterLines,
                filename,
            )

    """
    def test_03_global_off_shared_root(self):
        filename = inspect.stack()[0].function
        self.assertExportableRootExportEqualsFixture(
                bpy.data.objects[filename[5:]],
                os.path.join(__dirname__, 'fixtures', filename + '_root_objects.obj'),
                filterLines,
                filename,
            )

    def test_04_global_on_shared_root(self):
        filename = inspect.stack()[0].function
        self.assertExportableRootExportEqualsFixture(
                bpy.data.objects[filename[5:]],
                os.path.join(__dirname__, 'fixtures', filename + '_root_objects.obj'),
                filterLines,
                filename,
            )
    """

runTestCases([TestUpdateCastShadow])
