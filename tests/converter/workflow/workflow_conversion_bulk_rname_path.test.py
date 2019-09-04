import inspect
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_249_converter.xplane_249_constants import ProjectType, WorkflowType

__dirname__ = os.path.dirname(__file__)


class TestWorkflowConversionBulkRnamePath(XPlaneTestCase):
    def test_rnamepath_prop_conversion(self):
        bpy.ops.xplane.do_249_conversion(project_type=ProjectType.AIRCRAFT.name, workflow_type=WorkflowType.BULK.name)
        scene = bpy.context.scene
        self.assertEqual(scene.objects['OBJnoprops'].xplane.layer.name, "noprops")
        self.assertEqual(scene.objects['OBJpath'].xplane.layer.name, "../workflow/fixtures/path")
        self.assertEqual(scene.objects['OBJrname'].xplane.layer.name, "replaced_name")
        self.assertEqual(scene.objects['OBJrnamepath'].xplane.layer.name, "fixtures/path_replaced_name")

runTestCases([TestWorkflowConversionBulkRnamePath])
