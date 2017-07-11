import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config

__dirname__ = os.path.dirname(__file__)

class TestCase8_bone_optimization(XPlaneAnimationTestCase):
    def test_TestCase8_bone_optimization(self):
        self.exportAnimationTestCase('TestCase8_bone_optimization', os.path.join(__dirname__, '../tmp'))
        self.runAnimationTestCase('TestCase8_bone_optimization', __dirname__)

runTestCases([TestCase8_bone_optimization])
