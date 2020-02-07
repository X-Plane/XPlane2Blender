import inspect

from typing import Tuple
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *

__dirname__ = os.path.dirname(__file__)

class TestPre4_0_0_alpha_6PropsUpdated(XPlaneTestCase):
    def test_autodetectTexturesFalse(self)->None:
        for has_layer in bpy.data.collections[:] + bpy.data.objects[:]:
            self.assertFalse(has_layer.xplane.layer.autodetectTextures, f"{has_layer.name}'s autodetectTextures value isn't False")

    def test_exportMode_deleted(self)->None:
        for scene in bpy.data.scenes:
            try:
                exportMode_val = scene.xplane["exportMode"]
            except KeyError:
                pass
            else:
                assert False, f"{scene.name}'s should have no trace 'exportMode', has {exportMode_val}"

    def test_index_deleted(self)->None:
        for has_layer in bpy.data.collections[:] + bpy.data.objects[:]:
            try:
                index_val = has_layer.xplane.layer["index"]
            except KeyError:
                pass
            else:
                assert False, f"{has_layer.name}'s XPlaneLayer should have no trace 'index', has {index_val}"


runTestCases([TestPre4_0_0_alpha_6PropsUpdated])
