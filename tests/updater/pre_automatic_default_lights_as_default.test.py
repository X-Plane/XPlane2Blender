import inspect

from typing import Tuple
import os
import sys

import bpy
from io_xplane2blender import xplane_constants, xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers


class TestPreAutomaticDefaultLightsAsDefault(XPlaneTestCase):
    def test_update_preserves_default_light_type(self)->None:
        for light in bpy.data.lights:
            self.assertEqual(light.xplane.type, xplane_constants.LIGHT_DEFAULT)


runTestCases([TestPreAutomaticDefaultLightsAsDefault])
