import bpy
import os
import inspect
import sys

from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config

__dirname__ = os.path.dirname(__file__)

def filterLines(line):
    return isinstance(line[0],str) and\
            ("ANIM" in line[0] or\
             "ATTR_manip" in line[0])

class TestDragAxisAutoDetect(XPlaneTestCase):
    def test_01_not_driven_by_one_dataref(self):
        out  = self.exportLayer(0)
        self.assertLoggerErrors(1)

    def test_02_doesnt_have_two_non_clamping_keyframes(self):
        out  = self.exportLayer(1)
        self.assertLoggerErrors(1)

    def test_03_not_leaf_bone(self):
        out  = self.exportLayer(2)
        self.assertLoggerErrors(1)

    def test_04_known_good_drag_axis_autodetect(self):
        filename = inspect.stack()[0][3]

        self.assertLayerExportEqualsFixture(
            3, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

runTestCases([TestDragAxisAutoDetect])
