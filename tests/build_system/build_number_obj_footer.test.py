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
        coll = bpy.data.collections.new("Layer 1")
        coll.xplane.is_exportable_collection = True
        out = self.exportLayer(0)

        version_match = re.search("Exported with XPlane2Blender (.*)", out)
        self.assertIsNotNone(version_match, "Version string not found in footer of obj")

        version = VerStruct.parse_version(version_match.group(1))
        self.assertIsNotNone(version, "%s could not be parsed to a valid VerStruct" % version_match.group(1))
        self.assertEqual(version, xplane_helpers.VerStruct.current(),"Version in obj is not equal to current version")

runTestCases([TestBlendBuildNumberObjFooter])
