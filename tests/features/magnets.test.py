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
             "MAGNET" in line[0])

class TestMagnets(XPlaneTestCase):
    def test_passing_magnets(self):
        filename = inspect.stack()[0].function

        self.assertLayerExportEqualsFixture(
            0, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

    def test_no_type(self):
        out = self.exportLayer(1)
        self.assertLoggerErrors(1)

    def test_blank_debug_name(self):
        out = self.exportLayer(2)
        self.assertLoggerErrors(1)

    def test_wrong_export_type(self):
        out = self.exportLayer(3)
        self.assertLoggerErrors(1)


runTestCases([TestMagnets])
