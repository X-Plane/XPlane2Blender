import inspect
import os
import sys
from typing import Tuple

import bpy

from io_xplane2blender import xplane_config, xplane_constants
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers

__dirname__ = os.path.dirname(__file__)


class TestPartOfPanelToCockpitFeature(XPlaneTestCase):
    def test_post_update(self) -> None:

        self.assertEqual(
            bpy.data.materials["MaterialDefault"].xplane.cockpit_feature,
            xplane_constants.COCKPIT_FEATURE_NONE,
        )
        self.assertEqual(
            bpy.data.materials["MaterialFalse"].xplane.cockpit_feature,
            xplane_constants.COCKPIT_FEATURE_NONE,
        )
        self.assertEqual(
            bpy.data.materials["MaterialTrue"].xplane.cockpit_feature,
            xplane_constants.COCKPIT_FEATURE_PANEL,
        )

        self.assertIsNone(bpy.data.materials["MaterialDefault"]["xplane"].get("panel"))
        self.assertEqual(bpy.data.materials["MaterialFalse"]["xplane"]["panel"], 0)
        self.assertEqual(bpy.data.materials["MaterialTrue"]["xplane"]["panel"], 1)


runTestCases([TestPartOfPanelToCockpitFeature])
