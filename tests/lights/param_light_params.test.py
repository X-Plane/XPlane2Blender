import bpy
import os
import inspect
import sys

from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config
from io_xplane2blender.xplane_types import xplane_light

__dirname__ = os.path.dirname(__file__)
 
class TestParamLightParams(XPlaneTestCase):
    def test_comment_correct(self):
        #COPY-PASTA WARNING from xplane_file: 65-75
        # What we need is an xplaneFile in the data model and interrupt
        # the export before the xplane_file gets deleted when going out of scope
        xplaneLayer = xplane_file.getXPlaneLayerForBlenderLayerIndex(0)

        assert xplaneLayer is not None
        xplaneFile = xplane_file.XPlaneFile(xplane_file.getFilenameFromXPlaneLayer(xplaneLayer), xplaneLayer)

        assert xplaneFile is not None
        xplaneFile.collectFromBlenderLayerIndex(0)

        light = xplaneFile.objects["4_comment_contents_preserved_exactly"]
        self.assertTrue(light.comment == "0 spaces, number starts comment with uneven and a   trailing  space ")

    def test_illegal_params_content(self):
        out = self.exportLayer(1)
        self.assertLoggerErrors(3)

runTestCases([TestParamLightParams])

