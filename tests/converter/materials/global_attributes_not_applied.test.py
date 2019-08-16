import inspect

from typing import Tuple
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_249_converter.xplane_249_constants import WorkflowType

__dirname__ = os.path.dirname(__file__)

class TestGlobalAttributesNotApplied(XPlaneTestCase):
    def test_global_properties_not_applied(self)->None:
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.REGULAR.name)
        # Why? The algorithm makes and reuses one default material
        # and need to change that material would result in derivatives being made!
        self.assertEqual(len(bpy.data.materials), 1)

runTestCases([TestGlobalAttributesNotApplied])
