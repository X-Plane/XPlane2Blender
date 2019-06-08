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
                 or "ATTR_no_shadow"))

class TestShadowLocalOffLayersMode(XPlaneTestCase):
    def test_properties_correct(self):
        for mat in [bpy.data.materials["Material_shadow_should_be_off_1"],
                    bpy.data.materials["Material_shadow_should_be_off_2"],
                    bpy.data.materials["Material_shadow_should_be_off_3"],]:
            self.assertFalse(mat.xplane.shadow_local)

        for mat in [bpy.data.materials["Material_shadow_should_be_on_1"],
                    bpy.data.materials["Material_shadow_should_be_on_2"],
                    bpy.data.materials["Material_shadow_should_be_on_3"],]:
            self.assertTrue(mat.xplane.shadow_local)

        for layer_idx in range(4):
            self.assertIsNone(bpy.context.scene.xplane.layers[layer_idx].get("shadow"))

    def test_01_global_off(self):
        filename = inspect.stack()[0].function + "_layers"
        self.assertLayerExportEqualsFixture(
            0,
            os.path.join(__dirname__, "fixtures", filename + ".obj"),
            filename,
            filterLines
        )

    def test_02_global_on(self):
        filename = inspect.stack()[0].function + "_layers"
        self.assertLayerExportEqualsFixture(
            1,
            os.path.join(__dirname__, "fixtures", filename + ".obj"),
            filename,
            filterLines
        )

    '''
    def test_03_global_off_shared(self):
        filename = inspect.stack()[0].function + "_layers"
        self.assertLayerExportEqualsFixture(
            2,
            os.path.join(__dirname__, "fixtures", filename + ".obj"),
            filename,
            filterLines
        )

    def test_04_global_on_shared(self):
        filename = inspect.stack()[0].function + "_layers"
        self.assertLayerExportEqualsFixture(
            3,
            os.path.join(__dirname__, "fixtures", filename + ".obj"),
            filename,
            filterLines
        )
    '''


runTestCases([TestShadowLocalOffLayersMode])
