import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_types import xplane_file, XPlanePrimitive
from io_xplane2blender import xplane_config

class TestWriteXPlaneFiles(XPlaneTestCase):
    def setUp(self):
        super(TestWriteXPlaneFiles, self).setUp()

    def test_write_layer1(self):
        xplaneFile = xplane_file.createFileFromBlenderLayerIndex(0)
        print(xplaneFile.write())

runTestCases([TestWriteXPlaneFiles])
