import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_config import getDebug
from io_xplane2blender.xplane_types import xplane_file

__dirname__ = os.path.dirname(__file__)

class TestSSO_2compatibleMats_Draped(XPlaneTestCase):
    def test_export(self):
        def filterLines(line):
            return isinstance(line[0], str) and \
                   (line[0].find('TEXTURE') == 0 or line[0].find('ATTR_') == 0)

        filename = 'test_SSO_2compatibleMats_Draped'

        self.assertLayerExportEqualsFixture(
            0, os.path.join(__dirname__, '..', 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

        # remove generated texture
        os.unlink(os.path.join(__dirname__, 'texture_NML_nm.png'))

runTestCases([TestSSO_2compatibleMats_Draped])
