import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_config import getDebug
from io_xplane2blender.xplane_types import xplane_file

__dirname__ = os.path.dirname(__file__)

class TestLights(XPlaneTestCase):
    def test_lights_export(self):
        def filterLines(line):
            return isinstance(line[0], str) and \
                   (line[0].find('LIGHT') == 0 or \
                   line[0].find('VLIGHT') == 0)

        filename = 'test_lights'

        self.assertLayerExportEqualsFixture(
            0, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

runTestCases([TestLights])
