import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_config import getDebug
from io_xplane2blender.xplane_helpers import logger
from io_xplane2blender.xplane_types import xplane_file

__dirname__ = os.path.dirname(__file__)

class TestIST_2MatsSameSPECDifSURF(XPlaneTestCase):
    def test_export(self):
        def filterLines(line):
            return (isinstance(line[0], str)
                    and ('ATTR_' in line[0]
                         or 'GLOBAL' in line[0]))

        filename = 'test_IST_2Mats_SameSPEC_DifSURF'

        self.assertLayerExportEqualsFixture(
            0, os.path.join(__dirname__, '..', 'fixtures', filename + '.obj'),
            filterLines,
            filename,
        )

runTestCases([TestIST_2MatsSameSPECDifSURF])
