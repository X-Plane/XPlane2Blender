import bpy

import os
import sys
from io_xplane2blender import bl_info
from io_xplane2blender import xplane_config
from io_xplane2blender import xplane_constants
from io_xplane2blender import xplane_helpers
from io_xplane2blender.tests import *

__dirname__ = os.path.dirname(__file__)
bpy.ops.wm.open_mainfile(filepath=os.path.join(__dirname__,'originals','v3_4_0-beta_4.blend'))

class TestBuildNumberProp(XPlaneTestCase):
    current = xplane_helpers.VerStruct.current()

    def test_safe_set_version_data(self):
        xplane2blender_ver = bpy.context.scene.xplane.xplane2blender_ver_history[0]
        self.assertTrue(xplane2blender_ver.safe_set_version_data((3,4,0),"leg",0,0,xplane_constants.BUILD_NUMBER_NONE),
                        "xplane2blender_ver.safe_set_version_data failed with known good data")

        xplane2blender_ver.safe_set_version_data(self.current.addon_version,
                                                 self.current.build_type,
                                                 self.current.build_type_version,
                                                 self.current.data_model_version,
                                                 self.current.build_number)

        self.assertFalse(xplane2blender_ver.safe_set_version_data((0,0,0),"not_real",-1,-99,"99998877665544"),
                         "xplane2blender_ver.safe_set_version_data succeeded with known good data")

        #Important! Reset self.xplane2blender_ver before going on to another test!
        xplane2blender_ver.safe_set_version_data(self.current.addon_version,
                                                 self.current.build_type,
                                                 self.current.build_type_version,
                                                 self.current.data_model_version,
                                                 self.current.build_number)

    #Test if an exception is thrown doesn't seem to work across the Blender-PyDev boundaries
    #def test_prop_set_fails(self):
        #old_values = self.xplane2blender_ver.make_struct()
        #self.xplane2blender_ver.addon_version = (0,0,0)
        #self.xplane2blender_ver.build_type = "dev"
        #self.xplane2blender_ver.build_type_version = 0
        #self.xplane2blender_ver.data_model_version = 0
        #self.xplane2blender_ver.build_number = "20170915041130"
        #self.assertEqual(old_values, self.xplane2blender_ver.make_struct(), "XPlane2BlenderVersion properties changed outside of safe_set_version_data")

runTestCases([TestBuildNumberProp])
