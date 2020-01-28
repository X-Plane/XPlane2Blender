import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_types import xplane_file
from io_xplane2blender import xplane_config

__dirname__ = os.path.dirname(__file__)

class TestWriteXPlaneFiles(XPlaneTestCase):
    def setUp(self):
        super(TestWriteXPlaneFiles, self).setUp()

    def test_write_static(self):
        filename = 'test_write_static'
        # This is the "Who knows, just a bunch of stuff" style unit test
        filters = {"REQUIRE_DRY", "SLOPE_LIMIT", "TILTED", "TEXTURE", "ANIM", "TRIS", "VLIGHT", "LIGHTS"}
        self.assertLayerExportEqualsFixture(0, os.path.join(__dirname__, 'fixtures', filename + '.obj'), filename, filters)

    def test_write_trans_animated(self):
        filename = 'test_write_trans_anim'
        self.assertLayerExportEqualsFixture(1, os.path.join(__dirname__, 'fixtures', filename + '.obj'), filename, {"ANIM", "TRIS"})

    def test_write_transrot_animated(self):
        filename = 'test_write_transrot_anim'
        self.assertLayerExportEqualsFixture(2, os.path.join(__dirname__, 'fixtures', filename + '.obj'), filename, {"ANIM", "TRIS"})

runTestCases([TestWriteXPlaneFiles])
