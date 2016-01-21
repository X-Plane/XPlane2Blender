import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_config import getDebug
from io_xplane2blender.xplane_types import xplane_file

__dirname__ = os.path.dirname(__file__)

class TestDraped(XPlaneTestCase):
    def test_draped_export(self):
        def filterLines(line):
            return isinstance(line[0], str) and \
                   (line[0].find('TEXTURE') == 0 or \
                   line[0].find('ATTR_draped') == 0 or \
                   line[0].find('TRIS') == 0)

        filename = 'test_draped'
        
        self.assertLayerExportEqualsFixture(
            0, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

runTestCases([TestDraped])
