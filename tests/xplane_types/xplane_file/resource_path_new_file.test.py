import inspect
import os
import sys
from pathlib import Path
from typing import Tuple

import bpy

from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers

__dirname__ = os.path.dirname(__file__)


class TestResourcePathNewFile(XPlaneTestCase):
    def test_new_file_cwd_1_and_2(self) -> None:
        filename = inspect.stack()[0].function
        os.chdir(__dirname__)
        bpy.ops.wm.read_homefile()

        col = test_creation_helpers.create_datablock_collection("cwd_1_and_2")
        col.xplane.is_exportable_collection = True
        col.xplane.layer.name = filename + ".obj"
        col.xplane.layer.texture = "C:/tex.png"

        cube = test_creation_helpers.create_datablock_mesh(
            test_creation_helpers.DatablockInfo(
                "MESH", "Cube", collection="cwd_1_and_2"
            )
        )

        bpy.ops.export.xplane_obj(filepath=get_tmp_folder() + f"/{filename}")
        lines = (
            (Path(get_tmp_folder()) / Path(filename).with_suffix(".obj"))
            .read_text()
            .splitlines()
        )

        self.assertTrue(lines[5].split()[1], "../../../../../../tex.png")


runTestCases([TestResourcePathNewFile])
