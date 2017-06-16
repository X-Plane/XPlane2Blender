import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config

__dirname__ = os.path.dirname(__file__)

class TestCase6_scaling_rot(XPlaneAnimationTestCase):
    def test_TestCase6_scaling_rot(self):
        self.exportAnimationTestCase('TestCase6_scaling_rot', os.path.join(__dirname__, '../tmp'))
        self.runAnimationTestCase('TestCase6_scaling_rot', __dirname__)

runTestCases([TestCase6_scaling_rot])
