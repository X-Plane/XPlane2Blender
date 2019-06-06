import inspect
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *

__dirname__ = os.path.dirname(__file__)

#TI filter obj output. Define above or in the class level
#def filterLines(line):
    #return isinstance(line[0],str) and\
            #("OBJ_DIRECTIVE" in line[0] or\

class TestShadowLocalOffLayersMode(XPlaneTestCase):
    def test_01_global_off(self):
        for mat in [bpy.data.materials["Material_shadow_should_be_off_1"],
                    bpy.data.materials["Material_shadow_should_be_off_2"],
                    bpy.data.materials["Material_shadow_should_be_off_3"],]:
            self.assertFalse(mat.xplane.shadow_local)
        self.assertIsNone(bpy.context.scene.xplane.layers[0].get("shadow"))

    def test_02_global_on(self):
        for mat in [bpy.data.materials["Material_shadow_should_be_on_1"],
                    bpy.data.materials["Material_shadow_should_be_on_2"],
                    bpy.data.materials["Material_shadow_should_be_on_3"],]:
            self.assertTrue(mat.xplane.shadow_local)
        self.assertIsNone(bpy.context.scene.xplane.layers[1].get("shadow"))

    def test_03_global_off_shared(self):
        pass

    def test_04_global_on_shared(self):
        pass


runTestCases([TestShadowLocalOffLayersMode])
