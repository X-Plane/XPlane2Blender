import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_types import xplane_file, XPlanePrimitive
from io_xplane2blender import xplane_config

__dirname__ = os.path.dirname(__file__)

class TestWriteXPlaneFiles(XPlaneTestCase):
    def setUp(self):
        super(TestWriteXPlaneFiles, self).setUp()

    def test_write_static(self):
        tmpDir = os.path.realpath(os.path.join(__file__, '../../../tmp'))
        tmpFile = os.path.join(tmpDir, 'test_write_static.obj')

        xplaneFile = xplane_file.createFileFromBlenderLayerIndex(0)
        out = xplaneFile.write()
        outFile = open(tmpFile, 'w')
        outFile.write(out)
        outFile.close()

        self.assertFileEqualsFixture(out, os.path.join(__dirname__, './fixtures/test_write_static.obj'))

    def test_write_trans_animated(self):
        tmpDir = os.path.realpath(os.path.join(__file__, '../../../tmp'))
        tmpFile = os.path.join(tmpDir, 'test_write_trans_anim.obj')

        xplaneFile = xplane_file.createFileFromBlenderLayerIndex(1)
        out = xplaneFile.write()
        outFile = open(tmpFile, 'w')
        outFile.write(out)
        outFile.close()

        self.assertFileEqualsFixture(out, os.path.join(__dirname__, './fixtures/test_write_trans_anim.obj'))

    def test_write_transrot_animated(self):
        tmpDir = os.path.realpath(os.path.join(__file__, '../../../tmp'))
        tmpFile = os.path.join(tmpDir, 'test_write_transrot_anim.obj')

        xplaneFile = xplane_file.createFileFromBlenderLayerIndex(2)
        out = xplaneFile.write()
        outFile = open(tmpFile, 'w')
        outFile.write(out)
        outFile.close()

        self.assertFileEqualsFixture(out, os.path.join(__dirname__, './fixtures/test_write_transrot_anim.obj'))

runTestCases([TestWriteXPlaneFiles])
