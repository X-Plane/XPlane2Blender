import inspect

from typing import Tuple
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.xplane_types import xplane_light
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers

__dirname__ = os.path.dirname(__file__)

class TestAutomaticLightProperties(XPlaneTestCase):
    #TI as per unittest requirements, all test methods must start with "test_"
    def test_automatic_light_properties(self)->None:
        filename = inspect.stack()[0].function

        self.assertExportableRootExportEqualsFixture(
            filename[5:],
            os.path.join(__dirname__, "fixtures", f"{filename}.obj"),
            {"ANIM", "LIGHT"},
            filename,
        )

    def test_stripped_light_name(self)->None:
        ob = bpy.data.objects["taxi_y_spaces_stripped"]
        light_name_to_strip = "    taxi_y  "
        ob.data.xplane.name = light_name_to_strip
        self.assertEqual(ob.data.xplane.name,  light_name_to_strip.strip())

runTestCases([TestAutomaticLightProperties])
