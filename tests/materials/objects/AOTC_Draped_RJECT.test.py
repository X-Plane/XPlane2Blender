import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_config import getDebug
from io_xplane2blender.xplane_helpers import logger
from io_xplane2blender.xplane_types import xplane_file

__dirname__ = os.path.dirname(__file__)

class TestAOTC_Draped_RJECT(XPlaneTestCase):
    def test_export(self):
        xplaneFile = xplane_file.createFileFromBlenderLayerIndex(0)
        out = xplaneFile.write()

        self.assertLoggerErrors(1)

runTestCases([TestAOTC_Draped_RJECT])
