import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_config import getDebug
from io_xplane2blender.xplane_helpers import logger
from io_xplane2blender.xplane_types import xplane_file

__dirname__ = os.path.dirname(__file__)

class TestSSO_2incompatibleMats(XPlaneTestCase):
    expected_logger_errors = 3
        
    def test_export(self):
        filename = 'test_SSO_2incompatibleMats'

        xplaneFile = xplane_file.createFileFromBlenderLayerIndex(0)
        out = xplaneFile.write()

        self.assertEquals(len(logger.findErrors()), self.expected_logger_errors)

runTestCases([TestSSO_2incompatibleMats])
