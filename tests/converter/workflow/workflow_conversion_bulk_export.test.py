import inspect
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_249_converter.xplane_249_constants import WorkflowType

__dirname__ = os.path.dirname(__file__)


class TestWorkflowConversionBulkExport(XPlaneTestCase):
    def test_real_root_objects(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        scene = bpy.context.scene
        self.assertTrue(scene.objects['OBJ HasNameProperty'].xplane.isExportableRoot)
        self.assertTrue(scene.objects['OBJ HasNameProperty'].xplane.layer.name == scene.objects['OBJ HasNameProperty'].game.properties['rname'].value)

    def test_catch_false_negatives(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        scene = bpy.context.scene
        self.assertTrue(scene.objects['OBJNoChildren'].xplane.isExportableRoot)
        self.assertTrue(scene.objects['OBJNoChildren'].xplane.layer.name == "NoChildren")

    def test_catch_false_positives(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        scene = bpy.context.scene
        self.assertFalse(scene.objects['OBJNotTopLevel'].xplane.isExportableRoot)
        self.assertFalse(scene.objects['OBJMeshNotEmpty'].xplane.isExportableRoot)
        self.assertFalse(scene.objects['FakeOutCube1'].xplane.isExportableRoot)

runTestCases([TestWorkflowConversionBulkExport])
