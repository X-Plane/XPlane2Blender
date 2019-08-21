import inspect

from typing import Tuple
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_249_converter import xplane_249_constants as xp249c
from io_xplane2blender.xplane_249_converter.xplane_249_constants import WorkflowType

__dirname__ = os.path.dirname(__file__)

class TestObjectAttributesApplied(XPlaneTestCase):
    def assertLitLevel(self, obj:bpy.types.Object, hint_suffix:str, v1:float, v2:float, dref:str)->None:
        lit_level_mat = obj.material_slots[0].material
        self.assertEqual(lit_level_mat.name, xp249c.DEFAULT_MATERIAL_NAME + "_" + hint_suffix)
        self.assertTrue(lit_level_mat.xplane.lightLevel)
        self.assertAlmostEqual(lit_level_mat.xplane.lightLevel_v1, v1)
        self.assertAlmostEqual(lit_level_mat.xplane.lightLevel_v2, v2)
        self.assertEqual(lit_level_mat.xplane.lightLevel_dataref, dref)

    def test_Scene_cockpit(self)->None:
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.REGULAR.name)
        objects = bpy.data.scenes[inspect.stack()[0].function[5:]].objects
        self.assertEqual(objects["SOLID_CAM"].material_slots[0].material.name, xp249c.DEFAULT_MATERIAL_NAME + "_" + xp249c.HINT_PROP_SOLID_CAM)

    def test_Scene_has_prop(self)->None:
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.REGULAR.name)
        objects = bpy.data.scenes[inspect.stack()[0].function[5:]].objects
        self.assertEqual(objects["DRAW_DISABLE"].material_slots[0].material.name, xp249c.DEFAULT_MATERIAL_NAME + "_" + xp249c.HINT_PROP_DRAW_DISABLE)

    def test_Scene_lit_level(self)->None:
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.REGULAR.name)
        objects = bpy.data.scenes[inspect.stack()[0].function[5:]].objects
        self.assertLitLevel(objects["ATTR_light_level1prop"], xp249c.HINT_PROP_LIT_LEVEL,          .25, .75, "sim/weapons/x[0]")
        self.assertLitLevel(objects["lit_level"],             xp249c.HINT_PROP_LIT_LEVEL + ".001", .10, .90, "sim/weapons/y[0]")

    def test_Scene_lit_level_split(self)->None:
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.REGULAR.name)
        objects = bpy.data.scenes[inspect.stack()[0].function[5:]].objects
        self.assertEqual(objects["ATTR_light_level_v1"].material_slots[0].material.name, xp249c.DEFAULT_MATERIAL_NAME)
        self.assertEqual(objects["ATTR_light_level_v2"].material_slots[0].material.name, xp249c.DEFAULT_MATERIAL_NAME)
        # Yes, this is the only one that got the attribute. The rest get 249!
        self.assertLitLevel(objects["ATTR_light_level"], xp249c.HINT_PROP_LIT_LEVEL + ".002", 3, 6, "sim/weapons/z[0]")
        self.assertLitLevel(objects["ensures_v1_default"], xp249c.HINT_PROP_LIT_LEVEL + ".003", 0.0, .6, "test/dref1")
        self.assertLitLevel(objects["ensures_v2_default"], xp249c.HINT_PROP_LIT_LEVEL + ".004", .4, 1.0, "test/dref2")


runTestCases([TestObjectAttributesApplied])
