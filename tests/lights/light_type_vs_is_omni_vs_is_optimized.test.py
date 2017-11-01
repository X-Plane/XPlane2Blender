import bpy
import os
import inspect
import sys

from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config

__dirname__ = os.path.dirname(__file__)

def filterLines(line):
    return isinstance(line[0],str) and\
            ("LIGHT_PARAM" in line[0] or\
             "ANIM" in line[0])

class TestLightTypeVsIsOmniVsIsOptimized(XPlaneTestCase):
    def test_point_vs_is_omni_vs_is_optimized(self):
        filename = inspect.stack()[0][3]

        self.assertLayerExportEqualsFixture(
            0, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

    def test_spot_vs_is_omni_vs_is_optimized(self):
        filename = inspect.stack()[0][3]
        
        self.assertLayerExportEqualsFixture(
            1, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

runTestCases([TestLightTypeVsIsOmniVsIsOptimized])
