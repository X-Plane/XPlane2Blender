import bpy
import os
import re
import sys
from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config
from io_xplane2blender.xplane_helpers import VerStruct

__dirname__ = os.path.dirname(__file__)

#TEMPLATE_INFO filter obj output. Define above or in the class level 
#def filterLines(line):
    #return isinstance(line[0],str) and...
    
class TestBlendBuildNumberObjFooter(XPlaneBuildNumberTestCase):
    def test_build_number_obj_footer(self):
        bpy.ops.scene.add_xplane_layers()
        out = self.exportLayer(0)

        version_match = re.search("Exported with XPlane2Blender (.*)", out)
        self.assertTrue(version_match is not None, "Version string not found in footer of obj")
        
        version = VerStruct.parse_version(version_match.group(1))
        self.assertTrue(version is not None, "%s could not be parsed to a valid VerStruct" % version_match.group(1))
        self.assertTrue(VerStruct.cmp(version,self.xplane2blender_ver,True,True) == 0,
                        "Version in obj is not equal to current version")
        
runTestCases([TestBlendBuildNumberObjFooter])
