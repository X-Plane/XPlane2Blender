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

class TestShadowLocalOffNonScenery(XPlaneTestCase):
    def test_properties_correct(self):
        for mat in [bpy.data.materials["Material_shadow_should_be_on_1_shared"],
                    bpy.data.materials["Material_shadow_should_be_on_2_shared"],]:
            self.assertTrue(mat.xplane.shadow_local)

        for coll in bpy.data.collections:
            self.assertIsNone(coll.xplane.get("shadow"))

        self.assertIsNone(bpy.data.objects["01_aircraft_force_global_shadows_root"].get("shadow"))
        self.assertIsNone(bpy.data.objects["02_cockpit_force_global_shadows_root"].get("shadow"))

    def test_01_aircraft_force_global_shadows(self):
        bpy.context.window_manager.windows[0].scene = bpy.data.scenes["Scene_layers"]
        filename = inspect.stack()[0].function
        self.assertLayerExportEqualsFixture(
            0,
            os.path.join(__dirname__, "fixtures", filename + ".obj"),
            filterLines,
            filename,
        )

    def test_02_cockpit_force_global_shadows(self):
        bpy.context.window_manager.windows[0].scene = bpy.data.scenes["Scene_layers"]
        filename = inspect.stack()[0].function
        self.assertLayerExportEqualsFixture(
            1,
            os.path.join(__dirname__, "fixtures", filename + ".obj"),
            filterLines,
            filename,
        )

    def test_01_aircraft_force_global_shadows_root(self):
        bpy.context.window_manager.windows[0].scene = bpy.data.scenes["Scene_root_objects"]
        filename = inspect.stack()[0].function
        self.assertExportableRootExportEqualsFixture(
            bpy.data.objects[filename[5:]],
            os.path.join(__dirname__, "fixtures", filename + ".obj"),
            filterLines,
            filename,
        )

    def test_02_cockpit_force_global_shadows_root(self):
        bpy.context.window_manager.windows[0].scene = bpy.data.scenes["Scene_root_objects"]
        filename = inspect.stack()[0].function
        self.assertExportableRootExportEqualsFixture(
            bpy.data.objects[filename[5:]],
            os.path.join(__dirname__, "fixtures", filename + ".obj"),
            filterLines,
            filename,
        )


runTestCases([TestShadowLocalOffNonScenery])
