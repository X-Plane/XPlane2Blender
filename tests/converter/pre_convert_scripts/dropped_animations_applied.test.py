import inspect

from typing import Tuple
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_249_converter.xplane_249_constants import ProjectType, WorkflowType

__dirname__ = os.path.dirname(__file__)

class TestDroppedAnimationsApplied(XPlaneTestCase):
    def test_dropped_animations_applied(self)->None:
        bpy.ops.xplane.do_249_conversion(project_type=ProjectType.AIRCRAFT.name, workflow_type=WorkflowType.BULK.name)

        for arm in filter(lambda o: o.type == "ARMATURE" and "_solo" not in o.name, bpy.data.objects):
            self.assertEqual(arm.animation_data.action, bpy.data.actions['Action'], msg="{} has {} for its action".format(arm.name, arm.animation_data.action.name if arm.animation_data.action else None))

        self.assertEqual(bpy.data.objects["Armature_solo"].animation_data.action, bpy.data.actions['Action.002'])


runTestCases([TestDroppedAnimationsApplied])
