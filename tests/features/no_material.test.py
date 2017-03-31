import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_config import getDebug
from io_xplane2blender.xplane_helpers import logger
from io_xplane2blender.xplane_types import xplane_file

__dirname__ = os.path.dirname(__file__)

class TestNoMaterial(XPlaneTestCase):
    expected_logger_errors = 1
    def test_no_material(self):
        xplaneFile = xplane_file.createFileFromBlenderLayerIndex(0)
        out = xplaneFile.write()
        
        self.assertEquals(len(logger.findErrors()), self.expected_logger_errors)

runTestCases([TestNoMaterial])
