import inspect

from typing import Tuple
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *

__dirname__ = os.path.dirname(__file__)


class TestExportControlMethods(XPlaneTestCase):
    def test_ExpCollectionDisabledInViewport(self)->None:
        root = inspect.stack()[0].function[5:]
        self.assertRaises(ValueError, lambda: self.exportExportableRoot(root, dest=None, force_visible=False))

    def test_ExpCollectionHiddenInViewport(self)->None:
        root = inspect.stack()[0].function[5:]
        self.assertRaises(ValueError, lambda: self.exportExportableRoot(root, dest=None, force_visible=False))

    def test_ExpCollectionNotMarkedExportable(self)->None:
        root = inspect.stack()[0].function[5:]
        self.assertRaises(ValueError, lambda: self.exportExportableRoot(root, dest=None, force_visible=False))

    def test_ExpCollectionParentDisabledInViewport(self)->None:
        root = inspect.stack()[0].function[5:]
        self.assertRaises(ValueError, lambda: self.exportExportableRoot(root, dest=None, force_visible=False))

    def test_ExpCollectionParentHiddenInViewport(self)->None:
        root = inspect.stack()[0].function[5:]
        self.assertRaises(ValueError, lambda: self.exportExportableRoot(root, dest=None, force_visible=False))

    def test_CubeNotMarkedExportable(self)->None:
        root = inspect.stack()[0].function[5:]
        self.assertRaises(ValueError, lambda: self.exportExportableRoot(root, dest=None, force_visible=False))


runTestCases([TestExportControlMethods])
