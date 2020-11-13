import inspect
import os
import sys

import bpy

from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_constants import *

__dirname__ = os.path.dirname(__file__)


class TestBlendModeBlendGlassUpdate(XPlaneTestCase):
    def test_blend_mode_blend_glass_update(self):
        self.assertIsNone(
            bpy.data.materials["Material_DEFAULT_ON"].xplane.get("blend_v1000")
        )
        self.assertIsNone(
            bpy.data.materials["Material_DEFAULT_ON"].xplane.get("blend_v1100")
        )

        self.assertEqual(
            bpy.data.materials["Material_ON_DEFAULT"].xplane.blend_v1000, BLEND_ON
        )
        self.assertIsNone(
            bpy.data.materials["Material_ON_DEFAULT"].xplane.get("blend_v1100")
        )

        self.assertEqual(
            bpy.data.materials["Material_OFF_SHADOW"].xplane.blend_v1000, BLEND_OFF
        )
        self.assertIsNone(
            bpy.data.materials["Material_OFF_SHADOW"].xplane.get("blend_v1100")
        )

        self.assertEqual(
            bpy.data.materials["Material_SHADOW_BLEND_GLASS"].xplane.blend_v1000,
            BLEND_SHADOW,
        )
        self.assertIsNone(
            bpy.data.materials["Material_SHADOW_BLEND_GLASS"].xplane.get("blend_v1100")
        )
        self.assertTrue(bpy.data.collections["Layer 1"].xplane.layer.blend_glass)


runTestCases([TestBlendModeBlendGlassUpdate])
