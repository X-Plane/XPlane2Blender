import inspect
import os
import sys
from typing import Tuple

import bpy

from io_xplane2blender import xplane_config, xplane_constants, xplane_props
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers

__dirname__ = os.path.dirname(__file__)


class TestSynchronizeVersionNumbers(XPlaneTestCase):
    def assertVersionHistoryEqual(
        self, scene, correct_version_history: List[xplane_helpers.VerStruct]
    ) -> None:
        self.assertEqual(
            len(scene.xplane.xplane2blender_ver_history),
            len(correct_version_history),
        )
        for ver_entry, correct_ver in zip(
            scene.xplane.xplane2blender_ver_history, correct_version_history
        ):
            self.assertEqual(
                xplane_helpers.VerStruct.from_version_entry(ver_entry), correct_ver
            )

    def assertVersionsSynchronize(self) -> None:
        self.assertTrue(
            all(
                xplane_helpers.VerStruct.from_version_entry(
                    scene.xplane.xplane2blender_ver_history[-1]
                )
                == xplane_helpers.VerStruct.current()
                for scene in bpy.data.scenes
            ),
            msg=f"Not all histories end with the current version",
        )

    def assertIdPropIsDeprecated(self) -> None:
        self.assertTrue(
            all(
                scene["xplane2blender_version"] == xplane_constants.DEPRECATED_XP2B_VER
                for scene in bpy.data.scenes
            ),
            msg="Not all scene's 'xplane2blender_version' has 'DEPRECATED', check save handle",
        )

    def test_syncronize(self) -> None:
        V4_0_0 = xplane_helpers.VerStruct.parse_version("4.0.0-rc.1+89.20200910152046")
        VCURRENT = xplane_helpers.VerStruct.current()
        # My apologies to the distant future, I hope this doesn't cause too much trouble to hardcode this,
        # congratulations on so many releases however! /s
        VFUTURE = xplane_helpers.VerStruct.parse_version(
            "9999.0.0-rc.1+9999.99991231000000"
        )

        sceneA, sceneB, sceneC, sceneD = [None] * 4

        def before_1st_reload():
            nonlocal sceneA, sceneB, sceneC, sceneD
            """
            Creates the following test setup

            Scene Name | Version           | "xplane2blender_version" idprop?
            -----------|-------------------|-----------------------------
            SceneA     | [current_version] | "DEPRECATED"
            SceneB     | v4.0.0            | "DEPRECATED"
            SceneC     | None              | "DEPRECATED"

            *v4.0.0 is short for v4.0.0-rc.1+89_20200910152046
            """
            # --- Scene Creation ----------------------------------------------
            # bpy.ops.wm.read_factory_settings()
            # bpy.ops.preferences.addon_enable(module="io_xplane2blender")
            test_creation_helpers.delete_everything()
            sceneA = bpy.context.scene
            sceneB, sceneC = [
                test_creation_helpers.create_scene(name)
                for name in ["SceneB", "SceneC"]
            ]
            # -----------------------------------------------------------------

            # --- SceneA -----------------------------------------------------
            sceneA.name = "SceneA"
            sceneA.xplane.xplane2blender_ver_history.clear()
            xplane_helpers.VerStruct.add_to_version_history(
                sceneA, xplane_helpers.VerStruct.current()
            )
            sceneA["xplane2blender_version"] = xplane_constants.DEPRECATED_XP2B_VER
            # -----------------------------------------------------------------

            # --- SceneB ------------------------------------------------------
            bpy.context.window.scene = sceneB
            xplane_helpers.VerStruct.add_to_version_history(sceneB, V4_0_0)
            sceneB["xplane2blender_version"] = xplane_constants.DEPRECATED_XP2B_VER
            # -----------------------------------------------------------------

            # --- SceneC ------------------------------------------------------
            sceneC["xplane2blender_version"] = xplane_constants.DEPRECATED_XP2B_VER
            # -----------------------------------------------------------------
            for scene in bpy.data.scenes:
                scene.xplane.plugin_development = True

        def after_1st_reload():
            # --- On First Load ---------------------------------------------------
            # - SceneC's version history will be [current_version]
            # - SceneB will have [v4.0.0, current_version]
            # - SceneA will have [current_version]
            # All witll have "xplane2blender_version" = "DEPRECATED"
            # Thus we fulfill that all legacy cases are taken care of properly, "xplane2blender_version" is handled properly,
            # all scenes get the current version on top no matter what (and no duplicates as SceneA shows)

            # --- SceneC ----------------------------------------------------------
            self.assertVersionHistoryEqual(sceneC, [VCURRENT])
            # ---------------------------------------------------------------------
            # --- SceneB ----------------------------------------------------------
            self.assertVersionHistoryEqual(sceneB, [V4_0_0, VCURRENT])
            # ---------------------------------------------------------------------
            # --- SceneA ----------------------------------------------------------
            self.assertVersionHistoryEqual(sceneA, [VCURRENT])
            # ---------------------------------------------------------------------

            # Just to be double double sure, we double check
            # VCURRENT is the last in the list for all
            self.assertVersionsSynchronize()
            self.assertIdPropIsDeprecated()

        # ---------------------------------------------------------------------
        before_1st_reload()  # aka init file
        bpy.ops.wm.save_mainfile(
            filepath=os.path.join(
                get_tmp_folder(),
                "synchronize_version_numbers_before_1st_reload.test.blend",
            )
        )
        bpy.ops.wm.open_mainfile(
            filepath=os.path.join(
                get_tmp_folder(),
                "synchronize_version_numbers_before_1st_reload.test.blend",
            )
        )
        sceneA, sceneB, sceneC = sorted(
            [s for s in bpy.data.scenes], key=lambda s: s.name
        )
        after_1st_reload()
        # ---------------------------------------------------------------------
        # ---------------------------------------------------------------------

        def before_2nd_reload():
            xplane_helpers.VerStruct.add_to_version_history(sceneA, VFUTURE)

        before_2nd_reload()
        bpy.ops.wm.save_mainfile(
            filepath=os.path.join(
                get_tmp_folder(),
                "synchronize_version_numbers_before_2nd_reload.test.blend",
            )
        )
        bpy.ops.wm.open_mainfile(
            filepath=os.path.join(
                get_tmp_folder(),
                "synchronize_version_numbers_before_2nd_reload.test.blend",
            )
        )
        sceneA, sceneB, sceneC = sorted(
            [s for s in bpy.data.scenes], key=lambda s: s.name
        )
        # ---------------------------------------------------------------------

        # ---------------------------------------------------------------------
        def after_2nd_reload():
            """
            On second reload we test that the current version
            will always be applied, even if the current version is later.
            (And that we always end with the current version as latest)
            """

            # --- SceneC ----------------------------------------------------------
            self.assertVersionHistoryEqual(sceneC, [VCURRENT])
            # ---------------------------------------------------------------------
            # --- SceneB ----------------------------------------------------------
            self.assertVersionHistoryEqual(sceneB, [V4_0_0, VCURRENT])
            # ---------------------------------------------------------------------
            # --- SceneA ----------------------------------------------------------
            # *** Here is what has changed between reloads ***
            self.assertVersionHistoryEqual(sceneA, [VCURRENT, VFUTURE, VCURRENT])
            # ---------------------------------------------------------------------

            # Just to be double double sure, we double check
            # VCURRENT is the last in the list for all
            self.assertVersionsSynchronize()
            self.assertIdPropIsDeprecated()

        after_2nd_reload()
        # ---------------------------------------------------------------------

        def before_3rd_save():
            sceneD = test_creation_helpers.create_scene("SceneD")

        before_3rd_save()
        bpy.ops.wm.save_mainfile(
            filepath=os.path.join(
                get_tmp_folder(),
                "synchronize_version_numbers_after_3rd_save.test.blend",
            )
        )
        sceneD = bpy.data.scenes["SceneD"]

        def after_3rd_save():
            # We check that nothing changed since 2nd reload
            after_2nd_reload()
            # Then check we're synced up
            self.assertVersionHistoryEqual(sceneD, [VCURRENT])
            self.assertEqual(
                bpy.data.scenes["SceneD"]["xplane2blender_version"],
                xplane_constants.DEPRECATED_XP2B_VER,
            )

        after_3rd_save()


runTestCases([TestSynchronizeVersionNumbers])
