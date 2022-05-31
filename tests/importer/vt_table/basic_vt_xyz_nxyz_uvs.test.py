import inspect
import os
import pathlib
import sys
from typing import Tuple

import bpy

from io_xplane2blender import xplane_constants, xplane_import
from io_xplane2blender.importer import xplane_imp_parser
from io_xplane2blender.importer.xplane_imp_parser import import_obj
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers

__dirname__ = pathlib.Path(__file__).parent


class BasicVTxyzNxyzUvs(XPlaneTestCase):
    def test_basic_vt_xyz_nxyz_uvs(self) -> None:
        filenames = [
            "test_4_vts_normal_normals_no_uvs",
            "test_4_vts_normal_normals_no_uvs_rot_45",
            "test_4_vts_normal_normals_uvs",
            "test_4_vts_reversed_normals_no_uvs",
        ]
        for filename in filenames:
            with self.subTest(filename=filename):
                bpy.ops.wm.revert_mainfile()
                bpy.ops.import_scene.xplane_obj(
                    filepath=make_fixture_path(__dirname__, filename)
                )

                original_quad = bpy.data.collections[filename[5:]].objects[0]
                imported_quad = bpy.data.collections[filename].objects[0]
                self.assertVTTable(original_quad, imported_quad)


runTestCases([BasicVTxyzNxyzUvs])
