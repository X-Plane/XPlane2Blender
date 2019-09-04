import inspect

from typing import Tuple
import os
import sys

import bpy
from io_xplane2blender import xplane_config, xplane_constants
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_249_converter.xplane_249_constants import ProjectType, WorkflowType

__dirname__ = os.path.dirname(__file__)

class TestExportTypeHueristicAircraft(XPlaneTestCase):
    def test_IsAircraft(self)->None:
        bpy.ops.xplane.do_249_conversion(project_type=ProjectType.AIRCRAFT.name, workflow_type=WorkflowType.BULK.name)
        self.assertEqual(bpy.data.objects["OBJIsAircraft"].xplane.layer.export_type, xplane_constants.EXPORT_TYPE_AIRCRAFT)

    def test_IsCockpit(self)->None:
        bpy.ops.xplane.do_249_conversion(project_type=ProjectType.AIRCRAFT.name, workflow_type=WorkflowType.BULK.name)
        self.assertEqual(bpy.data.objects["OBJIsCockpit"].xplane.layer.export_type, xplane_constants.EXPORT_TYPE_COCKPIT)


runTestCases([TestExportTypeHueristicAircraft])
