import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config

__dirname__ = os.path.dirname(__file__)

class TestCase7_scaling_rotloc(XPlaneAnimationTestCase):
    def test_TestCase7_scaling_rotloc(self):
        self.exportAnimationTestCase('TestCase7_scaling_rotloc', os.path.join(__dirname__, '../tmp'))
        self.runAnimationTestCase('TestCase7_scaling_rotloc', __dirname__)

runTestCases([TestCase7_scaling_rotloc])
