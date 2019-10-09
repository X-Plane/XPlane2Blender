import inspect

from typing import Tuple
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_249_converter.xplane_249_constants import ProjectType, WorkflowType

__dirname__ = os.path.dirname(__file__)

class TestVnameConverted(XPlaneTestCase):
    def test_vname_converted(self)->None:
        bpy.ops.xplane.do_249_conversion(project_type=ProjectType.SCENERY.name, workflow_type=WorkflowType.BULK.name)

        self.assertEqual(len(bpy.data.objects["OBJ_vname2"].xplane.layer.export_path_directives), 3)
        self.assertEqual(bpy.data.objects["OBJ_vname2"].xplane.layer.export_path_directives[0].export_path, "special/path/vname")
        self.assertEqual(bpy.data.objects["OBJ_vname2"].xplane.layer.export_path_directives[1].export_path, "special/path/vname1")
        self.assertEqual(bpy.data.objects["OBJ_vname2"].xplane.layer.export_path_directives[2].export_path, "special/path/vname2")

        self.assertEqual(len(bpy.data.objects["OBJCase2"].xplane.layer.export_path_directives), 1)
        self.assertEqual(bpy.data.objects["OBJCase2"].xplane.layer.export_path_directives[0].export_path, "path_not_overridden")

        self.assertEqual(len(bpy.data.objects["AFakeOut"].xplane.layer.export_path_directives), 0)

runTestCases([TestVnameConverted])
