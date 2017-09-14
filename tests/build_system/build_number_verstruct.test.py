import bpy
import os
import sys
from shutil import *
from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config, xplane_constants
from io_xplane2blender.xplane_helpers import VerStruct

__dirname__ = os.path.dirname(__file__)

class TestBuildNumberVerStruct(XPlaneBuildNumberTestCase):
    def test_constructor_defaults_correct(self):
        ver_s = VerStruct()

        self.assertTrue(ver_s.addon_version      == (0,0,0), "addon_version %s does not match it's default %s" % (ver_s.addon_version, (0,0,0)))
        self.assertTrue(ver_s.build_type         == xplane_constants.BUILD_TYPE_DEV, "build_type %s does not match it's default %s" % (ver_s.build_type, xplane_constants.BUILD_TYPE_DEV))
        self.assertTrue(ver_s.build_type_version == 0, "build_type_version %s does not match it's default %s" % (ver_s.build_type_version,0))
        self.assertTrue(ver_s.data_model_version == 0, "data_model_version %s does not match it's default %s" % (ver_s.data_model_version,0))
        self.assertTrue(ver_s.build_number       == xplane_constants.BUILD_NUMBER_NONE,"build_number %s does not match it's default %s" % (ver_s.build_number,xplane_constants.BUILD_NUMBER_NONE))

    #def test_
    
runTestCases([TestBuildNumberVerStruct])
