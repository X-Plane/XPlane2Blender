import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config

__dirname__ = os.path.dirname(__file__)

def filterLines(line):
    return isinstance(line[0],str) and line[0].find("EXPORT") == 0

class TestExportPathCustomScene_2(XPlaneTestCase):
    def test_find_default_scenery(self):
        tmp_path = os.path.abspath(os.path.join(__dirname__,'../../../../../tmp'))
        filename = 'honda_2'
        bpy.ops.scene.export_to_relative_dir(initial_dir=tmp_path)
        self.assertFileTmpEqualsFixture(
            os.path.join(tmp_path,filename + '.obj'),
            make_fixture_path(__dirname__,"honda_2"),
            filterLines)

runTestCases([TestExportPathCustomScene_2])
