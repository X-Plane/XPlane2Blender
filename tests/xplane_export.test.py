import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config

__dirname__ = os.path.dirname(__file__)

class TestExportXPlaneFiles(XPlaneTestCase):
    def setUp(self):
        super(TestExportXPlaneFiles, self).setUp()

    def test_export_from_fresh_blend_file(self):
        # initially create xplane layers
        bpy.ops.scene.add_xplane_layers()

        bpy.context.scene.xplane.layers[0].name = 'test_xplane_export'

        tmpDir = os.path.realpath(os.path.join(__dirname__, './tmp'))
        tmpFile = os.path.join(tmpDir, 'test_xplane_export.obj')

        bpy.ops.export.xplane_obj(filepath = os.path.join(tmpDir, 'test_xplane_export.obj'))

        self.assertTrue(os.path.exists(tmpFile))


runTestCases([TestExportXPlaneFiles])
