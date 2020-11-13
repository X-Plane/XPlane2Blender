import inspect
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *

__dirname__ = os.path.dirname(__file__)

def filterLines(line):
    return isinstance(line[0],str) and\
            ("ATTR" in line[0] or\
             "GLOBAL_no_blend" in line[0] or\
             "GLOBAL_specular" in line[0] or\
             "TRIS" in line[0])

class TestPassiveResetting(XPlaneTestCase):
    def test_cube_empty_cube(self):
        filename = inspect.stack()[0][3]

        self.assertLayerExportEqualsFixture(
            0, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filterLines,
            filename,
        )

    def test_instanced_header_empty_cube(self):
        filename = inspect.stack()[0][3]

        self.assertLayerExportEqualsFixture(
            1, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filterLines,
            filename,
        )

runTestCases([TestPassiveResetting])
