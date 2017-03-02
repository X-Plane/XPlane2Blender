import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config

__dirname__ = os.path.dirname(__file__)

class TestCase3(XPlaneAnimationTestCase):
    def test_TestCase3(self):
        self.exportAnimationTestCase('TestCase3', os.path.join(__dirname__, '../tmp'))
        self.runAnimationTestCase('TestCase3', __dirname__)


runTestCases([TestCase3])
