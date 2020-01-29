import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_config import getDebug
from io_xplane2blender.xplane_types import xplane_file

__dirname__ = os.path.dirname(__file__)

class TestDrawEnabled(XPlaneTestCase):
    def test_draped_export(self):
        def filterLines(line):
            return isinstance(line[0], str) and \
                   (line[0].find('ATTR_draw') == 0 or \
                   line[0].find('TRIS') == 0)

        filename = 'test_draw_enabled'

        self.assertLayerExportEqualsFixture(
            0, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filterLines,
            filename,
        )

runTestCases([TestDrawEnabled])
