import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config

__dirname__ = os.path.dirname(__file__)

class TestCase2(XPlaneAnimationTestCase):
    def test_TestCase2(self):
        self.exportAnimationTestCase('TestCase2', os.path.join(__dirname__, '../tmp'))
        self.runAnimationTestCase('TestCase2', __dirname__)


runTestCases([TestCase2])
