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


class ComplexVTCases(XPlaneTestCase):
    def test_complex_vt_cases(self) -> None:
        filenames = ["test_multi_tris", "test_many_faces"]
        for filename in filenames:
            with self.subTest(filename=filename):
                bpy.ops.wm.revert_mainfile()
                bpy.ops.import_scene.xplane_obj(
                    filepath=make_fixture_path(__dirname__, filename)
                )
                original_mesh = bpy.data.collections[filename[5:]].objects[0]
                imported_mesh = bpy.data.collections[filename].objects[0]
                self.assertVTTable(original_mesh, imported_mesh)


runTestCases([ComplexVTCases])
