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
        self.assertTrue(bpy.scenes["BlendGlass"].objects[0].material_slots[0].xplane.blend_glass)
        self.assertTrue(bpy.scenes["BlendGlass"].objects[1].material_slots[0].xplane.blend_glass)

    def test_GlobalCockpitLit(self):
        """(everything gets Cockpit Lit, actually just sets panel_ok)"""
        self.assertTrue(bpy.scenes["GlobalCockpitLit"].objects[0].material_slots[0].xplane.cockpit_lit)
        self.assertTrue(bpy.scenes["GlobalCockpitLit"].objects[1].material_slots[0].xplane.cockpit_lit)

    def test_GlobalNoBlend(self):
        """(gets .15)"""
        self.assertEqual(bpy.scenes["GlobalNoBlend"].objects[0].material_slots[0].xplane.blend_v1000, xplane_constants.BLEND_OFF)
        self.assertEqual(bpy.scenes["GlobalNoBlend"].objects[1].material_slots[0].xplane.blend_v1000, xplane_constants.BLEND_OFF)
        self.assertEqual(bpy.scenes["GlobalNoBlend"].objects[0].material_slots[0].xplane.blendRatio, 0.15)
        self.assertEqual(bpy.scenes["GlobalNoBlend"].objects[1].material_slots[0].xplane.blendRatio, 0.15)

    def test_GlobalShadowBlend(self):
        """(gets .25)"""
        self.assertEqual(bpy.scenes["GlobalShadowBlend"].objects[0].material_slots[0].xplane.blend_v1000, xplane_constants.BLEND_SHADOW)
        self.assertEqual(bpy.scenes["GlobalShadowBlend"].objects[1].material_slots[0].xplane.blend_v1000, xplane_constants.BLEND_SHADOW)
        #TODO: Test specularity is normalized by having objects [0,1] have different materials
        pass

    def test_GlobalSpecular(self):
        """(gets .35)"""
        pass

    def test_GlobalTint(self):
        """(both cubes get Albedo .45, Emissive .55 whatever)"""
        self.assertTrue(bpy.scenes["GlobalTint"].objects[0].material_slots[0].xplane.tint)
        self.assertTrue(bpy.scenes["GlobalTint"].objects[1].material_slots[0].xplane.tint)

        self.assertEqual(bpy.scenes["GlobalTint"].objects[0].material_slots[0].xplane.tint_albedo, 0.45)
        self.assertEqual(bpy.scenes["GlobalTint"].objects[0].material_slots[0].xplane.tint_emissive, 0.55)

        self.assertEqual(bpy.scenes["GlobalTint"].objects[1].material_slots[0].xplane.tint_albedo, 0.45)
        self.assertEqual(bpy.scenes["GlobalTint"].objects[1].material_slots[0].xplane.tint_emissive, 0.55)

    def test_NormalMetalness(self):
        """(both cubes get NORMAL_METALNESS)"""
        self.assertTrue(bpy.scenes["NormalMetalness"].objects[0].material_slots[0].xplane.normal_metalness)
        self.assertTrue(bpy.scenes["NormalMetalness"].objects[1].material_slots[0].xplane.normal_metalness)

runTestCases([TestGlobalAttributesApplied])
