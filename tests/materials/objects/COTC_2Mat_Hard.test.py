import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_config import getDebug
from io_xplane2blender.xplane_helpers import logger
from io_xplane2blender.xplane_types import xplane_file

__dirname__ = os.path.dirname(__file__)

class TestCOTC_2Mat_Hard(XPlaneTestCase):
    def test_export(self):
        def filterLines(line):
            return isinstance(line[0], str) and \
                   (line[0].find('TEXTURE') == 0 or \
                   line[0].find('ATTR_') == 0 or \
                   line[0].find('GLOBAL') == 0 or \
                   line[0].find('SPECULAR'))

        filename = 'test_COTC_2Mat_Hard'
        
        self.assertLayerExportEqualsFixture(
            0, os.path.join(__dirname__, '..', 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

runTestCases([TestCOTC_2Mat_Hard])
