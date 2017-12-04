import bpy
import os
import inspect
import sys

from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config

__dirname__ = os.path.dirname(__file__)

#TI filter obj output. Define above or in the class level 
#def filterLines(line):
    #return isinstance(line[0],str) and\
            #("OBJ_DIRECTIVE" in line[0] or\

class TestKnownVsUnknownNamedVsParam(XPlaneTestCase):
    def test_01_known_param_should_error(self):
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

    def test_02_known_named_should_pass(self):
        out = self.exportLayer(1)
        self.assertLoggerErrors(0)
        self.assertTrue("ANIM_rotate" in out)

    def test_03_unknown_should_pass_no_auto(self):
        out = self.exportLayer(2)
        self.assertLoggerErrors(0)
        self.assertFalse("ANIM" in out)

    def test_04_known_param_enough_params_should_pass(self):
        out = self.exportLayer(3)
        self.assertTrue("ANIM" in out)

    def test_05_known_param_not_enough_params_should_error(self):
        out = self.exportLayer(4)
        self.assertLoggerErrors(1)

    def test_06_known_named_fake_params_should_error(self):
        out = self.exportLayer(5)
        self.assertLoggerErrors(1)

    def test_07_known_named_empty_param_should_error(self):
        out = self.exportLayer(6)
        self.assertLoggerErrors(1)

    def test_08_unknown_params(self):
        out = self.exportLayer(7)
        self.assertFalse("ANIM" in out)

    def test_09_unknown_empty_params(self):
        out = self.exportLayer(8)
        self.assertLoggerErrors(1)

    def test_10_custom_light_not_autocorrected(self):
        out = self.exportLayer(9)
        self.assertFalse("ANIM" in out)

runTestCases([TestKnownVsUnknownNamedVsParam])
