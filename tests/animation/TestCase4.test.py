import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config

__dirname__ = os.path.dirname(__file__)

class TestCase4(XPlaneAnimationTestCase):
    def test_TestCase4(self):
        self.runAnimationTestCase('TestCase4', __dirname__)


runTestCases([TestCase4])
