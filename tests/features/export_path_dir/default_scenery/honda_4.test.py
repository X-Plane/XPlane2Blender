import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config

__dirname__ = os.path.dirname(__file__)

def filterLines(line):
    return isinstance(line[0],str) and line[0].find("EXPORT") == 0

class TestExportPathCustomScene_4(XPlaneTestCase):
    def test_missing_one_dir_after_fails(self):
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)
        logger.clearMessages()

runTestCases([TestExportPathCustomScene_4])
