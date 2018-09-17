import inspect
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *

__dirname__ = os.path.dirname(__file__)

def filterLines(line):
    return isinstance(line[0],str) and\
            ("VT" in line[0] or\
            "IDX" in line[0] or\
            "ANIM" in line[0])

class TestOneKnownDfOneRotation(XPlaneTestCase):
    '''
    Unit Test Overview
        
        This tests if the converter can take a simple 2.49 rotation animation
    with one known dref and exporter it.
    '''
    def test_one_known_df_one_rotation(self):
        bpy.ops.xplane.do_249_conversion()
        bpy.context.scene.xplane.layers[0].name = "test_" + bpy.context.scene.xplane.layers[0].name

        filename = inspect.stack()[0][3]

        self.assertLayerExportEqualsFixture(
            0, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

runTestCases([TestOneKnownDfOneRotation])

