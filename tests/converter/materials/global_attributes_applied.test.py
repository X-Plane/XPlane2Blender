import inspect
from typing import Tuple
import os
import sys

import bpy
from io_xplane2blender import xplane_config, xplane_constants
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_249_converter.xplane_249_constants import WorkflowType

__dirname__ = os.path.dirname(__file__)

class TestGlobalAttributesApplied(XPlaneTestCase):
    def test_BlendGlass(self):
        """(both cubes get BLEND_GLASS)"""
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.REGULAR.name)
        self.assertTrue(bpy.data.scenes["BlendGlass"].objects["BlendGlass_1"].material_slots[0].material.xplane.blend_glass)
        self.assertTrue(bpy.data.scenes["BlendGlass"].objects["BlendGlass_2"].material_slots[0].material.xplane.blend_glass)

    def test_GlobalNoBlend(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.REGULAR.name)
        """(gets 1.0)"""
        self.assertEqual(bpy.data.scenes["GlobalNoBlend"].objects["GlobalNoBlend_1"].material_slots[0].material.xplane.blend_v1000, xplane_constants.BLEND_OFF)
        self.assertEqual(bpy.data.scenes["GlobalNoBlend"].objects["GlobalNoBlend_2"].material_slots[0].material.xplane.blend_v1000, xplane_constants.BLEND_OFF)
        self.assertAlmostEqual(bpy.data.scenes["GlobalNoBlend"].objects["GlobalNoBlend_1"].material_slots[0].material.xplane.blendRatio, 1.0)
        self.assertAlmostEqual(bpy.data.scenes["GlobalNoBlend"].objects["GlobalNoBlend_2"].material_slots[0].material.xplane.blendRatio, 1.0)

    def test_GlobalShadowBlend(self):
        """(gets .25)"""
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.REGULAR.name)
        self.assertEqual(bpy.data.scenes["GlobalShadowBlend"].objects["GlobalShadowBlend_1"].material_slots[0].material.xplane.blend_v1000, xplane_constants.BLEND_SHADOW)
        self.assertEqual(bpy.data.scenes["GlobalShadowBlend"].objects["GlobalShadowBlend_2"].material_slots[0].material.xplane.blend_v1000, xplane_constants.BLEND_SHADOW)
        self.assertAlmostEqual(bpy.data.scenes["GlobalShadowBlend"].objects["GlobalShadowBlend_1"].material_slots[0].material.xplane.blendRatio, 0.25)
        self.assertAlmostEqual(bpy.data.scenes["GlobalShadowBlend"].objects["GlobalShadowBlend_2"].material_slots[0].material.xplane.blendRatio, 0.25)

    def test_GlobalSpecular(self):
        """(unchanged specular intensity, default material gets prop value"""
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.REGULAR.name)
        self.assertTrue(bpy.data.scenes["GlobalSpecular"].objects["GlobalSpecular_1"].material_slots[0].material.specular_intensity, bpy.data.materials["Material"].specular_intensity)
        self.assertTrue(bpy.data.scenes["GlobalSpecular"].objects["GlobalSpecular_2"].material_slots[0].material.specular_intensity, .35)

    def test_GlobalTint(self):
        """(both cubes get Albedo .45, Emissive .55)"""
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.REGULAR.name)
        self.assertTrue(bpy.data.scenes["GlobalTint"].objects["GlobalTint_1"].material_slots[0].material.xplane.tint)
        self.assertTrue(bpy.data.scenes["GlobalTint"].objects["GlobalTint_2"].material_slots[0].material.xplane.tint)

        self.assertAlmostEqual(bpy.data.scenes["GlobalTint"].objects["GlobalTint_1"].material_slots[0].material.xplane.tint_albedo, 0.45)
        self.assertAlmostEqual(bpy.data.scenes["GlobalTint"].objects["GlobalTint_1"].material_slots[0].material.xplane.tint_emissive, 0.55)

        self.assertAlmostEqual(bpy.data.scenes["GlobalTint"].objects["GlobalTint_2"].material_slots[0].material.xplane.tint_albedo, 0.45)
        self.assertAlmostEqual(bpy.data.scenes["GlobalTint"].objects["GlobalTint_2"].material_slots[0].material.xplane.tint_emissive, 0.55)

    def test_NormalMetalness(self):
        """(both cubes get NORMAL_METALNESS)"""
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.REGULAR.name)
        self.assertTrue(bpy.data.scenes["NormalMetalness"].objects["NormalMetalness_1"].material_slots[0].material.xplane.normal_metalness)
        self.assertTrue(bpy.data.scenes["NormalMetalness"].objects["NormalMetalness_2"].material_slots[0].material.xplane.normal_metalness)

runTestCases([TestGlobalAttributesApplied])
