import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_config import getDebug
from io_xplane2blender.xplane_helpers import logger
from io_xplane2blender.xplane_types import xplane_file

__dirname__ = os.path.dirname(__file__)

class TestSSO_2incompatibleATTRsDrapedMats(XPlaneTestCase):
    def test_export(self):
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

runTestCases([TestSSO_2incompatibleATTRsDrapedMats])
