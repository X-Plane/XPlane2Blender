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
    def test_1_known_param_should_error(self):
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

    def test_2_known_named_should_pass(self):
        out = self.exportLayer(1)
        self.assertLoggerErrors(0)
        self.assertTrue("ANIM_rotate" in out)

    def test_3_unknown_should_pass_no_auto(self):
        out = self.exportLayer(2)
        self.assertLoggerErrors(0)
        self.assertFalse("ANIM" in out)

    def test_4_known_param_enough_params_should_pass(self):
        out = self.exportLayer(3)
        self.assertTrue("ANIM" in out)

    def test_5_known_param_not_enough_params_should_error(self):
        out = self.exportLayer(4)
        self.assertLoggerErrors(1)

    def test_6_known_named_fake_params_should_error(self):
        out = self.exportLayer(5)
        self.assertLoggerErrors(1)

    def test_7_known_named_empty_param_should_error(self):
        out = self.exportLayer(6)
        self.assertLoggerErrors(1)

    def test_8_unknown_params(self):
        out = self.exportLayer(7)
        self.assertFalse("ANIM" in out)

    def test_9_unknown_empty_params(self):
        out = self.exportLayer(8)
        self.assertLoggerErrors(1)

runTestCases([TestKnownVsUnknownNamedVsParam])
