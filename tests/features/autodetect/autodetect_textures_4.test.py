import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_config import getDebug
from io_xplane2blender.xplane_types import xplane_file

__dirname__ = os.path.dirname(__file__)

class TestAutodetectTextures4(XPlaneTestCase):
    def test_autodetect_textures_export(self):
        def filterLines(line):
            return isinstance(line[0], str) and \
                   line[0].find('TEXTURE') == 0

        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

runTestCases([TestAutodetectTextures4])
