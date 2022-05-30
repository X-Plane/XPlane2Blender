from pathlib import Path
import inspect
import os
import sys
from typing import Tuple

import bpy

from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers
from io_xplane2blender.xplane_utils import xplane_wiper_gradient

__dirname__ = Path(__file__).parent


class TestBakeWiperTexture(XPlaneTestCase):
    def setUp(self):
        super().setUp()
        # Just in case we forget to reset this in the .blend file
        bpy.data.collections[
            "four_slot_wiper_system"
        ].xplane.layer.rain.wiper_texture = ""
        bpy.data.objects["two_slot_wiper_system"].xplane.layer.rain.wiper_texture = ""

        # Just in case our test failed, we want to be neat for the developer's
        # folders
        shutil.rmtree(
            __dirname__ / Path("four_slot_textures", "_tmp_bake_images"),
            ignore_errors=True,
        )
        shutil.rmtree(
            __dirname__ / Path("two_slot_textures", "_tmp_bake_images"),
            ignore_errors=True,
        )

    def _test_bake_op(self, slot: str) -> None:
        """Runs and asserts the core of running the operator, slot must be 'four' or 'two'"""
        assert slot in {"four", "two"}
        textures_folder = __dirname__ / Path(f"{slot}_slot_textures")
        test_fixtures = __dirname__ / Path("fixtures", "bake_fixtures")
        fixture_wiper_gradient_path = test_fixtures / Path(
            f"test_{slot}_slot_system_wiper_gradient_texture.png"
        )
        output_wiper_gradient_path = get_tmp_folder() / Path(
            f"test_{slot}_slot_system_wiper_gradient_texture.png"
        )

        # --- Ensure initial conditions ---------------------------------------
        self.assertEqual(
            16,
            bpy.context.scene.render.bake.margin,
            f"Margin was {bpy.context.scene.render.bake.margin}, check you didn't change the .blend file accidentally",
        )

        def test_no_temp_data():
            self.assertEqual(
                {"Render Result", "wiper_four_slot_system", "wiper_two_slot_system"},
                {img.name for img in bpy.data.images},
            )
            self.assertFalse(
                (textures_folder / Path("_bake_temp_files")).exists(),
                "_bake_temp_files folder not cleaned up since last time. Check setUp and feature code",
            )

        test_no_temp_data()
        # ---------------------------------------------------------------------
        if slot == "four":
            root = bpy.data.collections["four_slot_wiper_system"]
            any_object = bpy.data.objects["Armature"]
            any_object.select_set(True)
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[
                "four_slot_wiper_system"
            ]
            bpy.context.view_layer.objects.active = any_object
            start = 1

        if slot == "two":
            root = bpy.data.objects["two_slot_wiper_system"]
            root.select_set(True)
            bpy.context.view_layer.objects.active = root
            start = 6

        bpy.ops.xplane.bake_wiper_gradient_texture(
            start=start, debug_master_filepath=str(output_wiper_gradient_path)
        )

        self.assertEqual(
            16,
            bpy.context.scene.render.bake.margin,
            f"Margin is {bpy.context.scene.render.bake.margin}, state was not reset after test",
        )
        test_no_temp_data()
        # --- Test bake output ------------------------------------------------
        self.assertImagesEqual(fixture_wiper_gradient_path, output_wiper_gradient_path)
        self.assertNotEqual(
            root.xplane.layer.rain.wiper_texture,
            "",
            msg="wiper_texture not set after bake",
        )

        self.assertEqual(
            root.xplane.layer.rain.wiper_texture.replace("\\", "/"),
            bpy.path.relpath(str(output_wiper_gradient_path)).replace("\\", "/"),
        )
        # ---------------------------------------------------------------------

    def test_bake_systems(self) -> None:
        for slot in ["two", "four"]:
            with self.subTest(slot=slot):
                self._test_bake_op(slot)


runTestCases([TestBakeWiperTexture])
