import inspect
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *

__dirname__ = os.path.dirname(__file__)

def filterLines(line):
    return isinstance(line[0],str) and\
            ("ANIM" in line[0] or\
             "IDX" in line[0] or\
             "TRIS" in line[0] or\
             "VT" in line[0])

class TestDatarefDecodingKnownCases(XPlaneTestCase):
    def test_dataref_decoding_known_cases(self):
        bpy.ops.xplane.do_249_conversion()
        filename = inspect.stack()[0][3]

        self.assertLayerExportEqualsFixture(
            0, os.path.join(__dirname__, 'fixtures', filename.replace("test_","") + '.obj'),
            filename.replace("test_",""),
            filterLines
        )

runTestCases([TestDatarefDecodingKnownCases])
