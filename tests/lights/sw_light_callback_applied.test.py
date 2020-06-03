import bpy
import mathutils

import os
import inspect
import sys

from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config, xplane_constants
from io_xplane2blender.xplane_types import xplane_light
from io_xplane2blender.xplane_utils import xplane_lights_txt_parser

__dirname__ = os.path.dirname(__file__)

class TestSwLightCallbackApplied(XPlaneTestCase):
    def test_sw_light_callback_used(self):
        filename = inspect.stack()[0].function
        self.assertExportableRootExportEqualsFixture(
            filename[5:],
            os.path.join(__dirname__, "fixtures", f"{filename}.obj"),
            {"LIGHT_"},
            filename,
        )


runTestCases([TestSwLightCallbackApplied])
