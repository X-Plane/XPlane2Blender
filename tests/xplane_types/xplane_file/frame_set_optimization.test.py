import inspect
import os
import sys
import time
from typing import Tuple

import bpy

from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers
from io_xplane2blender.xplane_types import xplane_file

__dirname__ = os.path.dirname(__file__)


class TestFrameSetOptimization(XPlaneTestCase):
    def test_time_test(self) -> None:
        # print(*(s.name for s in bpy.data.scenes))
        bpy.context.window.scene = bpy.data.scenes["Scene_time_test"]
        bpy.context.window.scene.xplane.plugin_development = True
        bpy.context.window.scene.xplane.dev_export_as_dry_run = True

        start = time.perf_counter()
        bpy.ops.scene.export_to_relative_dir()
        total = time.perf_counter() - start
        self.assertLess(
            total,
            3,
            "frame_set animation should never take more than 3 seconds long, took {total} seconds",
        )
        # print("TIME", start, total)

    def test_cache_results(self) -> None:
        from io_xplane2blender.xplane_types.xplane_file import XPlaneFile

        # This implementation detail is important enough to check,
        # without it
        bpy.context.window.scene = bpy.data.scenes["Scene_time_test"]

        # Slight hack - I could have messed with the file names or simply stopped
        # files from being written
        bpy.context.window.scene.xplane.plugin_development = True
        bpy.context.window.scene.xplane.dev_export_as_dry_run = True

        exportable_root = bpy.data.collections["time_test_1"]
        start = time.perf_counter()
        layer_props = bpy.data.collections["time_test_1"].xplane.layer
        filename = layer_props.name if layer_props.name else exportable_root.name

        xp_file = XPlaneFile(filename, layer_props)
        xp_file.create_xplane_bone_hiearchy(exportable_root)
        xp_file.write()
        time_test_1_total = time.perf_counter() - start

        exportable_root = bpy.data.collections["time_test_1"]
        start = time.perf_counter()
        layer_props = bpy.data.collections["time_test_2"].xplane.layer
        filename = layer_props.name if layer_props.name else exportable_root.name

        xp_file = XPlaneFile(filename, layer_props)
        xp_file.create_xplane_bone_hiearchy(exportable_root)
        xp_file.write()
        time_test_2_total = time.perf_counter() - start

        # print("t1", time_test_1_total, "t2", time_test_2_total)
        self.assertLess(
            time_test_2_total,
            time_test_1_total,
            msg=f"Time 1 '{time_test_1_total}s' > Time 2 '{time_test_2_total}s', is cache between OBJs working?",
        )
        self.assertLess(
            time_test_1_total,
            3,
            f"frame_set prescanning should never take more than 3 seconds long, tool {time_test_1_total} seconds",
        )

    def _edit_export_edit_export(self, suffix: str):
        bpy.context.window.scene = test_creation_helpers.create_scene(
            "edit_export_edit_export"
        )

        col = test_creation_helpers.create_datablock_collection(
            f"edit_export_edit_export_{suffix}"
        )
        col.xplane.is_exportable_collection = True
        col.xplane.layer.name = f"../../tmp/edit_export_edit_export_{suffix}.obj"

        ob = test_creation_helpers.create_datablock_empty(
            info=test_creation_helpers.DatablockInfo(
                "EMPTY", f"anim_empty_{suffix}", collection=col
            )
        )
        test_creation_helpers.set_collection(ob, col)
        test_creation_helpers.set_animation_data(
            ob,
            [
                test_creation_helpers.KeyframeInfo(0, "test", -1, location=(0, 0, 0)),
                test_creation_helpers.KeyframeInfo(1, "test", 0, location=(1, 0, 0)),
            ],
        )

    def test_edit_export_animate_export_unittest(self):
        """Tests the edit-export-animate-export cycle works when using unit testing methods"""
        suffix = "test"
        self._edit_export_edit_export(suffix)
        col = bpy.data.collections[f"edit_export_edit_export_{suffix}"]
        ob = bpy.data.objects[f"anim_empty_{suffix}"]
        two_kfs = self.exportExportableRoot(col)
        test_creation_helpers.set_animation_data(
            ob, [test_creation_helpers.KeyframeInfo(2, "test", 1, location=(2, 0, 0))]
        )
        three_kfs = self.exportExportableRoot(col)

        # print('-----------------')
        # print(two_kfs)
        # print(three_kfs)
        self.assertEqual(len(three_kfs.splitlines()) - len(two_kfs.splitlines()), 1)

    def test_edit_export_animate_export_operators(self):
        """Tests the edit-export-animate-export cycle works when using operators"""
        suffix = "operator"
        self._edit_export_edit_export(suffix)
        col = bpy.data.collections[f"edit_export_edit_export_{suffix}"]
        ob = bpy.data.objects[f"anim_empty_{suffix}"]
        bpy.ops.scene.export_to_relative_dir()
        filepath = os.path.join(get_tmp_folder(), f"{col.name}.obj")
        with open(filepath, "r") as f:
            two_kfs = f.readlines()
        test_creation_helpers.set_animation_data(
            ob, [test_creation_helpers.KeyframeInfo(2, "test", 1, location=(2, 0, 0))]
        )
        bpy.ops.scene.export_to_relative_dir()
        with open(filepath, "r") as f:
            three_kfs = f.readlines()

        # print('-----------------')
        # print('\n'.join(two_kfs))
        # print('\n'.join(three_kfs))
        self.assertEqual(len(three_kfs) - len(two_kfs), 1)

    def test_one_of_each_animation_type(self):
        bpy.context.window.scene = bpy.data.scenes["Scene_datablocks"]
        filename = inspect.stack()[0].function
        self.assertExportableRootExportEqualsFixture(
            filename[5:],
            os.path.join(__dirname__, "fixtures", f"{filename}.obj"),
            {"ANIM", "TRIS"},
            filename,
        )


runTestCases([TestFrameSetOptimization])
