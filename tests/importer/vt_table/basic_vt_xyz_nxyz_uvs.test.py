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
    def _assertVTTable(self, filename):
        bpy.ops.import_scene.xplane_obj(
            filepath=make_fixture_path(__dirname__, filename)
        )

        original_quad = bpy.data.collections[filename[5:]].objects[0]
        imported_quad = bpy.data.collections[filename].objects[0]

        o_vt_cos = sorted(
            set(
                tuple(original_quad.matrix_world @ v.co)
                for v in original_quad.data.vertices
            )
        )
        i_vt_cos = sorted(
            set(
                tuple(imported_quad.matrix_world @ v.co)
                for v in imported_quad.data.vertices
            )
        )
        o_vt_normals = sorted(set(tuple(v.normal) for v in original_quad.data.vertices))
        i_vt_normals = sorted(set(tuple(v.normal) for v in imported_quad.data.vertices))
        o_vt_uvs = sorted(
            set(tuple(v.uv) for v in original_quad.data.uv_layers[0].data)
        )
        i_vt_uvs = sorted(
            set(tuple(v.uv) for v in imported_quad.data.uv_layers[0].data)
        )
        for i, (o_vt_co, i_vt_co) in enumerate(zip(o_vt_cos, i_vt_cos)):
            self.assertVectorAlmostEqual(o_vt_co, i_vt_co, 1)
        for i, (o_vt_normal, i_vt_normal) in enumerate(zip(o_vt_normals, i_vt_normals)):
            self.assertVectorAlmostEqual(o_vt_normal, i_vt_normal, 1)
        for i, (o_vt_uv, i_vt_uv) in enumerate(zip(o_vt_uvs, i_vt_uvs)):
            self.assertVectorAlmostEqual(o_vt_uv, i_vt_uv, 1)

    def test_basic_vt_xyz_nxyz_uvs(self) -> None:
        filenames = [
            # "test_4_vts_normal_normals_no_uvs",
            "test_4_vts_normal_normals_no_uvs_rot_45",
            # "test_4_vts_normal_normals_uvs",
            # "test_4_vts_reversed_normals_no_uvs",
        ]
        for filename in filenames:
            with self.subTest(filename=filename):
                bpy.ops.wm.revert_mainfile()
                self._assertVTTable(filename)


runTestCases([BasicVTxyzNxyzUvs])
