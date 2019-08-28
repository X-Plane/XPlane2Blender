import inspect

from typing import Tuple
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_249_converter.xplane_249_constants import WorkflowType

__dirname__ = os.path.dirname(__file__)

class TestTextureAutodetectApplied(XPlaneTestCase):
    #TODO Move case
    def test_OBJCustomLightTexSkip(self)->None:
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        root_object = bpy.data.objects[inspect.stack()[0].function[5:]]
        self.assertTrue(root_object.xplane.layer.autodetectTextures)
        self.assertEqual(root_object.xplane.layer.texture,"")
        self.assertEqual(root_object.xplane.layer.texture_lit,"")
        self.assertEqual(root_object.xplane.layer.texture_normal,"")
        self.assertEqual(root_object.xplane.layer.texture_draped,"")
        self.assertEqual(root_object.xplane.layer.texture_draped_normal,"")

    def test_OBJFakeTextureWritten(self)->None:
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        root_object = bpy.data.objects[inspect.stack()[0].function[5:]]
        tex_used = r"//tex\notreal"
        self.assertEqual(root_object.xplane.layer.texture, tex_used + ".png")
        self.assertEqual(root_object.xplane.layer.texture_lit, "")
        self.assertEqual(root_object.xplane.layer.texture_normal, "")
        self.assertEqual(root_object.xplane.layer.texture_draped, "")
        self.assertEqual(root_object.xplane.layer.texture_draped_normal, "")

    def test_OBJFindTextures(self)->None:
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        root_object = bpy.data.objects[inspect.stack()[0].function[5:]]
        tex_used = r"//tex\texture"
        self.assertFalse(root_object.xplane.layer.autodetectTextures)
        self.assertEqual(root_object.xplane.layer.texture,        tex_used + ".png")
        self.assertEqual(root_object.xplane.layer.texture_lit,    tex_used + "_LIT.png")
        self.assertEqual(root_object.xplane.layer.texture_normal, tex_used + "_NML.png")
        self.assertEqual(root_object.xplane.layer.texture_draped,"")
        self.assertEqual(root_object.xplane.layer.texture_draped_normal,"")

    def test_OBJFindTexturesDDS(self)->None:
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        root_object = bpy.data.objects[inspect.stack()[0].function[5:]]
        tex_used = r"//tex\textureB"
        self.assertFalse(root_object.xplane.layer.autodetectTextures)
        self.assertEqual(root_object.xplane.layer.texture,        tex_used + ".dds")
        self.assertEqual(root_object.xplane.layer.texture_normal, tex_used + "_NML.dds")
        self.assertEqual(root_object.xplane.layer.texture_draped,"")
        self.assertEqual(root_object.xplane.layer.texture_draped_normal,"")

    def test_OBJFindTexturesDraped(self)->None:
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        root_object = bpy.data.objects[inspect.stack()[0].function[5:]]
        self.assertFalse(root_object.xplane.layer.autodetectTextures)
        tex_used = r"//tex\texture"
        self.assertEqual(root_object.xplane.layer.texture,        tex_used + ".png")
        self.assertEqual(root_object.xplane.layer.texture_normal, tex_used + "_NML.png")
        self.assertEqual(root_object.xplane.layer.texture_lit,    tex_used + "_LIT.png")

        tex_used_draped = r"//tex\draped"
        self.assertEqual(root_object.xplane.layer.texture_draped,        tex_used_draped + ".png")
        self.assertEqual(root_object.xplane.layer.texture_draped_normal, tex_used_draped + "_NML.png")

    def test_OBJNoPanelTexture(self)->None:
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        root_object = bpy.data.objects[inspect.stack()[0].function[5:]]
        tex_used = r"//tex\texture"
        self.assertFalse(root_object.xplane.layer.autodetectTextures)
        self.assertEqual(root_object.xplane.layer.texture,        tex_used + ".png")
        self.assertEqual(root_object.xplane.layer.texture_lit,    tex_used + "_LIT.png")
        self.assertEqual(root_object.xplane.layer.texture_normal, tex_used + "_NML.png")
        self.assertEqual(root_object.xplane.layer.texture_draped,"")
        self.assertEqual(root_object.xplane.layer.texture_draped_normal,"")


runTestCases([TestTextureAutodetectApplied])
