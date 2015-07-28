import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config

__dirname__ = os.path.dirname(__file__)

class TestCase1(XPlaneAnimationTestCase):
    def test_TestCase1(self):
        self.runAnimationTestCase('TestCase1', __dirname__)


runTestCases([TestCase1])
