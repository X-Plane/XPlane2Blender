import inspect
import os
import sys

import bpy
from io_xplane2blender import xplane_config, xplane_constants
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_249_converter.xplane_249_constants import WorkflowType

__dirname__ = os.path.dirname(__file__)


class TestLODConversion(XPlaneTestCase):
    def test_selective_lods(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        scene = bpy.context.scene
        self.assertTrue([(l.near, l.far) for l in scene.objects["OBJSelLODs_1_none"].xplane.layer.lod]  == [(0, 1000), (1000, 4000), (4000, 10000), (0, 0), (0, 0)])
        self.assertTrue([(l.near, l.far) for l in scene.objects["OBJSelLODs_2_13"].xplane.layer.lod]    == [(0, 300),  (300, 4000),  (4000, 6000),  (0, 0), (0, 0)])
        self.assertTrue([(l.near, l.far) for l in scene.objects["OBJSelLODs_3_0123"].xplane.layer.lod]  == [(10, 250), (250, 4000),  (4000, 5000),  (0, 0), (0, 0)])

    def test_odd_lods(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        scene = bpy.context.scene
        self.assertTrue([(l.near, l.far) for l in scene.objects["OBJodd_using_defs"].xplane.layer.lod]  == [(0, 1000), (1000, 4000), (4000, 10000), (0, 0), (0, 0)])
        self.assertTrue([(l.near, l.far) for l in scene.objects["OBJodd_prop_values"].xplane.layer.lod] == [(1, 100),  (100, 3500),  (3500, 0),     (0, 0), (0, 0)])

    def test_additive_lods(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        scene = bpy.context.scene
        self.assertTrue([(l.near, l.far) for l in scene.objects["OBJAddLODs_1_none"].xplane.layer.lod]  == [(0, 1000), (0, 4000), (0, 10000), (0, 0), (0, 0)])
        self.assertTrue([(l.near, l.far) for l in scene.objects["OBJAddLODs_2_12"].xplane.layer.lod]    == [(0, 1700), (0, 3500), (0, 10000), (0, 0), (0, 0)])
        self.assertTrue([(l.near, l.far) for l in scene.objects["OBJAddLODs_3_0123"].xplane.layer.lod]  == [(0, 250),  (0, 500),  (0, 9000),  (0, 0), (0, 0)])
        self.assertTrue([(l.near, l.far) for l in scene.objects["OBJAddLODs_4_03"].xplane.layer.lod]    == [(0, 1000), (0, 4000), (0, 2000),  (0, 0), (0, 0)])
        self.assertTrue(scene.objects["OBJAddLODs_1_none"].xplane.layer.export_type == xplane_constants.EXPORT_TYPE_INSTANCED_SCENERY)
        self.assertTrue(scene.objects["OBJAddLODs_2_12"].xplane.layer.export_type   == xplane_constants.EXPORT_TYPE_INSTANCED_SCENERY)
        self.assertTrue(scene.objects["OBJAddLODs_3_0123"].xplane.layer.export_type == xplane_constants.EXPORT_TYPE_INSTANCED_SCENERY)
        self.assertTrue(scene.objects["OBJAddLODs_4_03"].xplane.layer.export_type   == xplane_constants.EXPORT_TYPE_INSTANCED_SCENERY)


runTestCases([TestLODConversion])
