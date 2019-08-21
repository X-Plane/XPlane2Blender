import inspect

from typing import Tuple
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_249_converter import xplane_249_constants
from io_xplane2blender.xplane_249_converter.xplane_249_constants import WorkflowType

__dirname__ = os.path.dirname(__file__)

class TestGlobalAttributesNotApplied(XPlaneTestCase):
    def _compare_objects_to_material(self, scene_name:str, material_1:str = None, material_2:str = None)->None:
        """
        Since we've been super careful to keep all the names aligned, we can make some boilerplate
        assumptions!
        """
        if not material_1:
            material_1 = xplane_249_constants.DEFAULT_MATERIAL_NAME
        if not material_2:
            material_2 = xplane_249_constants.DEFAULT_MATERIAL_NAME
        scene = bpy.data.scenes[scene_name]

        if scene_name.endswith("_not"):
            obj_base_name = scene.name[:-4]
        elif scene_name.endswith("_arg"):
            obj_base_name = scene.name
        elif scene_name.endswith("_not_STRING"):
            obj_base_name = scene.name[:-11]
        self.assertEqual(scene.objects[obj_base_name + "_1"].material_slots[0].name, material_1)
        self.assertEqual(scene.objects[obj_base_name + "_2"].material_slots[0].name, material_2)

    def test_GlobalNoBlend_not(self)->None:
        """(1.2notafloatafterall)"""
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.REGULAR.name)
        scene_name = inspect.stack()[0].function[5:]
        self._compare_objects_to_material(scene_name)

    def test_GlobalShadowBlend_not(self)->None:
        """(notafloat)"""
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.REGULAR.name)
        scene_name = inspect.stack()[0].function[5:]
        self._compare_objects_to_material(scene_name)

    def test_GlobalSpecular1_not(self)->None:
        """(notafloat2)"""
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.REGULAR.name)
        scene_name = inspect.stack()[0].function[5:]
        self._compare_objects_to_material(scene_name)

    def test_GlobalSpecular2_not(self)->None:
        """(Global Specular value (".6") not used, cubes have Materials instead)"""
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.REGULAR.name)
        scene_name = inspect.stack()[0].function[5:]
        self._compare_objects_to_material(scene_name, "Material_.10", "Material_.80")

    def test_GlobalSpecular3_not(self)->None:
        """(notafloat2)"""
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.REGULAR.name)
        scene_name = inspect.stack()[0].function[5:]
        self._compare_objects_to_material(scene_name)

    def test_GlobalTint_few_arg(self)->None:
        """(string value cannot be unpacked)"""
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.REGULAR.name)
        scene_name = inspect.stack()[0].function[5:]
        self._compare_objects_to_material(scene_name)

    def test_GlobalTint_many_arg(self)->None:
        """(string value cannot be unpacked)"""
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.REGULAR.name)
        scene_name = inspect.stack()[0].function[5:]
        self._compare_objects_to_material(scene_name)

    def test_GlobalTint_not_STRING(self)->None:
        """(Cubes get nothing, Global Tint wasn't a string)"""
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.REGULAR.name)
        scene_name = inspect.stack()[0].function[5:]
        self._compare_objects_to_material(scene_name)

runTestCases([TestGlobalAttributesNotApplied])
