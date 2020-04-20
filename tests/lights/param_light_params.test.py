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
        filename = inspect.stack()[0].function
        xplaneFile = self.createXPlaneFileFromPotentialRoot("Layer 1")
        light = xplaneFile._bl_obj_name_to_bone["04_comment_contents_preserved_exactly"].xplaneObject
        self.assertEqual(light.comment, "0 spaces, number starts comment with uneven and a   trailing  space ")

    def test_illegal_params_content(self):
        out = self.exportLayer(1)
        self.assertLoggerErrors(3)

    def test_unused_param_pass(self):
        filename = inspect.stack()[0].function

        self.assertExportableRootExportEqualsFixture(
            filename[5:],
            os.path.join(__dirname__, "fixtures", f"{filename}.obj"),
            {"LIGHT_PARAM"},
            filename,
        )

    def test_unused_param_fail(self):
        out = self.exportLayer(3)
        self.assertLoggerErrors(2)

runTestCases([TestParamLightParams])

