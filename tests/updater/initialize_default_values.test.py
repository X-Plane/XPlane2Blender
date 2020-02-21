import inspect

from typing import Tuple
import os
import sys

import bpy
from io_xplane2blender import xplane_config, xplane_constants
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers

__dirname__ = os.path.dirname(__file__)


class TestInitializeDefaultValues(XPlaneTestCase):
    """
    Instead of making a person manually run an operator
    to give each XPlaneLayer 4 lods/cockpit regions,
    we instead update each root object on load and
    set it when Root Object is applied
    """
    def test_update_none(self)->None:
        """
        To test this, you'll need to replace the start up file with
        1 collection and 1 root object, and delete their lod and cockpit region
        to make sure the user absolutely cannot start off without this.
        Sucks? Yes.
        """
        with test_creation_helpers.TemporaryStartFile(os.path.join(__dirname__, "custom_startup", "no_xp2b.blend")):
            for layer_props in [thing.xplane.layer for thing in bpy.data.objects[:] + bpy.data.collections[:]]:
                self.assertEqual(len(layer_props.lod), xplane_constants.MAX_LODS-1)
                self.assertEqual(len(layer_props.cockpit_region), xplane_constants.MAX_COCKPIT_REGIONS)

    def test_update_functions(self)->None:
        """
        The load_handle sets up new and past files, updater functions
        ensures users can somehow reset things in Blender without a restart
        """

        with test_creation_helpers.TemporaryStartFile(os.path.join(__dirname__, "custom_startup", "no_xp2b.blend")):
            layer_props = bpy.data.objects["Cube"].xplane.layer
            # Test that removing a couple from the collection
            # then changing lods or cockpit_regions causes update to run
            # again
            layer_props.lod.remove(0)
            layer_props.lod.remove(0)
            layer_props.cockpit_region.remove(0)
            layer_props.cockpit_region.remove(0)
            layer_props.lods = "0"
            layer_props.cockpit_regions = "2" # random choice
            self.assertEqual(len(layer_props.lod), xplane_constants.MAX_LODS-1)
            self.assertEqual(len(layer_props.cockpit_region), xplane_constants.MAX_COCKPIT_REGIONS)


runTestCases([TestInitializeDefaultValues])
