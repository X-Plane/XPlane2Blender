import inspect
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_249_converter.xplane_249_constants import WorkflowType, WORKFLOW_DEFAULT_ROOT_NAME


__dirname__ = os.path.dirname(__file__)

class TestWorkflowConversionRegularExport(XPlaneTestCase):
    def test_regular_conversion(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.REGULAR.name)
        objects = bpy.context.scene.objects
        new_root = objects[WORKFLOW_DEFAULT_ROOT_NAME + "_01"]
        self.assertEqual(new_root.xplane.layer.name, os.path.splitext(os.path.basename(bpy.data.filepath))[0])
        self.assertTrue(new_root.xplane.isExportableRoot)

        self.assertEqual(objects['Armature'].parent, new_root)
        # Only the top level objects should have parents re-assigned
        self.assertEqual(objects['Cube'].parent, objects['Armature'])
        self.assertEqual(objects['Empty'].parent, new_root)
        self.assertEqual(objects['Lamp'].parent, new_root)

runTestCases([TestWorkflowConversionRegularExport])
