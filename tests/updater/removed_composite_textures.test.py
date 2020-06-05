import inspect

from typing import Tuple
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers

__dirname__ = os.path.dirname(__file__)

class TestRemovedCompositeTextures(XPlaneTestCase):
    def test_remove_composite_textures(self)->None:
        self.assertRaises(AttributeError, lambda: bpy.context.scene.xplane.compositeTextures)
        self.assertFalse("compositeTextures" in bpy.context.scene.xplane)

runTestCases([TestRemovedCompositeTextures])
