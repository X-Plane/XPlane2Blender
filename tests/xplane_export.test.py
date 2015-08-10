import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config

__dirname__ = os.path.dirname(__file__)

class TestExportXPlaneFiles(XPlaneTestCase):
    def setUp(self):
        super(TestExportXPlaneFiles, self).setUp()

    def beforeEach(self):
        bpy.ops.wm.revert_mainfile()

    def test_export_layers_from_fresh_blend_file(self):
        # initially create xplane layers
        bpy.ops.scene.add_xplane_layers()

        filename = 'test_export_layer'

        bpy.context.scene.xplane.layers[0].name = filename

        tmpDir = os.path.realpath(os.path.join(__dirname__, './tmp'))
        tmpFile = os.path.join(tmpDir, filename + '.obj')

        bpy.ops.export.xplane_obj(filepath = os.path.join(tmpDir, filename + '.obj'))

        self.assertTrue(os.path.exists(tmpFile))

    def test_export_root_objects_from_fresh_blend_file(self):
        # set export mode
        bpy.context.scene.xplane.exportMode = 'root_objects'

        filename = 'test_export_root_object'

        # initially create a root object
        blenderObject = bpy.data.objects['Cube']
        blenderObject.xplane.isExportableRoot = True
        blenderObject.xplane.layer.name = filename

        tmpDir = os.path.realpath(os.path.join(__dirname__, './tmp'))
        tmpFile = os.path.join(tmpDir, filename + '.obj')

        bpy.ops.export.xplane_obj(filepath = os.path.join(tmpDir, filename + '.obj'))

        self.assertTrue(os.path.exists(tmpFile))


runTestCases([TestExportXPlaneFiles])
