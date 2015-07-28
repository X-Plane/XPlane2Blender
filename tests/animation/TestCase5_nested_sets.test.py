import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config

__dirname__ = os.path.dirname(__file__)

class TestCase5_nested_sets(XPlaneAnimationTestCase):
    def test_TestCase5_nested_sets(self):
        self.runAnimationTestCase('TestCase5_nested_sets', __dirname__)

runTestCases([TestCase5_nested_sets])
