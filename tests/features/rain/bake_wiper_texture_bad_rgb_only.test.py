from pathlib import Path
import inspect
import os
import sys
from typing import Tuple

import bpy

from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers
from io_xplane2blender.xplane_utils import xplane_wiper_gradient

__dirname__ = Path(__file__).parent


class TestBakeWiperTextureBadRGBOnly(XPlaneTestCase):
    def test_bad_wiper_image_rgb_only(self)->None:
        root = bpy.data.collections["bad_wiper_image_rgb_only"]
        any_object = bpy.data.objects["Armature.001"]
        any_object.select_set(True)
        bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[
            "bad_wiper_image_rgb_only"
        ]
        bpy.context.view_layer.objects.active = any_object
        self.assertEquals(bpy.ops.xplane.bake_wiper_gradient_texture(), {"CANCELLED"})

runTestCases([TestBakeWiperTextureBadRGBOnly])
