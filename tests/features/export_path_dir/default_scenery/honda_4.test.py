import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config

__dirname__ = os.path.dirname(__file__)

def filterLines(line):
    return isinstance(line[0],str) and line[0].find("EXPORT") == 0
    
class TestExportPathCustomScen_4(XPlaneTestCase):
    def test_missing_one_dir_after_fails(self):
        expected_logger_errors = 1
        out = xplane_file.createFileFromBlenderLayerIndex(0).write()
        self.assertEquals(len(logger.findErrors()),expected_logger_errors)
        logger.clearMessages()

runTestCases([TestExportPathCustomScen_4])
