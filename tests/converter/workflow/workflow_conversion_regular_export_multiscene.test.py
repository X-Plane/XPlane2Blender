import inspect
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_249_converter.xplane_249_constants import WorkflowType, WORKFLOW_DEFAULT_ROOT_NAME


__dirname__ = os.path.dirname(__file__)

class TestWorkflowConversionRegularExportMultiScene(XPlaneTestCase):
    def test_regular_multiscene_conversion(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.REGULAR.name)
        objects = bpy.context.scene.objects
        self.assertEqual(bpy.data.scenes['SuperPlane_cockpit'].objects[WORKFLOW_DEFAULT_ROOT_NAME + "_01"].xplane.layer.name, "SuperPlane_cockpit")
        self.assertEqual(bpy.data.scenes['SuperPlane_wings'].objects[WORKFLOW_DEFAULT_ROOT_NAME + "_02"].xplane.layer.name,   "SuperPlane_wings")

runTestCases([TestWorkflowConversionRegularExportMultiScene])
