import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config

__dirname__ = os.path.dirname(__file__)

class TestCase9_keyframe_loops(XPlaneAnimationTestCase):
    def test_TestCase9_keyframe_loops(self):
        self.exportAnimationTestCase('TestCase9_keyframe_loops', os.path.join(__dirname__, '../tmp'))
        self.runAnimationTestCase('TestCase9_keyframe_loops', __dirname__)

runTestCases([TestCase9_keyframe_loops])
