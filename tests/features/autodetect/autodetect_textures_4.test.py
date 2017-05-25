import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_config import getDebug
from io_xplane2blender.xplane_types import xplane_file

__dirname__ = os.path.dirname(__file__)

class TestAutodetectTextures(XPlaneTestCase):
    expected_logger_errors = 1
    def test_autodetect_textures_export(self):
        def filterLines(line):
            return isinstance(line[0], str) and \
                   line[0].find('TEXTURE') == 0

        xplaneFile = xplane_file.createFileFromBlenderLayerIndex(0)
        out = xplaneFile.write()
        
        self.assertEquals(len(logger.findErrors()),self.expected_logger_errors)
        
runTestCases([TestAutodetectTextures])
