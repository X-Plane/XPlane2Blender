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

class TestObjectAttributesApplied(XPlaneTestCase):
    def assertLitLevel(self, obj:bpy.types.Object, mat_name:str, v1:float, v2:float, dref:str, is_ll=True)->None:
        lit_level_mat = obj.material_slots[0].material
        self.assertEqual(lit_level_mat.name, mat_name)
        self.assertEqual(lit_level_mat.xplane.lightLevel, is_ll)
        self.assertAlmostEqual(lit_level_mat.xplane.lightLevel_v1, v1)
        self.assertAlmostEqual(lit_level_mat.xplane.lightLevel_v2, v2)
        self.assertEqual(lit_level_mat.xplane.lightLevel_dataref, dref)

    def test_Scene_cockpit(self)->None:
        bpy.ops.xplane.do_249_conversion(project_type=ProjectType.AIRCRAFT.name, workflow_type=WorkflowType.REGULAR.name)
        objects = bpy.data.scenes[inspect.stack()[0].function[5:]].objects
        self.assertEqual(objects["SOLID_CAM"].material_slots[0].material.name, "{}_{}_{}".format(xp249c.DEFAULT_MATERIAL_NAME, xp249c.HINT_PROP_DRAW_DISABLE, xp249c.HINT_PROP_SOLID_CAM))

    def test_Scene_has_prop(self)->None:
        bpy.ops.xplane.do_249_conversion(project_type=ProjectType.AIRCRAFT.name, workflow_type=WorkflowType.REGULAR.name)
        objects = bpy.data.scenes[inspect.stack()[0].function[5:]].objects
        self.assertEqual(objects["DRAW_DISABLE"].material_slots[0].material.name, xp249c.DEFAULT_MATERIAL_NAME + "_" + xp249c.HINT_PROP_DRAW_DISABLE)

    def test_Scene_lit_level(self)->None:
        bpy.ops.xplane.do_249_conversion(project_type=ProjectType.AIRCRAFT.name, workflow_type=WorkflowType.REGULAR.name)
        objects = bpy.data.scenes[inspect.stack()[0].function[5:]].objects
        self.assertLitLevel(objects["ATTR_light_level1prop"], "SpecialName_" + xp249c.HINT_PROP_LIT_LEVEL + "1", .25, .75, "sim/weapons/x[0]")
        self.assertLitLevel(objects["lit_level"],             "249_"         + xp249c.HINT_PROP_LIT_LEVEL + "2", .10, .90, "sim/weapons/y[0]")

    def test_Scene_lit_level_split(self)->None:
        bpy.ops.xplane.do_249_conversion(project_type=ProjectType.AIRCRAFT.name, workflow_type=WorkflowType.REGULAR.name)
        objects = bpy.data.scenes[inspect.stack()[0].function[5:]].objects
        self.assertEqual(objects["ATTR_light_level_v1"].material_slots[0].material.name, xp249c.DEFAULT_MATERIAL_NAME)
        self.assertEqual(objects["ATTR_light_level_v2"].material_slots[0].material.name, xp249c.DEFAULT_MATERIAL_NAME)

        self.assertLitLevel(objects["ATTR_light_level_v1"], xp249c.DEFAULT_MATERIAL_NAME, 0, 1, "", False)
        self.assertLitLevel(objects["ATTR_light_level_v2"], xp249c.DEFAULT_MATERIAL_NAME, 0, 1, "", False)
        # Yes, this is the only one that got the attribute. The rest get 249!
        def make_name(n)->str:
            return "{}_{}{}".format(xp249c.DEFAULT_MATERIAL_NAME, xp249c.HINT_PROP_LIT_LEVEL, n)
        self.assertLitLevel(objects["ATTR_light_level"],   make_name(3), 3, 6, "sim/weapons/z[0]")
        self.assertLitLevel(objects["ensures_v1_default"], make_name(4), 0.0, .6, "test/dref1")
        self.assertLitLevel(objects["ensures_v2_default"], make_name(5), .4, 1.0, "test/dref2")

    def test_Scene_many_lit_level(self)->None:
        bpy.ops.xplane.do_249_conversion(project_type=ProjectType.AIRCRAFT.name, workflow_type=WorkflowType.REGULAR.name)
        for i, obj in enumerate(
                filter(lambda o: o.type == "MESH" and "013" not in o.name,
                    bpy.data.scenes[inspect.stack()[0].function[5:]].objects),
                start=1):
            self.assertLitLevel(
                    obj,
                    "{}_{}_{}{}".format(
                        xp249c.DEFAULT_MATERIAL_NAME,
                        xp249c.HINT_PROP_SOLID_CAM,
                        xp249c.HINT_PROP_LIT_LEVEL,
                        i+5,
                    ),
                    0,
                    i,
                    "test/dref"
            )

        self.assertLitLevel(
                bpy.data.objects["Cube.013"],
                "{}_{}_{}{}".format(
                    xp249c.DEFAULT_MATERIAL_NAME,
                    xp249c.HINT_PROP_SOLID_CAM,
                    xp249c.HINT_PROP_LIT_LEVEL,
                    10,
                ),
                0,
                5,
                "test/dref"
        )

runTestCases([TestObjectAttributesApplied])
