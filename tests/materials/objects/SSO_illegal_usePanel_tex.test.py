import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_config import getDebug
from io_xplane2blender.xplane_helpers import logger
from io_xplane2blender.xplane_types import xplane_file

__dirname__ = os.path.dirname(__file__)

class TestSSO_IllegalUsePanelTex(XPlaneTestCase):
    def test_export(self):
        filename = 'test_SSO_IllegalUsePanelTex'

        # we must the console transport to prevent the CI from thinking that we got errors
        logger.clearTransports()

        xplaneFile = xplane_file.createFileFromBlenderLayerIndex(0)
        out = xplaneFile.write()

        self.assertEquals(len(logger.findErrors()), 1)

runTestCases([TestSSO_IllegalUsePanelTex])
