import bpy
import os
import inspect
import sys

from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config
from io_xplane2blender.xplane_types import xplane_light

__dirname__ = os.path.dirname(__file__)
 
class TestParamLightParams(XPlaneTestCase):
    def test_comment_correct(self):
        light = xplane_light.XPlaneLight(bpy.data.objects["4_comment contents_preserved_exactly"])
        light.collect()
        self.assertTrue(light.parsed_params["COMMENT"] == "0 spaces, number starts comment with uneven and a   trailing  space ")

        out  = self.exportLayer(0)
        self.assertLoggerErrors(0)

    def test_illegal_params_content(self):
        out = self.exportLayer(1)
        self.assertLoggerErrors(3)

runTestCases([TestParamLightParams])

