import bpy
import os
import inspect
import sys

from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config

__dirname__ = os.path.dirname(__file__)

def filterLines(line):
    return isinstance(line[0],str) and\
            ("LIGHT_CUSTOM" in line[0])

class TestCustomLightRGBOverride(XPlaneTestCase):
    def test_Custom_Spot_RGB_values_disabled(self):
        filename = inspect.stack()[0][3]

        self.assertLayerExportEqualsFixture(
            0, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filterLines,
            filename,
        )

    def test_Custom_Spot_RGB_values_enabled(self):
        filename = inspect.stack()[0][3]

        self.assertLayerExportEqualsFixture(
            1, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filterLines,
            filename,
        )

runTestCases([TestCustomLightRGBOverride])
