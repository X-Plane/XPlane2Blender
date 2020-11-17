import inspect
import os
import sys
from typing import Tuple

import bpy

from io_xplane2blender import xplane_config, xplane_constants
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers

__dirname__ = os.path.dirname(__file__)


class TestPre_4_1_0_Beta_1_RegionsChangesPanelMode(XPlaneTestCase):
    def test_cockpit_regions_changes_panel_mode(self) -> None:
        self.assertEqual(
            bpy.data.collections[
                "Collection_regions_none"
            ].xplane.layer.cockpit_regions,
            "0",
        )
        self.assertEqual(
            bpy.data.collections[
                "Collection_regions_none"
            ].xplane.layer.cockpit_panel_mode,
            xplane_constants.PANEL_COCKPIT,
        )
        for i in range(1, 5):
            self.assertEqual(
                bpy.data.collections[
                    f"Collection_regions_{i}"
                ].xplane.layer.cockpit_regions,
                f"{i}",
            )
            self.assertEqual(
                bpy.data.collections[
                    f"Collection_regions_{i}"
                ].xplane.layer.cockpit_panel_mode,
                xplane_constants.PANEL_COCKPIT_REGION,
            )
        for col in [
            "Collection_default",
            "Collection_default_hand_set",
            "Collection_emissive",
        ]:
            self.assertEqual(
                bpy.data.collections[col].xplane.layer.cockpit_regions, "0"
            )
        self.assertEqual(
            bpy.data.collections["Collection_default"].xplane.layer.cockpit_panel_mode,
            xplane_constants.PANEL_COCKPIT,
        )
        self.assertEqual(
            bpy.data.collections[
                "Collection_default_hand_set"
            ].xplane.layer.cockpit_panel_mode,
            xplane_constants.PANEL_COCKPIT,
        )
        self.assertEqual(
            bpy.data.collections["Collection_emissive"].xplane.layer.cockpit_panel_mode,
            xplane_constants.PANEL_COCKPIT_LIT_ONLY,
        )


runTestCases([TestPre_4_1_0_Beta_1_RegionsChangesPanelMode])
