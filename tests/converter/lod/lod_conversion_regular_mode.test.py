import inspect
import os
import sys

import bpy
from io_xplane2blender import xplane_config, xplane_constants
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_249_converter.xplane_249_constants import WORKFLOW_REGULAR_NEW_ROOT_NAME, WorkflowType


__dirname__ = os.path.dirname(__file__)


class TestLODConversionRegularMode(XPlaneTestCase):
    def test_lods_regular_mode(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.REGULAR.name)
        fixture_lods = [(0, 200), (0, 3000), (0, 5000), (0, 0), (0, 0)]
        lods = bpy.context.scene.objects[WORKFLOW_REGULAR_NEW_ROOT_NAME].xplane.layer.lod
        print([(l.near, l.far) for l in lods])
        self.assertTrue([(l.near, l.far) for l in lods] == fixture_lods)

runTestCases([TestLODConversionRegularMode])
