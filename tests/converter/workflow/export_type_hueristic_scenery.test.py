import inspect

from typing import Tuple
import os
import sys

import bpy
from io_xplane2blender import xplane_config, xplane_constants
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_249_converter.xplane_249_constants import ProjectType, WorkflowType

__dirname__ = os.path.dirname(__file__)

class TestExportTypeHueristicScenery(XPlaneTestCase):
    def test_IsScenery(self)->None:
        bpy.ops.xplane.do_249_conversion(project_type=ProjectType.SCENERY.name, workflow_type=WorkflowType.BULK.name)
        self.assertEqual(bpy.data.objects["OBJIsScenery"].xplane.layer.export_type, xplane_constants.EXPORT_TYPE_SCENERY)

    def test_IsInstancedScenery(self)->None:
        bpy.ops.xplane.do_249_conversion(project_type=ProjectType.SCENERY.name, workflow_type=WorkflowType.BULK.name)
        self.assertEqual(bpy.data.objects["OBJIsInstancedScenery"].xplane.layer.export_type, xplane_constants.EXPORT_TYPE_INSTANCED_SCENERY)


runTestCases([TestExportTypeHueristicScenery])
