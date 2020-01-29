import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_config import getDebug
from io_xplane2blender.xplane_helpers import logger
from io_xplane2blender.xplane_types import xplane_file

__dirname__ = os.path.dirname(__file__)

class TestCOTC_2Mat_Manip_SolidCamera(XPlaneTestCase):
    def test_export(self):
        def filterLines(line):
            return (isinstance(line[0], str)
                    and ("TEXTURE" in line[0]
                        or 'ATTR_' in line[0]
                        or 'GLOBAL' in line[0]
                        or 'SPECULAR' in line[0]))

        filename = 'test_COTC_2Mat_Manip_SolidCamera'

        self.assertLayerExportEqualsFixture(
            0, os.path.join(__dirname__, '..', 'fixtures', filename + '.obj'),
            filterLines,
            filename,
        )

runTestCases([TestCOTC_2Mat_Manip_SolidCamera])
