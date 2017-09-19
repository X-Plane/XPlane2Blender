import bpy
import os
import re
import sys
from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config
from io_xplane2blender.xplane_helpers import VerStruct

__dirname__ = os.path.dirname(__file__)

class TestBlendBuildNumberObjFooter(XPlaneTestCase):
    def test_build_number_obj_footer(self):
        bpy.ops.scene.add_xplane_layers()
        out = self.exportLayer(0)

        version_match = re.search("Exported with XPlane2Blender (.*)", out)
        self.assertTrue(version_match is not None, "Version string not found in footer of obj")
        
        version = VerStruct.parse_version(version_match.group(1))
        self.assertTrue(version is not None, "%s could not be parsed to a valid VerStruct" % version_match.group(1))
        self.assertTrue(version == bpy.context.scene.xplane.xplane2blender_ver.make_struct(),
                        "Version in obj is not equal to current version")
        
runTestCases([TestBlendBuildNumberObjFooter])
