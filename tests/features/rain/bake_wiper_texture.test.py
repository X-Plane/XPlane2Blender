from pathlib import Path
import inspect
import os
import sys
from typing import Tuple

import bpy

from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers

__dirname__ = Path(__file__).parent


class TestBakeWiperTexture(XPlaneTestCase):
    def setUp(self):
        super().setUp()
        # Just in case we forget to reset this in the .blend file
        bpy.context.scene.xplane.wiper_bake_start = 1
        bpy.context.scene.xplane.wiper_bake_end = 256
        bpy.data.collections[
            "four_slot_wiper_system"
        ].xplane.layer.rain.wiper_texture = ""
        bpy.data.objects["two_slot_wiper_system"].xplane.layer.rain.wiper_texture = ""

        shutil.rmtree(
            __dirname__ / Path("four_slot_textures", "_tmp_bake_images"),
            ignore_errors=True,
        )
        shutil.rmtree(
            __dirname__ / Path("two_slot_textures", "_tmp_bake_images"),
            ignore_errors=True,
        )

        try:
            (
                __dirname__ / Path("four_slot_textures", "wiper_gradient_texture.png")
            ).unlink()
        except FileNotFoundError:
            pass

        try:
            (
                __dirname__ / Path("two_slot_textures", "wiper_gradient_texture.png")
            ).unlink()
        except FileNotFoundError:
            pass

        bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[
            "fake_collection"
        ]

    @unittest.skip
    def test_bake_four_slot_system(self) -> None:
        test_fixtures = __dirname__ / Path("fixtures", "bake_fixtures")
        fixture_wiper_gradient_path = test_fixtures / Path(
            "test_four_slot_system_wiper_gradient_texture.png"
        )
        textures_folder = __dirname__ / Path("four_slot_textures")
        output_wiper_gradient_path = textures_folder / Path(
            "wiper_gradient_texture.png"
        )

        # --- Ensure initial conditions ---------------------------------------
        def test_no_temp_materials():
            self.assertEqual(
                {"wiper_four_slot_system", "Render Result", "wiper_four_slot_system"},
                {img.name for img in bpy.data.images},
            )
            self.assertFalse(
                (textures_folder / Path("wiper_gradient_texture.png")).exists()
            )
            self.assertFalse((textures_folder / Path("_bake_temp_files")).exists())

        test_no_temp_materials()
        # ---------------------------------------------------------------------

        root = bpy.data.collections["four_slot_wiper_system"]
        bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[
            "four_slot_wiper_system"
        ]

        start, end = 230, 233
        bpy.ops.xplane.bake_wiper_gradient_texture(
            debug_reuse_temps=True, debug_start=start, debug_end=end
        )

        # Assert the master images produced are the same
        # --- Test bake output ------------------------------------------------
        self.assertImagesEqual(fixture_wiper_gradient_path, output_wiper_gradient_path)
        self.assertEqual(
            root.xplane.layer.rain.wiper_texture,
            "//four_slot_textures/wiper_gradient_texture.png",
        )
        # ---------------------------------------------------------------------

    def test_bake_two_slot_system(self) -> None:
        test_fixtures = __dirname__ / Path("fixtures", "bake_fixtures")
        fixture_wiper_gradient_path = test_fixtures / Path(
            "test_two_slot_system_wiper_gradient_texture.png"
        )
        textures_folder = __dirname__ / Path("two_slot_textures")
        output_wiper_gradient_path = textures_folder / Path(
            "wiper_gradient_texture.png"
        )

        # --- Ensure initial conditions ---------------------------------------
        def test_no_temp_materials():
            self.assertEqual(
                {"wiper_four_slot_system", "Render Result", "wiper_two_slot_system"},
                {img.name for img in bpy.data.images},
            )
            self.assertFalse(
                (textures_folder / Path("wiper_gradient_texture.png")).exists()
            )
            self.assertFalse((textures_folder / Path("_bake_temp_files")).exists())

        test_no_temp_materials()
        # ---------------------------------------------------------------------

        root = bpy.data.objects["two_slot_wiper_system"]
        root.select_set(True)
        bpy.context.view_layer.objects.active = root

        start, end = 230, 233
        bpy.ops.xplane.bake_wiper_gradient_texture(debug_start=start, debug_end=end)

        # Assert the master images produced are the same
        # --- Test bake output ------------------------------------------------
        self.assertImagesEqual(fixture_wiper_gradient_path, output_wiper_gradient_path)
        self.assertEqual(
            root.xplane.layer.rain.wiper_texture,
            "//two_slot_textures/wiper_gradient_texture.png",
        )
        # ---------------------------------------------------------------------


runTestCases([TestBakeWiperTexture])
