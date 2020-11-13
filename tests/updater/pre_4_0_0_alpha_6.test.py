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
                assert False, f"{scene.name}'s XPlaneLayer should have no trace of 'exportMode', has {exportMode_val}"

    def test_index_deleted(self)->None:
        for has_layer in bpy.data.collections[:] + bpy.data.objects[:]:
            try:
                index_val = has_layer.xplane.layer["index"]
            except KeyError:
                pass
            else:
                assert False, f"{has_layer.name}'s XPlaneLayer should have no trace of 'index', has {index_val}"

    def test_export_mesh_deleted(self)->None:
        for obj in bpy.data.objects:
            try:
                export_mesh_val = obj.xplane["export_mesh"]
            except KeyError:
                pass
            else:
                assert False, f"{obj.name}'s XPlaneObjectSettings should have no trace of 'export_mesh_val', has {export_mesh_val}"

    def test_export_deleted(self)->None:
        for has_layer in bpy.data.collections[:] + bpy.data.objects[:]:
            try:
                export_val = has_layer.xplane.layer["export"]
            except KeyError:
                pass
            else:
                assert False, f"{has_layer.name}'s XPlaneLayer should have no trace of 'export', has {export_val}"

runTestCases([TestPre4_0_0_alpha_6PropsUpdated])
