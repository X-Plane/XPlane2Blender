import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_types import xplane_file
from io_xplane2blender import xplane_config

__dirname__ = os.path.dirname(__file__)

class TestAxis(XPlaneTestCase):
    def test_axis(self):
        tmpDir = os.path.realpath(os.path.join(__dirname__, '../tmp'))
        tmpFile = os.path.join(tmpDir, 'axis.obj')

        bpy.ops.export.xplane_obj(filepath = os.path.join(tmpDir, 'axis.obj'))

        self.assertTrue(os.path.exists(tmpFile))

runTestCases([TestAxis])
