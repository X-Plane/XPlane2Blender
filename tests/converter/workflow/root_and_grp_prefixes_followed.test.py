import inspect

from typing import Tuple
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_249_converter.xplane_249_constants import ProjectType, WorkflowType

__dirname__ = os.path.dirname(__file__)

class TestRootAndGRPPrefixesFollowed(XPlaneTestCase):
    def test_root_object_prefixes(self)->None:
        bpy.ops.xplane.do_249_conversion(project_type=ProjectType.SCENERY.name, workflow_type=WorkflowType.BULK.name)
        for name in ["OBJ_OBJLevel1", "OBJ_OBJLevel2", "OBJ_OBJLevel3", "BGN_BGNLevel2", "VRT_VRTLevel2", "END_ENDLevel2"]:
            self.assertTrue(bpy.data.objects[name].xplane.isExportableRoot)

    def test_path_prop_spread(self)->None:
        bpy.ops.xplane.do_249_conversion(project_type=ProjectType.SCENERY.name, workflow_type=WorkflowType.BULK.name)
        names_to_path = {
            "OBJ_OBJLevel1": "GRP_Level1/_OBJLevel1",
            "OBJ_OBJLevel2": "GRP_Level2/_OBJLevel2",
            "OBJ_OBJLevel3": "GRP_Level3/_OBJLevel3",
            "BGN_BGNLevel2": "GRP_Level2/_BGNLevel2",
            "VRT_VRTLevel2": "GRP_Level2/_VRTLevel2",
            "END_ENDLevel2": "GRP_Level2/_ENDLevel2",
            }
        for name, path in names_to_path.items():
            self.assertEqual(bpy.data.objects[name].xplane.layer.name, path)

    def test_not_empty_is_not_root(self)->None:
        bpy.ops.xplane.do_249_conversion(project_type=ProjectType.SCENERY.name, workflow_type=WorkflowType.BULK.name)
        for obj in [bpy.data.objects[p+"NotEmpty"] for p in ("BGN", "VRT", "END", "OBJ")]:
            self.assertFalse(obj.xplane.isExportableRoot)

        self.assertFalse(bpy.data.objects["OBJRealRoot"].xplane.isExportableRoot)


runTestCases([TestRootAndGRPPrefixesFollowed])
