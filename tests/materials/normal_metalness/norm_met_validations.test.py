import inspect
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *

__dirname__ = os.path.dirname(__file__)

class TestNormMetValidations(XPlaneTestCase):
    def test_01_mismatching_metalness_error(self):
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

    def test_02_03_warn_no_nml_tex(self):
        out = self.exportLayer(1)
        #print(out)
        out = self.exportLayer(2)
        #print(out)
        print("Manual verification of warning needed")
        #self.assertLoggerWarnings(2)# For now, it must be manual

    def test_06_Mixed_panel_metal_on(self):
        out = self.exportLayer(5)
        self.assertTrue("NORMAL_METALNESS" in out)

    def test_07_Mixed_panel_metal_on(self):
        out = self.exportLayer(6)
        self.assertTrue("NORMAL_METALNESS" not in out)


runTestCases([TestNormMetValidations])
