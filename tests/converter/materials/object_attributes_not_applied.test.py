import inspect

from typing import Tuple
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_249_converter import xplane_249_constants as xp249c
from io_xplane2blender.xplane_249_converter.xplane_249_constants import ProjectType, WorkflowType

__dirname__ = os.path.dirname(__file__)

class TestObjectAttributesNotApplied(XPlaneTestCase):
    def assertLitLevel(self, obj:bpy.types.Object, hint_suffix:str, v1:float, v2:float, dref:str)->None:
        lit_level_mat = obj.material_slots[0].material
        self.assertEqual(lit_level_mat.name, xp249c.DEFAULT_MATERIAL_NAME + "_" + hint_suffix)
        self.assertTrue(lit_level_mat.xplane.lightLevel)
        self.assertAlmostEqual(lit_level_mat.xplane.lightLevel_v1, v1)
        self.assertAlmostEqual(lit_level_mat.xplane.lightLevel_v2, v2)
        self.assertEqual(lit_level_mat.xplane.lightLevel_dataref, dref)

    def test_not_applied_common_cases(self):
        bpy.ops.xplane.do_249_conversion(project_type=ProjectType.AIRCRAFT.name, workflow_type=WorkflowType.REGULAR.name)
        # We aren't checking for errors, we just want to let people move on with their conversion
        for obj in filter(lambda obj: obj.type == "MESH", bpy.data.objects):
            if obj.name == "litlevel_overwrite":
                self.assertLitLevel(obj, xp249c.HINT_PROP_LIT_LEVEL + "1", 3, 4, "test/chose/overwrite")
            else:
                self.assertEqual(obj.material_slots[0].material.name, xp249c.DEFAULT_MATERIAL_NAME)

runTestCases([TestObjectAttributesNotApplied])
