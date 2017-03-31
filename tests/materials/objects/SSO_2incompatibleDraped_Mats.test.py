import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_config import getDebug
from io_xplane2blender.xplane_helpers import logger
from io_xplane2blender.xplane_types import xplane_file

__dirname__ = os.path.dirname(__file__)

class TestSSO_2incompatibleDrapedMats(XPlaneTestCase):
    expected_logger_errors = 2
        
    def test_export(self):
        filename = 'test_SSO_2incompatibleDraped_Mats'

        xplaneFile = xplane_file.createFileFromBlenderLayerIndex(0)
        out = xplaneFile.write()

        self.assertEquals(len(logger.findErrors()), self.expected_logger_errors)

runTestCases([TestSSO_2incompatibleDrapedMats])
