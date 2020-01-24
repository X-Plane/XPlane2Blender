import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config

__dirname__ = os.path.dirname(__file__)

def filterLines(line):
    return isinstance(line[0],str) and line[0].find("EXPORT") == 0

class TestExportPathCustomScene_3(XPlaneTestCase):
    def test_no_second_folder_works(self):
           self.assertLayerExportEqualsFixture(
               0,
               make_fixture_path(__dirname__,"honda_3"),
                                             "honda_3",
               filterLines)

runTestCases([TestExportPathCustomScene_3])
