import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_types import xplane_file, XPlanePrimitive
from io_xplane2blender import xplane_config

class TestWriteXPlaneFiles(XPlaneTestCase):
    def setUp(self):
        super(TestWriteXPlaneFiles, self).setUp()

    def test_write_static(self):
        tmpDir = os.path.realpath(os.path.join(__file__, '../../../tmp'))
        tmpFile = os.path.join(tmpDir, 'test_write_static.obj')

        xplaneFile = xplane_file.createFileFromBlenderLayerIndex(0)
        out = xplaneFile.write()
        print(out)
        outFile = open(tmpFile, 'w')
        outFile.write(out)
        outFile.close()

    def test_write_animated(self):
        tmpDir = os.path.realpath(os.path.join(__file__, '../../../tmp'))
        tmpFile = os.path.join(tmpDir, 'test_write_anim.obj')

        xplaneFile = xplane_file.createFileFromBlenderLayerIndex(1)
        out = xplaneFile.write()
        print(out)
        outFile = open(tmpFile, 'w')
        outFile.write(out)
        outFile.close()

runTestCases([TestWriteXPlaneFiles])
